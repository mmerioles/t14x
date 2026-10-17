"""T14 ANSI layout drawn with Tk primitives; no external image dependencies."""
import tkinter as tk
from tkinter import font as tkfont

KEYS = []


def row(y, entries, height=0.9):
    x=0
    for key,width in entries:
        KEYS.append((key,x,y,width,height))
        x+=width


# Function row, four groups, matching the supplied T14 photo.
KEYS.append(('Esc',0,0,1,.65))
x=1.15
for i in range(1,13):
    if i in (5,9): x+=.15
    KEYS.append((f'F{i}',x,0,.76,.65)); x+=.76
x+=.2
nav_width=(15-x)/4
for key in ['Home','End','Insert','Delete']:
    KEYS.append((key,x,0,nav_width,.65))
    x+=nav_width
row(.82,[(k,1) for k in ['`',*list('1234567890'),'-','=']]+[('Backspace',2)])
row(1.85,[('Tab',1.5)]+[(k,1) for k in list('QWERTYUIOP')+['[',']']]+[('\\',1.5)])
row(2.88,[('Caps Lock',1.75)]+[(k,1) for k in list('ASDFGHJKL')+[';',"'"]]+[('Enter',2.25)])
row(3.91,[('LShift',2.25)]+[(k,1) for k in list('ZXCVBNM')+[',','.','/']]+[('RShift',2.75)])
row(4.94,[(k,1) for k in ['Fn','LCtrl','Super','LAlt']]+[('Space',5)]+[(k,1) for k in ['RAlt','PrtSc','RCtrl']])
for x,key in enumerate(['PgUp','Up','PgDn'],12): KEYS.append((key,x,4.94,1,.43))
for x,key in enumerate(['Left','Down','Right'],12): KEYS.append((key,x,5.41,1,.43))

DISPLAY={'LShift':'Shift','RShift':'Shift','LCtrl':'Ctrl','RCtrl':'Ctrl',
         'LAlt':'Alt','RAlt':'Alt','Caps Lock':'CapsLock','Super':'⊞','Space':'',
         'Up':'↑','Left':'←','Down':'↓','Right':'→','`':'~\n`',
         '1':'!\n1','2':'@\n2','3':'#\n3','4':'$\n4','5':'%\n5',
         '6':'^\n6','7':'&\n7','8':'*\n8','9':'(\n9','0':')\n0',
         '-':'_\n-','=':'+\n=','[':'{\n[',']':'}\n]','\\':'|\n\\',
         ';':':\n;',"'":'"\n\'',',':'<\n,','.':'>\n.','/':'?\n/'}
DISPLAY.update({'Esc':'FnLock\nEsc','F1':'Mute\nF1','F2':'Vol −\nF2','F3':'Vol +\nF3',
                'F4':'Mic\nF4','F5':'Light −\nF5','F6':'Light +\nF6','F7':'Display\nF7',
                'F8':'Wi-Fi\nF8','F9':'Settings\nF9','F10':'Call\nF10',
                'F11':'Hang up\nF11','F12':'★\nF12'})


class Keyboard(tk.Canvas):
    def __init__(self,parent,on_key,on_mouse):
        super().__init__(parent,bg='#17191c',highlightthickness=0,height=300)
        self.on_key,self.on_mouse=on_key,on_mouse
        self.results={}; self.active=set(); self.target=None
        self.rectangles={}
        self.bind('<Configure>',lambda _:self.draw())
        self.bind('<Button-1>',self.click)

    def update_state(self,results,active,target):
        self.results,self.active,self.target=results,active,target
        self.draw()

    def keycap(self,x1,y1,x2,y2,**options):
        r=5
        return self.create_polygon(x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,
                                   x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,
                                   x1,y2,x1,y2-r,x1,y1+r,x1,y1,
                                   smooth=True,splinesteps=12,**options)

    def top_row_font(self,unit,vertical):
        """Largest font that fits every top-row label, so F1-F12 all match."""
        size=int(min(unit/5.5,11))
        if not hasattr(self,'_top_font'): self._top_font=tkfont.Font(family='Arial')
        font=self._top_font; font.configure(size=size)
        while size>6:
            fits=all(font.measure(line)<=w*unit-12 and font.metrics('linespace')*len(DISPLAY.get(k,k).split('\n'))<=h*vertical-7
                     for k,_,y,w,h in KEYS if y==0 for line in DISPLAY.get(k,k).split('\n'))
            if fits: break
            size-=1; font.configure(size=size)
        return font

    def draw(self):
        self.delete('all'); self.rectangles={}
        # Fit both ways: 15 units across, 6.7 rows down (keys plus mouse buttons).
        # Keys may be up to 10% taller or shorter than wide, to use the space.
        width,height=max(self.winfo_width(),300),max(self.winfo_height(),150)
        rows=(height-6)/6.7
        unit=min((width-4)/15,rows/0.9)
        vertical=min(unit*1.1,rows)
        ox,oy=(width-15*unit+5)/2,max(2,(height-6.7*vertical)/2)
        top_font=self.top_row_font(unit,vertical)
        for key,x,y,w,h in KEYS:
            x1,y1=ox+x*unit,oy+y*vertical
            x2,y2=x1+w*unit-5,y1+h*vertical-3
            self.rectangles[key]=(x1,y1,x2,y2)
            result=self.results.get(key,{}).get('status')
            fill='#292c31'; border='#484b52'; thickness=1
            if result=='pass': border='#5bd28b'; thickness=2
            elif result: border='#f5ac57'; thickness=2
            if key==self.target: border='#ededed'; thickness=3
            if key in self.active: fill='#245c82'
            # Bevel and inset surface follow the dark physical keycaps.
            self.keycap(x1,y1+3,x2,y2+3,fill='#0b0d0f',outline='')
            self.keycap(x1,y1,x2,y2,fill=fill,outline=border,width=thickness)
            label=DISPLAY.get(key,key)
            if y==0:
                # One size for the whole top row: function dim above, key name below.
                lines=label.split('\n')
                if len(lines)==2:
                    gap=top_font.metrics('linespace')/2
                    self.create_text((x1+x2)/2,(y1+y2)/2-gap,text=lines[0],fill='#9aa0a8',font=top_font)
                    self.create_text((x1+x2)/2,(y1+y2)/2+gap,text=lines[1],fill='#f0f0f0',font=top_font)
                else: self.create_text((x1+x2)/2,(y1+y2)/2,text=label,fill='#f0f0f0',font=top_font)
                if result=='pass': self.create_oval(x2-9,y1+5,x2-5,y1+9,fill='#5bd28b',outline='')
                continue
            size=max(9,int(min(unit/5,14)))
            font=tkfont.Font(family='Arial',size=size)
            while size>7 and (max(font.measure(line) for line in label.split('\n'))>x2-x1-10
                             or font.metrics('linespace')*len(label.split('\n'))>y2-y1-4):
                size-=1; font.configure(size=size)
            if key=='Super':
                cx,cy=(x1+x2)/2,(y1+y2)/2
                for dx,dy in [(-8,-8),(1,-8),(-8,1),(1,1)]:
                    self.create_rectangle(cx+dx,cy+dy,cx+dx+7,cy+dy+7,fill='#eeeeee',outline='')
            else: self.create_text((x1+x2)/2,(y1+y2)/2,text=label,fill='#f0f0f0',font=('Arial',size))
            if result=='pass': self.create_oval(x2-9,y1+5,x2-5,y1+9,fill='#5bd28b',outline='')
        # Red TrackPoint between G/H/B and the three physical mouse buttons below.
        tx,ty=ox+6.75*unit,oy+3.84*vertical
        self.create_oval(tx-11,ty-11,tx+11,ty+11,fill='#e13d4d',outline='#ff6675',tags='mouse')
        by=oy+6.0*vertical
        for name,x,w in [('Left',4.3,2),('Middle',6.3,1),('Right',7.3,2)]:
            self.create_rectangle(ox+x*unit,by,ox+(x+w)*unit-4,by+.65*vertical,fill='#292c31',outline='#484b52',tags='mouse')
            self.create_line(ox+x*unit+6,by+.65*vertical-4,ox+(x+w)*unit-10,by+.65*vertical-4,fill='#c83b4a',width=2,tags='mouse')

    def click(self,event):
        current=self.find_withtag('current')
        if current and 'mouse' in self.gettags(current[0]): self.on_mouse(); return
        for key,(x1,y1,x2,y2) in self.rectangles.items():
            if x1<=event.x<=x2 and y1<=event.y<=y2:
                self.on_key(key); return
