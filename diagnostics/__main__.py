import argparse
import json
import queue
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from .model import Session, Guide, EXPECTED, WIRING, parse_pairs
from .keyboard import Keyboard
from .mouse import MousePanel
from .transport import Connection


class App:
    def __init__(self,root,demo=False):
        self.root,self.demo=root,demo
        self.session=Session(); self.guide=Guide(self.session)
        self.events=queue.Queue(); self.connection=None
        self.identified=self.scanning=False
        self.last_state=0
        self.metadata={'mode':'simulation' if demo else 'hardware'}
        self.report_dir=self.new_report_dir()
        root.title('T14 test' + (' · Demo' if demo else ''))
        root.geometry('1160x720'); root.minsize(920,650)
        root.configure(bg='#17191c')
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',background='#17191c',foreground='#e9eaec',font=('Arial',11))
        style.configure('TButton',background='#30343b',padding=(12,7),borderwidth=0)
        style.map('TButton',background=[('active','#424852')],foreground=[('disabled','#777c85')])
        style.configure('TCombobox',fieldbackground='#30343b',background='#30343b',foreground='#ffffff')
        style.map('TCombobox',fieldbackground=[('readonly','#30343b')])
        style.configure('TNotebook',borderwidth=0)
        style.configure('TNotebook.Tab',background='#25282e',padding=(20,8))
        style.map('TNotebook.Tab',background=[('selected','#424852')])
        style.configure('Title.TLabel',font=('Arial',21,'bold'))
        shell=ttk.Frame(root,padding=16); shell.pack(fill='both',expand=True)
        bar=ttk.Frame(shell); bar.pack(fill='x',pady=(0,12))
        ttk.Label(bar,text='T14',style='Title.TLabel').pack(side='left',padx=(0,20))
        self.port=ttk.Combobox(bar,width=12,postcommand=self.refresh)
        self.port.pack(side='left',padx=(0,6))
        self.connect_button=ttk.Button(bar,text='Connect',command=self.connect)
        self.connect_button.pack(side='left')
        self.count=tk.StringVar()
        ttk.Label(bar,textvariable=self.count).pack(side='right')
        self.tabs=ttk.Notebook(shell); self.tabs.pack(fill='both',expand=True)
        self.keys_tab=ttk.Frame(self.tabs,padding=(8,12))
        self.tabs.add(self.keys_tab,text='Keyboard')
        self.prompt=tk.StringVar(value='Connect your Pico')
        ttk.Label(self.keys_tab,textvariable=self.prompt,style='Title.TLabel').pack(anchor='w')
        self.status=tk.StringVar(value='')
        ttk.Label(self.keys_tab,textvariable=self.status).pack(anchor='w',pady=(5,0))
        self.keyboard=Keyboard(self.keys_tab,self.select,self.show_mouse)
        self.keyboard.pack(fill='x',pady=8)
        controls=ttk.Frame(self.keys_tab); controls.pack(fill='x')
        self.start_button=ttk.Button(controls,text='Start',command=self.start_scan,state='disabled')
        self.start_button.pack(side='left')
        ttk.Button(controls,text='Pause',command=self.stop_scan).pack(side='left',padx=6)
        ttk.Button(controls,text='Save',command=self.export).pack(side='left')
        ttk.Button(controls,text='Open results',command=self.open_report).pack(side='left',padx=6)
        ttk.Button(controls,text='Details',command=self.toggle_details).pack(side='right')
        if demo: ttk.Button(controls,text='Simulate key',command=self.simulate).pack(side='left')
        self.log=tk.Text(self.keys_tab,height=4,bg='#202327',fg='#bfc6cf',state='disabled',relief='flat',wrap='word')
        self.mouse=MousePanel(self.tabs,self.mouse_changed)
        self.metadata['mouse']=self.mouse.state.report()
        self.tabs.add(self.mouse,text='Mouse')
        self.refresh(); self.paint()
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.poll_id=root.after(30,self.poll)
        if demo:
            self.identified=True; self.start_button.config(state='normal')
            self.prompt.set('Demo'); self.status.set('Click Start')

    def show_mouse(self): self.tabs.select(self.mouse)

    def toggle_details(self):
        if self.log.winfo_manager(): self.log.pack_forget()
        else: self.log.pack(fill='both',expand=True,pady=8)

    def note(self,text):
        self.log.config(state='normal')
        self.log.insert('end',time.strftime('%H:%M:%S')+'  '+text+'\n')
        if int(self.log.index('end-1c').split('.')[0])>500: self.log.delete('1.0','100.0')
        self.log.see('end'); self.log.config(state='disabled')

    def new_report_dir(self):
        return Path('diagnostic-results')/('simulation-' if self.demo else 'hardware-')/datetime.now().strftime('%Y%m%d-%H%M%S-%f')

    def save_session(self):
        try: self.session.export(self.report_dir,self.metadata)
        except OSError as exc:
            self.status.set('Could not save results'); self.note(str(exc))

    def mouse_changed(self,report):
        if self.metadata.get('mouse')!=report:
            self.metadata['mouse']=report
            self.save_session()

    def refresh(self):
        if self.demo: self.port.set('Demo'); return
        from serial.tools import list_ports
        ports=list(list_ports.comports())
        self.port['values']=[p.device for p in ports]
        if not self.port.get() and ports:
            self.port.set(next((p.device for p in ports if p.vid==0x2e8a),ports[0].device))

    def connect(self):
        if self.demo: return
        if self.connection:
            self.disconnect(); return
        if not self.port.get(): self.status.set('Choose a port'); return
        self.metadata['port']=self.port.get()
        self.events=queue.Queue()
        self.connection=Connection(self.port.get(),self.events)
        self.connection.start()
        self.prompt.set('Connecting…')

    def disconnect(self):
        if self.connection: self.connection.close()
        self.scanning=False; self.guide.cancel(); self.session.cancel(); self.paint()

    def start_scan(self):
        if not self.identified or self.scanning: return
        if all(self.session.results.get(k,{}).get('status')=='pass' for k in EXPECTED):
            if not messagebox.askyesno('Test again','Start a new test? Your saved results will stay.'): return
            self.session=Session(); self.guide=Guide(self.session); self.report_dir=self.new_report_dir()
        self.session.cancel(); self.guide.cancel()
        self.start_button.config(state='disabled')
        if self.demo:
            self.events.put({'type':'started'}); self.events.put({'type':'state','pairs':[]})
        elif self.connection: self.connection.send('START t14-fpc-v1')

    def stop_scan(self):
        if self.connection: self.connection.send('STOP')
        self.scanning=False; self.guide.cancel(); self.session.cancel()
        self.start_button.config(state='normal' if self.identified else 'disabled')
        self.prompt.set('Paused'); self.status.set('Click Start to continue'); self.paint()

    def selected_prompt(self,key):
        self.prompt.set('Press '+key)
        self.status.set('Press and release')
        a,b=EXPECTED[key]
        self.note(f'{key}: FPC {a}/{b}, GP{WIRING[a]}/GP{WIRING[b]}')

    def select(self,key):
        if not self.scanning: self.status.set('Click Start first'); return
        try: self.session.arm(key)
        except ValueError:
            self.status.set('Release all keys first'); return
        self.guide.cancel(); self.selected_prompt(key); self.paint()

    def simulate(self):
        if self.scanning and self.session.target:
            self.events.put({'type':'state','pairs':[list(EXPECTED[self.session.target])]})
            self.root.after(100,lambda:self.events.put({'type':'state','pairs':[]}))

    def paint(self):
        active={key for key,pair in EXPECTED.items() if pair in self.session.active}
        self.keyboard.update_state(self.session.results,active,self.session.target)
        passed=sum(r['status']=='pass' for r in self.session.results.values())
        self.count.set(f'{passed} / {len(EXPECTED)} passed')

    def handle(self,event):
        kind=event.get('type')
        if kind=='hello':
            self.identified=True; self.metadata['firmware']=event
            self.start_button.config(state='normal')
            self.connect_button.config(text='Disconnect')
            if len(self.session.results)!=84: self.prompt.set('Ready')
            self.status.set('Click Start')
        elif kind=='started':
            self.scanning=True; self.last_state=time.monotonic()
            self.start_button.config(state='disabled')
            self.guide.begin(); self.prompt.set('Release all keys')
        elif kind=='state' and self.scanning:
            try: pairs=parse_pairs(event.get('pairs'))
            except ValueError as exc:
                self.stop_scan(); self.status.set('Bad scan data'); self.note(str(exc)); return
            self.last_state=time.monotonic()
            previous=self.session.active.copy()
            result,next_key=self.guide.feed(pairs)
            if pairs!=previous: self.note(f'Pairs: {sorted(pairs)}')
            if result:
                key,status=result
                self.note(f'{key}: {status}')
                self.save_session()
                if status!='pass':
                    self.prompt.set('Check '+key)
                    self.status.set('Click the key to try again')
                elif next_key is None and self.session.next_key() is None:
                    passed=sum(r['status']=='pass' for r in self.session.results.values())
                    self.prompt.set('All keys passed' if passed==84 else 'Check the orange keys')
                    self.status.set('Results saved')
            if next_key: self.selected_prompt(next_key)
            elif pairs and self.session.target: self.status.set('Release the key' if len(pairs)==1 else 'Release all keys')
            self.paint()
        elif kind in ('fault','error','connection_error'):
            self.scanning=False; self.guide.cancel(); self.session.cancel(); self.paint()
            self.prompt.set('Check connection')
            self.status.set('FPC '+str(event['fpc'])+' is stuck low' if 'fpc' in event else event.get('message','Connection error'))
            self.note(str(event))
            self.start_button.config(state='normal' if self.identified else 'disabled')
        elif kind=='stopped':
            self.scanning=False; self.guide.cancel(); self.session.cancel(); self.paint()
            self.start_button.config(state='normal' if self.identified else 'disabled')
            self.prompt.set('Paused'); self.status.set('Click Start to continue')
        elif kind=='disconnected':
            self.connection=None; self.identified=False; self.scanning=False
            self.guide.cancel(); self.session.cancel(); self.paint()
            self.start_button.config(state='disabled'); self.connect_button.config(text='Connect')
            self.prompt.set('Disconnected')

    def poll(self):
        for _ in range(200):
            try: event=self.events.get_nowait()
            except queue.Empty: break
            self.handle(event)
        if self.scanning and not self.demo and time.monotonic()-self.last_state>2:
            self.stop_scan(); self.status.set('Connection lost. Reconnect your Pico.')
        self.poll_id=self.root.after(30,self.poll)

    def export(self):
        parent=filedialog.askdirectory(title='Save results')
        if not parent: return
        try:
            folder=self.session.export(Path(parent)/('t14-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')),self.metadata)
        except OSError as exc: messagebox.showerror('Could not save',str(exc)); return
        self.status.set('Results saved'); self.note(str(folder))

    def load_report(self,path):
        # Parse and validate everything before replacing the current session.
        report=json.loads(Path(path).read_text(encoding='utf-8'))
        if report.get('metadata',{}).get('mode')!=self.metadata['mode']:
            raise ValueError('This report is from a different test mode')
        if {int(k):v for k,v in report['wiring'].items()}!=WIRING:
            raise ValueError('This report uses different wiring')
        loaded=Session()
        if set(report['keys'])!=set(EXPECTED): raise ValueError('Incomplete key list')
        for key,result in report['keys'].items():
            if tuple(result['expected'])!=EXPECTED[key]: raise ValueError('Different reference mapping')
            status=result['status']; observed=sorted(parse_pairs(result['observed']))
            if status not in ('pass','mismatch','ambiguous','untested'): raise ValueError('Unknown result')
            if status=='pass' and observed!=[EXPECTED[key]]: raise ValueError('Invalid pass result')
            if status!='untested': loaded.results[key]={'status':status,'observed':observed}
        if self.scanning: self.stop_scan()
        self.session=loaded; self.guide=Guide(loaded); self.report_dir=self.new_report_dir()
        self.metadata['loaded_from']=str(Path(path).resolve())
        self.prompt.set('All keys passed' if all(v['status']=='pass' for v in loaded.results.values()) and len(loaded.results)==84 else 'Results loaded')
        self.status.set('Click Start to test again'); self.paint()

    def open_report(self):
        path=filedialog.askopenfilename(title='Open results',filetypes=[('Test report','*.json')])
        if path:
            try: self.load_report(path)
            except (ValueError,KeyError,TypeError,OSError) as exc: messagebox.showerror('Could not open',str(exc))

    def close(self):
        self.root.after_cancel(self.poll_id)
        if self.connection:
            self.connection.close(); self.connection.thread.join(timeout=1)
        self.root.destroy()


def main():
    parser=argparse.ArgumentParser(description='T14 keyboard diagnostics')
    parser.add_argument('--demo',action='store_true')
    parser.add_argument('--port')
    parser.add_argument('--report',help='Open a saved report')
    args=parser.parse_args()
    root=tk.Tk(); app=App(root,args.demo)
    if args.report:
        try: app.load_report(args.report)
        except (ValueError,KeyError,TypeError,OSError) as exc: messagebox.showerror('Could not open',str(exc))
    if args.port and not args.demo:
        app.port.set(args.port); root.after(100,app.connect)
    root.mainloop()


if __name__=='__main__': main()
