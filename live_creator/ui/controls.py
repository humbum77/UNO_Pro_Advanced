"""UNO-style flat controls: thin grey track, orange thumb, dark popup."""
import tkinter as tk
import ui_theme
from live_creator.ui.theme import *

class Button(tk.Canvas):
    """Shared pad-like button surface used by LIVE transport controls."""
    def __init__(self,parent,text,command,width=72,height=30):
        super().__init__(parent,width=width,height=height,bg=PANEL,highlightthickness=0)
        self.text=text;self.command=command;self.active=False
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',lambda e:command());self.bind('<Return>',lambda e:command());self.configure(takefocus=True)
    def _round(self,x1,y1,x2,y2,r,**kw):
        pts=(x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1)
        return self.create_polygon(*pts,smooth=True,splinesteps=20,**kw)
    @staticmethod
    def _shade(color,f):
        c=color.lstrip('#');v=[int(c[i:i+2],16) for i in (0,2,4)];return '#'+''.join(f'{max(0,min(255,round(n*f))):02x}' for n in v)
    def draw(self):
        self.delete('all');w=max(2,self.winfo_width()-1);h=max(2,self.winfo_height()-1);base=PANEL2
        # Very slight pad volume: edges lighter, centre darker.
        for i in range(7):
            q=i/6;ins=1+q*min(w,h)*.12;self._round(ins,ins,w-ins,h-ins,max(3,7-ins/3),fill=self._shade(base,1.045-.105*q),outline='')
        transport=self.text.startswith(('PLAY','STOP'));edge=ui_theme.TOKENS['dark']['play'] if transport else (ORANGE if self.active else EDGE)
        if transport and self.active and int(__import__('time').monotonic()*3)%2:edge=self._shade(edge,.55)
        self._round(1,1,w-1,h-1,7,fill='',outline=edge,width=2 if transport else 1)
        self.create_text(w/2,h/2,text=self.text,fill=TEXT,font=('Segoe UI',10,'bold' if transport else 'normal'))
    def set(self,text,active=False):self.text=text;self.active=active;self.draw()


class TransportButton(Button):
    """Dark raised hardware-style PLAY/STOP key with top-left illuminated legend."""
    def __init__(self,parent,text,command,width=72,height=30,label_color='#6fd34f'):
        self.label_color=label_color
        super().__init__(parent,text,command,width,height)
    def draw(self):
        self.delete('all');w=max(2,self.winfo_width()-1);h=max(2,self.winfo_height()-1);base='#1b1e20'
        # Deep lower/side face first: visible hardware key thickness.
        self._round(3,6,w-2,h-1,8,fill='#0b0d0e',outline='#08090a',width=1)
        # Raised top face with vertical bevel; no coloured body fill.
        top_h=max(12,h-8)
        for i in range(9):
            q=i/8;yy=2+q*top_h
            col=self._shade(base,1.20-.22*q)
            self.create_rectangle(5,yy,w-5,min(h-7,yy+max(2,top_h/8+1)),fill=col,outline='')
        self._round(3,2,w-3,h-7,8,fill='',outline='#3d4347',width=1)
        self.create_line(9,3,w-10,3,fill='#4a5054',width=1)
        label=self.label_color
        # Active transport: restrained legend glow plus a thin illuminated outline
        # in the button's own colour (PLAY green, STOP yellow).
        if self.active:
            glow=self._shade(label,.48)
            for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                self.create_text(11+dx,8+dy,text=self.text,anchor='nw',fill=glow,font=('Segoe UI',10,'bold'))
            self._round(3,2,w-3,h-7,8,fill='',outline=self._shade(label,.48),width=2)
            self._round(4,3,w-4,h-8,7,fill='',outline=label,width=1)
        self.create_text(11,8,text=self.text,anchor='nw',fill=label if self.active else self._shade(label,.72),font=('Segoe UI',10,'bold'))

class Scrollbar(tk.Canvas):
    def __init__(self,parent,command,horizontal=False):
        super().__init__(parent,bg=PANEL,highlightthickness=0,**({'height':14} if horizontal else {'width':14}))
        self.command=command;self.horizontal=horizontal;self.first=0;self.last=1
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.move);self.bind('<B1-Motion>',self.move)
    def set(self,first,last):self.first=float(first);self.last=float(last);self.draw()
    def draw(self):
        self.delete('all');length=(self.winfo_width() if self.horizontal else self.winfo_height())-16
        if length<=0:return
        def line(a,b,color,width):
            self.create_line(*((a,7,b,7) if self.horizontal else (7,a,7,b)),fill=color,width=width)
        line(8,length+8,EDGE,3)
        if self.last-self.first<.999:line(8+length*self.first,8+length*self.last,'#c9ced1',5)
    def move(self,e):
        length=max(1,(self.winfo_width() if self.horizontal else self.winfo_height())-16)
        v=((e.x if self.horizontal else e.y)-8)/length-(self.last-self.first)/2
        self.command('moveto',max(0,min(1-(self.last-self.first),v)))

class Dropdown(Button):
    def __init__(self,parent,options,command):
        self.options=options;self.choice=options[0];self.callback=command
        super().__init__(parent,self.choice+'  ▾',self.open,width=224)
    def open(self):
        menu=tk.Menu(self,tearoff=False,bg=PANEL2,fg=TEXT,activebackground=ORANGE,activeforeground='#0d1114',bd=1,relief='solid',font=('Segoe UI',10))
        for option in self.options:menu.add_command(label=option,command=lambda o=option:self.choose(o))
        try:menu.tk_popup(self.winfo_rootx(),self.winfo_rooty()+self.winfo_height())
        finally:menu.grab_release()
    def choose(self,value):self.choice=value;self.set(value+'  ▾');self.callback(value)
