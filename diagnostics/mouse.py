"""Host-pointer checks are explicitly separate from unwired T14 hardware."""
import tkinter as tk
from tkinter import ttk


class MouseState:
    def __init__(self):
        self.directions=set()
        self.buttons=set()
        self.pressed=set()
        self.last=None

    def move(self,x,y):
        if self.last is not None:
            dx,dy=x-self.last[0],y-self.last[1]
            if dx>=4: self.directions.add('Right')
            if dx<=-4: self.directions.add('Left')
            if dy>=4: self.directions.add('Down')
            if dy<=-4: self.directions.add('Up')
            if abs(dx)>=4 or abs(dy)>=4: self.last=(x,y)
        else: self.last=(x,y)

    def press(self,button):
        if button in ('Left','Middle','Right'): self.pressed.add(button)

    def release(self,button):
        if button in self.pressed:
            self.buttons.add(button)
            self.pressed.remove(button)

    def report(self):
        return {'source':'computer pointer (device identity unavailable)',
                't14_trackpoint':'not connected', 't14_buttons':'not connected',
                'directions':sorted(self.directions),'buttons':sorted(self.buttons)}


class MousePanel(ttk.Frame):
    def __init__(self,parent,on_change):
        super().__init__(parent,padding=16)
        self.state=MouseState(); self.enabled=False; self.on_change=on_change
        ttk.Label(self,text='T14 mouse is not connected',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self,text='The pointing stick and its buttons need separate wiring.').pack(anchor='w',pady=(5,16))
        self.toggle=ttk.Button(self,text='Test computer mouse',command=self.start)
        self.toggle.pack(anchor='w')
        self.caption=tk.StringVar(value='This checks your computer’s pointer, not the T14.')
        ttk.Label(self,textvariable=self.caption).pack(anchor='w',pady=10)
        self.area=tk.Canvas(self,bg='#202327',height=260,highlightthickness=1,highlightbackground='#454951')
        self.area.pack(fill='both',expand=True)
        self.area.bind('<Motion>',self.move)
        self.area.bind('<Leave>',lambda _:setattr(self.state,'last',None))
        self.area.bind('<ButtonPress>',self.press)
        self.winfo_toplevel().bind('<ButtonRelease>',self.release,add='+')
        self.winfo_toplevel().bind('<FocusOut>',lambda _:self.state.pressed.clear(),add='+')
        self.progress=tk.StringVar(value='Movement: 0/4    Buttons: 0/3')
        ttk.Label(self,textvariable=self.progress).pack(anchor='w',pady=10)
        self.trail=[]

    def start(self):
        self.state=MouseState(); self.enabled=True
        self.area.delete('all'); self.trail=[]
        self.toggle.config(text='Restart mouse test')
        self.caption.set('Move inside the box. Click left, middle, and right.')
        self.update_report()

    def move(self,event):
        if not self.enabled: return
        self.state.move(event.x,event.y)
        self.trail.append(self.area.create_oval(event.x-2,event.y-2,event.x+2,event.y+2,fill='#e44655',outline=''))
        if len(self.trail)>150: self.area.delete(self.trail.pop(0))
        self.update_report()

    @staticmethod
    def button(number): return {1:'Left',2:'Middle',3:'Right'}.get(number)

    def press(self,event):
        if self.enabled: self.state.press(self.button(event.num))

    def release(self,event):
        if self.enabled:
            self.state.release(self.button(event.num)); self.update_report()

    def update_report(self):
        self.progress.set(f'Movement: {len(self.state.directions)}/4    Buttons: {len(self.state.buttons)}/3')
        self.on_change(self.state.report())
