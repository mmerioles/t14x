import argparse
import queue
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from .model import Session, Guide, EXPECTED, WIRING, WIRING_ID, BUTTONS, parse_pairs
from .keyboard import Keyboard
from .mouse import MousePanel, LightsPanel
from .transport import Connection

TEENSY_VID=0x16c0  # PJRC


class App:
    """Finds the Teensy, starts testing on its own, and shows only what to press next."""
    def __init__(self,root,port=None,autoconnect=True):
        self.root,self.port,self.autoconnect=root,port,autoconnect
        self.session=Session(); self.guide=Guide(self.session)
        self.events=queue.Queue(); self.connection=None
        self.identified=self.scanning=False
        self.last_state=self.started_at=self.retry_at=0
        self.metadata={'mode':'hardware'}
        self.report_dir=Path('diagnostic-results')/datetime.now().strftime('%Y%m%d-%H%M%S')
        root.title('T14 diagnostics')
        root.geometry('1120x640'); root.minsize(820,520)
        root.configure(bg='#17191c')
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',background='#17191c',foreground='#e9eaec',font=('Arial',11))
        style.configure('TButton',background='#30343b',padding=(12,7),borderwidth=0)
        style.map('TButton',background=[('active','#424852')],foreground=[('disabled','#777c85')])
        style.configure('TNotebook',borderwidth=0)
        style.configure('TNotebook.Tab',background='#25282e',padding=(16,5))
        style.map('TNotebook.Tab',background=[('selected','#424852')])
        style.configure('Title.TLabel',font=('Arial',18,'bold'))
        style.configure('Dim.TLabel',foreground='#9aa0a8')
        # Dark tick boxes and radio dots; the theme's default white boxes stand out.
        for widget in ('TCheckbutton','TRadiobutton'):
            style.configure(widget,indicatorbackground='#30343b',indicatorforeground='#e9eaec',
                            upperbordercolor='#30343b',lowerbordercolor='#30343b',focuscolor='#17191c')
            style.map(widget,background=[('active','#17191c')],foreground=[('disabled','#777c85')],
                      indicatorbackground=[('disabled','#25282e'),('pressed','#424852'),('selected','#4cc277')])
        shell=ttk.Frame(root,padding=(10,8,10,10)); shell.pack(fill='both',expand=True)
        bar=ttk.Frame(shell); bar.pack(fill='x',pady=(0,6))
        # Connection light: gray until the diagnostics firmware answers, then green.
        self.light=tk.Canvas(bar,width=12,height=12,bg='#17191c',highlightthickness=0)
        self.light.pack(side='left',padx=(2,6))
        self.dot=self.light.create_oval(1,1,11,11,fill='#6b7078',outline='')
        self.connection_text=tk.StringVar(value='Not connected')
        ttk.Label(bar,textvariable=self.connection_text).pack(side='left')
        self.count=tk.StringVar()
        ttk.Label(bar,textvariable=self.count,style='Dim.TLabel').pack(side='right')
        self.tabs=ttk.Notebook(shell); self.tabs.pack(fill='both',expand=True)
        self.keys_tab=ttk.Frame(self.tabs,padding=(8,6,8,4))
        self.tabs.add(self.keys_tab,text='Keyboard')
        line=ttk.Frame(self.keys_tab); line.pack(fill='x')
        self.prompt=tk.StringVar()
        ttk.Label(line,textvariable=self.prompt,style='Title.TLabel').pack(side='left')
        self.status=tk.StringVar()
        ttk.Label(line,textvariable=self.status,style='Dim.TLabel').pack(side='left',padx=12)
        # The drawing scales to whatever space is left, so nothing is ever cut off.
        self.keyboard=Keyboard(self.keys_tab,self.select,self.show_mouse)
        self.keyboard.pack(fill='both',expand=True,pady=(4,0))
        self.mouse=MousePanel(self.tabs,self.start_trackpoint,self.mouse_changed)
        self.metadata['mouse']=self.mouse.state.report()
        self.tabs.add(self.mouse,text='TrackPoint')
        self.lights=LightsPanel(self.tabs,lambda command:self.send(command))
        self.tabs.add(self.lights,text='Lights')
        self.waiting(); self.paint()
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.poll_id=root.after(30,self.poll)

    def show_mouse(self): self.tabs.select(self.mouse)

    def set_connected(self,on):
        self.light.itemconfig(self.dot,fill='#4cc277' if on else '#6b7078')
        self.connection_text.set('Connected' if on else 'Not connected')

    def waiting(self,problem=None):
        self.set_connected(False)
        self.prompt.set('Plug in the Teensy' if not problem else 'Can’t talk to the Teensy')
        self.status.set(problem or '')

    def send(self,command):
        if self.connection: self.connection.send(command)

    def start_trackpoint(self):
        self.mouse.set_status('starting'); self.send('TRACKPOINT')

    def stop_extras(self):
        # The firmware switches the TrackPoint and lights off whenever it stops.
        self.mouse.pause(); self.lights.reset()

    def reset_scan(self):
        self.scanning=False; self.guide.cancel(); self.session.cancel(); self.stop_extras(); self.paint()

    def save_session(self):
        try: self.session.export(self.report_dir,self.metadata)
        except OSError as exc: self.status.set('Could not save results: '+str(exc))

    def mouse_changed(self,report):
        if self.metadata.get('mouse')!=report:
            self.metadata['mouse']=report
            self.save_session()

    def find_port(self):
        if self.port: return self.port
        from serial.tools import list_ports
        return next((p.device for p in list_ports.comports() if p.vid==TEENSY_VID),None)

    def connect(self):
        port=self.find_port()
        if not port: return
        self.metadata['port']=port
        self.events=queue.Queue()
        self.connection=Connection(port,self.events)
        self.connection.start()
        self.prompt.set('Connecting…')

    def start(self):
        self.started_at=time.monotonic()
        self.send('START '+WIRING_ID)
        if not self.mouse.state.live: self.start_trackpoint()

    def selected_prompt(self,key):
        self.prompt.set('Press '+key)
        self.status.set('')

    def select(self,key):
        if not self.scanning: return
        try: self.session.arm(key)
        except ValueError:
            self.status.set('Release all keys first'); return
        self.guide.cancel(); self.selected_prompt(key); self.paint()

    def paint(self):
        active={key for key,pair in EXPECTED.items() if pair in self.session.active}
        self.keyboard.update_state(self.session.results,active,self.session.target)
        passed=sum(r['status']=='pass' for r in self.session.results.values())
        self.count.set(f'{passed} / {len(EXPECTED)} keys passed')

    def check_failed(self,key):
        a,b=EXPECTED[key]
        self.prompt.set('Check '+key)
        self.status.set(f'Its wires: FPC {a} + {b} (Teensy pins {WIRING[a]} + {WIRING[b]}). Click the key to test it again.')

    def handle(self,event):
        kind=event.get('type')
        if kind=='hello':
            self.identified=True; self.metadata['firmware']=event
            self.set_connected(True); self.status.set('')
            self.lights.enable(True); self.start()
        elif kind=='started':
            self.scanning=True; self.last_state=time.monotonic()
            self.guide.begin()
        elif kind=='state' and self.scanning:
            try: pairs=parse_pairs(event.get('pairs'))
            except ValueError: self.reset_scan(); return
            self.last_state=time.monotonic()
            # T14 mouse buttons go to the TrackPoint tab; everything else is a key test.
            buttons={pair for pair in pairs if pair in BUTTONS.values()}
            self.mouse.feed(buttons); pairs-=buttons
            result,next_key=self.guide.feed(pairs)
            if result:
                key,status=result
                self.save_session()
                if status!='pass': self.check_failed(key)
                elif next_key is None and self.session.next_key() is None:
                    passed=sum(r['status']=='pass' for r in self.session.results.values())
                    self.prompt.set('All keys passed' if passed==len(EXPECTED) else 'Check the orange keys')
                    self.status.set('Click any key to test it again. Results are saved in diagnostic-results.')
            if next_key: self.selected_prompt(next_key)
            elif pairs and self.session.target: self.status.set('Release the key' if len(pairs)==1 else 'Release all keys')
            self.paint()
        elif kind=='fault':
            self.reset_scan()
            self.prompt.set('Check the wiring')
            self.status.set(f'FPC {event.get("fpc")} is stuck low: that wire touches ground or sits on the wrong contact.')
        elif kind in ('error','stopped'):
            self.reset_scan()  # restarted automatically
        elif kind=='connection_error':
            self.retry_at=time.monotonic()+3; self.waiting(event.get('message','Connection error'))
        elif kind=='trackpoint':
            self.mouse.set_status(event.get('status','unknown'))
        elif kind=='motion':
            try: self.mouse.motion(int(event['dx']),int(event['dy']))
            except (KeyError,TypeError,ValueError): pass
        elif kind=='disconnected':
            problem=self.prompt.get()=='Can’t talk to the Teensy'
            self.connection=None; self.identified=False; self.lights.enable(False); self.reset_scan()
            if not problem: self.waiting()

    def poll(self):
        for _ in range(200):
            try: event=self.events.get_nowait()
            except queue.Empty: break
            self.handle(event)
        now=time.monotonic()
        if self.autoconnect and not self.connection and now>=self.retry_at:
            self.retry_at=now+1
            try: self.connect()
            except Exception as exc: self.waiting(str(exc))
        # Keep testing without any buttons: restart after faults, errors or a stall.
        if self.identified and not self.scanning and now-self.started_at>2: self.start()
        if self.scanning and now-self.last_state>2: self.reset_scan()
        self.poll_id=self.root.after(30,self.poll)

    def close(self):
        self.root.after_cancel(self.poll_id)
        if self.connection:
            self.connection.close(); self.connection.thread.join(timeout=1)
        self.root.destroy()


def main():
    parser=argparse.ArgumentParser(description='T14 keyboard diagnostics')
    parser.add_argument('--port',help='Serial port, if the Teensy is not found automatically')
    args=parser.parse_args()
    root=tk.Tk(); App(root,args.port)
    root.mainloop()


if __name__=='__main__': main()
