"""TrackPoint, mouse-button, indicator LED and backlight checks, driven by the Teensy."""
import tkinter as tk
from tkinter import ttk
from .model import BUTTONS, LEDS

STEP=20  # TrackPoint counts in one direction that count as a deliberate push


class MouseState:
    def __init__(self):
        self.trackpoint='untested'  # result of the last start: ready or no response
        self.live=False
        self.directions=set()
        self.buttons=set()
        self.pressed=set()
        self.x=self.y=0

    def move(self,dx,dy):
        """Accumulate firmware motion in screen directions (dy positive is down)."""
        if not self.live: return
        self.x+=dx; self.y+=dy
        if self.x>=STEP: self.directions.add('Right'); self.x=0
        if self.x<=-STEP: self.directions.add('Left'); self.x=0
        if self.y>=STEP: self.directions.add('Down'); self.y=0
        if self.y<=-STEP: self.directions.add('Up'); self.y=0

    def feed(self,pairs):
        """A button passes after its FPC pair is seen and then released."""
        active={name for name,pair in BUTTONS.items() if pair in pairs}
        self.buttons|=self.pressed-active
        self.pressed=active

    def status(self,status):
        self.live=status=='ready'
        if status in ('ready','no response'): self.trackpoint=status

    def cancel(self):
        """Scanning stopped: forget held buttons without counting them as released."""
        self.live=False
        self.pressed=set()

    def report(self):
        return {'trackpoint':self.trackpoint,'directions':sorted(self.directions),'buttons':sorted(self.buttons)}


class MousePanel(ttk.Frame):
    def __init__(self,parent,on_start,on_change):
        super().__init__(parent,padding=16)
        self.state=MouseState(); self.on_start,self.on_change=on_start,on_change
        ttk.Label(self,text='TrackPoint and buttons',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self,text='Push the red stick up, down, left and right, then click each T14 button.').pack(anchor='w',pady=(5,12))
        row=ttk.Frame(self); row.pack(fill='x')
        self.caption=tk.StringVar(value='Waiting for the Teensy')
        ttk.Label(row,textvariable=self.caption).pack(side='left')
        # Only shown when the TrackPoint did not answer; everything else starts by itself.
        self.retry=ttk.Button(row,text='Try again',command=self.on_start)
        self.area=tk.Canvas(self,bg='#202327',height=260,highlightthickness=1,highlightbackground='#454951')
        self.area.pack(fill='both',expand=True,pady=10)
        self.progress=tk.StringVar()
        ttk.Label(self,textvariable=self.progress).pack(anchor='w')
        self.dot=None; self.trail=[]
        self.show_progress()

    def set_status(self,status):
        self.state.status(status)
        self.caption.set({'starting':'Starting the TrackPoint…','ready':'TrackPoint ready',
                          'no response':'TrackPoint not responding: check CLK, DATA, RST, 3.3 V and GND',
                          'reset':'TrackPoint restarted by itself'}.get(status,status))
        if status in ('no response','reset'): self.retry.pack(side='left',padx=12)
        else: self.retry.pack_forget()
        self.update_report()

    def motion(self,dx,dy):
        self.state.move(dx,dy)
        width,height=max(self.area.winfo_width(),40),max(self.area.winfo_height(),40)
        if self.dot is None: self.dot=[width/2,height/2]
        self.dot[0]=min(max(self.dot[0]+dx/2,4),width-4)
        self.dot[1]=min(max(self.dot[1]+dy/2,4),height-4)
        x,y=self.dot
        self.trail.append(self.area.create_oval(x-3,y-3,x+3,y+3,fill='#e44655',outline=''))
        if len(self.trail)>150: self.area.delete(self.trail.pop(0))
        self.update_report()

    def feed(self,pairs):
        before=(set(self.state.buttons),set(self.state.pressed))
        self.state.feed(pairs)
        if before!=(self.state.buttons,self.state.pressed): self.update_report()

    def pause(self):
        self.state.cancel(); self.retry.pack_forget(); self.caption.set('Waiting for the Teensy'); self.update_report()

    def update_report(self):
        self.show_progress()
        self.on_change(self.state.report())

    def show_progress(self):
        s=self.state
        held=', '.join(sorted(s.pressed))
        self.progress.set(f'Directions {len(s.directions)}/4: {", ".join(sorted(s.directions)) or "—"}     '
                          f'Buttons {len(s.buttons)}/3: {", ".join(sorted(s.buttons)) or "—"}'+(f'     Holding: {held}' if held else ''))


class LightsPanel(ttk.Frame):
    def __init__(self,parent,send):
        super().__init__(parent,padding=16)
        self.send=send
        ttk.Label(self,text='Lights',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self,text='Tick an LED and check that the matching light on the keyboard turns on.').pack(anchor='w',pady=(5,12))
        self.leds={name:tk.BooleanVar() for name in LEDS}
        self.controls=[]
        for name,var in self.leds.items():
            box=ttk.Checkbutton(self,text=name+' LED',variable=var,command=self.apply_leds)
            box.pack(anchor='w',pady=3); self.controls.append(box)
        ttk.Label(self,text='Backlight').pack(anchor='w',pady=(16,4))
        self.level=tk.IntVar(value=0)
        row=ttk.Frame(self); row.pack(anchor='w')
        for value,name in enumerate(['Off','Low','High']):
            button=ttk.Radiobutton(row,text=name,value=value,variable=self.level,command=self.apply_backlight)
            button.pack(side='left',padx=(0,12)); self.controls.append(button)
        ttk.Label(self,text='No LED lights: check FPC 16 to 3.3 V. One LED dark: check its resistor and wire.\n'
                            'No backlight: check VIN, GND and the gate wire on pin 33.').pack(anchor='w',pady=(20,0))
        self.enable(False)

    def enable(self,on):
        for control in self.controls: control.state(['!disabled'] if on else ['disabled'])
        if not on: self.reset()

    def reset(self):
        """The firmware turns every light off when it stops."""
        for var in self.leds.values(): var.set(False)
        self.level.set(0)

    def apply_leds(self):
        self.send('LED '+str(sum(1<<i for i,var in enumerate(self.leds.values()) if var.get())))

    def apply_backlight(self): self.send('BACKLIGHT '+str(self.level.get()))
