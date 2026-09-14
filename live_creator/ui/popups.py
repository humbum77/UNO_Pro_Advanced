"""Shared dark object menus, color palette and marker prompt."""
import colorsys
import tkinter as tk
from .theme import PANEL,PANEL2,EDGE,TEXT,MUTED,ORANGE

PALETTE=[]
for value in (.30,.48,.66,.84):
    for hue in range(12):
        rgb=colorsys.hsv_to_rgb(hue/12,.48,value)
        PALETTE.append('#'+''.join(f'{round(c*255):02x}' for c in rgb))
PALETTE+=['#24282c','#51585e','#899198','#cbd0d4']

def contrast(color):
    rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    lum=sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))
    return '#101417' if lum>.179 else '#ffffff'

class Popup(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.withdraw();self.overrideredirect(True);self.transient(parent)
        self.configure(bg=EDGE);self.bind('<Escape>',lambda e:self.destroy())
    def show(self,x,y,width,height):
        x=max(0,min(int(x),self.winfo_screenwidth()-width));y=max(0,min(int(y),self.winfo_screenheight()-height))
        self.geometry(f'{width}x{height}+{x}+{y}');self.deiconify();self.lift();self.grab_set();self.focus_force()
        self.bind('<Button-1>',self.outside,add='+')
    def outside(self,event):
        if not(0<=event.x_root-self.winfo_rootx()<self.winfo_width() and 0<=event.y_root-self.winfo_rooty()<self.winfo_height()):self.destroy()

class ObjectMenu(Popup):
    def __init__(self,parent,items,x,y):
        super().__init__(parent);self.items=items;self.rows=[]
        self.canvas=tk.Canvas(self,bg=PANEL2,highlightthickness=1,highlightbackground=EDGE);self.canvas.pack(fill='both',expand=True)
        top=5
        for item in items:
            if item is None:self.canvas.create_line(8,top+4,218,top+4,fill=EDGE);top+=9;continue
            label,command,enabled,shortcut=item;self.rows.append((top,top+27,item))
            self.canvas.create_text(12,top+13,text=label,anchor='w',fill=TEXT if enabled else MUTED,font=('Segoe UI',10))
            self.canvas.create_text(215,top+13,text=shortcut,anchor='e',fill=MUTED,font=('Segoe UI',9));top+=27
        self.canvas.bind('<Motion>',self.hover);self.canvas.bind('<Button-1>',self.click)
        self.show(x,y,228,top+5)
    def hover(self,event):
        self.canvas.delete('hover')
        for y,y2,item in self.rows:
            if y<=event.y<y2 and item[2]:
                self.canvas.create_rectangle(3,y,224,y2,outline=ORANGE,tags='hover');break
    def click(self,event):
        for y,y2,item in self.rows:
            if y<=event.y<y2 and item[2]:
                command=item[1];self.destroy();command();return

class ColorPalette(Popup):
    def __init__(self,parent,color,callback,x,y):
        super().__init__(parent);self.callback=callback
        c=tk.Canvas(self,width=304,height=152,bg=PANEL2,highlightthickness=1,highlightbackground=EDGE);c.pack()
        for i,value in enumerate(PALETTE):
            cx=8+i%12*24;cy=8+i//12*27
            c.create_rectangle(cx,cy,cx+20,cy+22,fill=value,outline=ORANGE if value==color else EDGE,width=2)
        c.bind('<Button-1>',self.choose);self.show(x,y,306,152)
    def choose(self,event):
        col=int((event.x-8)//24);row=int((event.y-8)//27);i=row*12+col
        if 0<=col<12 and 0<=row<5 and i<len(PALETTE):
            color=PALETTE[i];self.destroy();self.callback(color)

class MarkerPrompt(Popup):
    def __init__(self,parent,text,callback,x,y):
        super().__init__(parent);self.callback=callback
        tk.Label(self,text='Marker',bg=PANEL2,fg=TEXT,font=('Segoe UI',10)).pack(fill='x')
        self.entry=tk.Entry(self,bg=PANEL,fg=TEXT,insertbackground=ORANGE,relief='flat',font=('Segoe UI',11));self.entry.pack(fill='x',padx=6,pady=6)
        self.entry.insert(0,text);self.entry.select_range(0,'end');self.entry.bind('<Return>',self.accept)
        self.show(x,y,250,64);self.entry.focus_set()
    def accept(self,event=None):
        text=self.entry.get();self.destroy();self.callback(text)
