"""UNO-style flat controls: thin grey track, orange thumb, dark popup."""
import tkinter as tk
from live_creator.ui.theme import *

class Button(tk.Canvas):
    def __init__(self,parent,text,command,width=72,height=30):
        super().__init__(parent,width=width,height=height,bg=PANEL2,highlightthickness=1,highlightbackground=EDGE)
        self.text=text;self.command=command;self.active=False
        self.bind('<Configure>',lambda e:self.draw())
        self.bind('<Enter>',lambda e:self.configure(highlightbackground=ORANGE))
        self.bind('<Leave>',lambda e:self.configure(highlightbackground=EDGE))
        self.bind('<Button-1>',lambda e:command())
        self.bind('<Return>',lambda e:command());self.configure(takefocus=True)
    def draw(self):
        self.delete('all');self.configure(bg=ORANGE2 if self.active else PANEL2)
        self.create_text(self.winfo_width()/2,self.winfo_height()/2,text=self.text,fill=TEXT,font=('Segoe UI',10))
    def set(self,text,active=False):self.text=text;self.active=active;self.draw()

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
        if self.last-self.first<.999:line(8+length*self.first,8+length*self.last,ORANGE,5)
    def move(self,e):
        length=max(1,(self.winfo_width() if self.horizontal else self.winfo_height())-16)
        v=((e.x if self.horizontal else e.y)-8)/length-(self.last-self.first)/2
        self.command('moveto',max(0,min(1-(self.last-self.first),v)))

class Dropdown(Button):
    def __init__(self,parent,options,command):
        self.options=options;self.choice=options[0];self.callback=command
        super().__init__(parent,self.choice+'  ▾',self.open,width=224)
    def open(self):
        menu=tk.Menu(self,tearoff=False,bg=PANEL2,fg=TEXT,activebackground=ORANGE2,activeforeground=TEXT,bd=1,relief='solid',font=('Segoe UI',10))
        for option in self.options:menu.add_command(label=option,command=lambda o=option:self.choose(o))
        try:menu.tk_popup(self.winfo_rootx(),self.winfo_rooty()+self.winfo_height())
        finally:menu.grab_release()
    def choose(self,value):self.choice=value;self.set(value+'  ▾');self.callback(value)
