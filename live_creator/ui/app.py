"""Standalone LIVE: single Core, read-only LOCAL library, no MIDI."""
import tkinter as tk
from tkinter import filedialog, messagebox
from live_creator.ui.controls import Button,Dropdown,Scrollbar
from live_creator.devices.uno import song
from live_creator.core.arrangement import Arrangement
from live_creator.devices.uno.library import PresetLibrary, children, default_root
from live_creator.ui.theme import BG,PANEL,PANEL2,EDGE,TEXT,MUTED,ORANGE,ORANGE2

class LiveCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Live Creator v0.3-alpha');self.geometry('1200x750');self.minsize(960,600);self.configure(bg=BG)
        self.model=Arrangement();self.library=PresetLibrary();self.boxes=[];self.pad_boxes=[];self.drag=None;self.source=None;self.paths={}
        self.status=tk.StringVar()
        self.mode='CREATOR';self.job=None;self.dirty=False;self.song_path=None
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.columnconfigure(1,weight=1);self.rowconfigure(2,weight=1)
        modes=tk.Frame(self,bg=BG);modes.grid(row=0,column=0,columnspan=3,sticky='e',padx=12,pady=(8,4))
        self.mode_buttons={}
        for name in ['CREATOR','LIVE']:
            button=Button(modes,name,lambda n=name:self.set_mode(n));button.pack(side='left',padx=2);self.mode_buttons[name]=button
        top=tk.Frame(self,bg=BG);top.grid(row=1,column=0,columnspan=3,sticky='ew',padx=12,pady=(0,8));top.columnconfigure(0,weight=1)
        self.left=left=tk.Frame(self,bg=PANEL,width=260,highlightbackground=EDGE,highlightthickness=1);left.grid(row=2,column=0,sticky='nsew',padx=(12,6),pady=(0,12));left.grid_propagate(False)
        left.rowconfigure(1,weight=1);left.columnconfigure(0,weight=1)
        header=tk.Frame(left,bg=PANEL);header.grid(row=0,column=0,sticky='ew')
        self.browser_mode=Dropdown(header,['LOCAL PRESETS','HARDWARE PRESETS'],lambda value:self.populate());self.browser_mode.pack(fill='x',padx=8,pady=8)
        self.tree=tk.Canvas(left,bg=PANEL,highlightthickness=0);self.tree.grid(row=1,column=0,sticky='nsew')
        sb=Scrollbar(left,command=self.tree.yview);sb.grid(row=1,column=1,sticky='ns');self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind('<ButtonPress-1>',self.tree_press);self.tree.bind('<B1-Motion>',self.tree_motion);self.tree.bind('<ButtonRelease-1>',self.drop)
        self.tree.bind('<MouseWheel>',lambda e:self.tree.yview_scroll(-int(e.delta/120),'units'))
        self.tree.bind('<Button-3>',self.browser_menu)
        center=tk.Frame(self,bg=BG);center.grid(row=2,column=1,sticky='nsew',padx=6,pady=(0,12));center.columnconfigure(0,weight=1);center.rowconfigure(0,weight=1)
        self.timeline=tk.Canvas(top,height=86,bg=PANEL,highlightbackground=EDGE,highlightthickness=1);self.timeline.grid(row=0,column=0,sticky='ew')
        scroll=Scrollbar(top,horizontal=True,command=self.timeline.xview);scroll.grid(row=1,column=0,sticky='ew');self.timeline.configure(xscrollcommand=scroll.set)
        self.timeline.bind('<ButtonPress-1>',self.press);self.timeline.bind('<B1-Motion>',self.motion);self.timeline.bind('<ButtonRelease-1>',self.release)
        self.timeline.bind('<Shift-Button-3>',self.loop_selection)
        self.grid_canvas=tk.Canvas(center,bg=BG,highlightthickness=0);self.grid_canvas.grid(row=0,column=0,sticky='nsew');self.grid_canvas.bind('<Configure>',lambda e:self.render_grid());self.grid_canvas.bind('<ButtonPress-1>',self.pad_click);self.grid_canvas.bind('<Shift-Button-3>',self.loop_selection)
        self.grid_canvas.bind('<Motion>',self.pad_hover);self.grid_canvas.bind('<Leave>',lambda e:self.grid_canvas.delete('hover'))
        self.work=work=tk.Frame(self,bg=PANEL,width=260,highlightbackground=EDGE,highlightthickness=1);work.grid(row=2,column=2,sticky='nsew',padx=(6,12),pady=(0,12));work.grid_propagate(False)
        work.pack_propagate(False)
        actions=tk.Frame(work,bg=PANEL);actions.pack(pady=10)
        for label,fn in [('NEW',self.new),('OPEN',self.open_song),('SAVE',self.save_song)]:Button(actions,label,fn,width=68).pack(side='left',padx=3)
        self.play_button=Button(work,'▶',self.toggle_play,width=104,height=104);self.play_button.pack(pady=20)
        tempo=tk.Frame(work,bg=PANEL);tempo.pack(pady=10)
        tk.Label(tempo,text='TEMPO',bg=PANEL,fg=TEXT,font=('Segoe UI',10)).pack(side='left',padx=8)
        self.tempo=tk.StringVar(value='120');entry=tk.Entry(tempo,textvariable=self.tempo,width=5,bg=PANEL2,fg=TEXT,insertbackground=ORANGE,relief='flat',highlightthickness=1,highlightbackground=EDGE,highlightcolor=ORANGE,font=('Segoe UI',11));entry.pack(side='left');entry.bind('<Return>',self.apply_tempo);entry.bind('<FocusOut>',self.apply_tempo)
        tk.Label(tempo,text='BPM',bg=PANEL,fg=MUTED).pack(side='left',padx=6)
        self.current=tk.Label(work,bg=PANEL,fg=TEXT,font=('Segoe UI',10),wraplength=230);self.current.pack(padx=10,pady=12)
        tk.Label(work,textvariable=self.status,bg=PANEL,fg=ORANGE,wraplength=230,font=('Segoe UI',10)).pack(padx=10)
        self.set_root(default_root());self.render()
        self.set_mode('CREATOR')
    def set_mode(self,mode):
        self.mode=mode
        for name,button in self.mode_buttons.items():button.set(name,name==mode)
    def apply_tempo(self,event=None):
        try:self.model.set_tempo(self.tempo.get());self.dirty=True;self.status.set('')
        except ValueError as error:self.status.set(str(error));self.tempo.set(str(self.model.tempo))
    def toggle_play(self):
        if self.model.playing:self.stop()
        else:
            self.model.start()
            if self.model.playing:self.schedule()
        self.render()
    def schedule(self):self.job=self.after(round(60000/self.model.tempo),self.tick)
    def tick(self):
        self.job=None;self.model.advance();self.render()
        if self.model.playing:self.schedule()
    def stop(self):
        if self.job is not None:self.after_cancel(self.job);self.job=None
        self.model.stop()
    def loop_selection(self,event=None):self.model.toggle_loop();self.render();return 'break'
    def discard(self):return not self.dirty or messagebox.askyesno('Live Creator','Discard unsaved changes?',parent=self)
    def new(self):
        if not self.discard():return
        self.stop();self.model=Arrangement();self.library=PresetLibrary();self.song_path=None;self.dirty=False;self.tempo.set('120');self.status.set('');self.render()
    def open_song(self):
        if not self.discard():return
        path=filedialog.askopenfilename(parent=self,filetypes=[('Live Creator song','*.unosong')])
        if not path:return
        try:model,library=song.load(path)
        except Exception as error:self.status.set(f'Open failed: {error}');return
        self.stop();self.model=model;self.library=library;self.song_path=path;self.tempo.set(str(model.tempo));self.dirty=False;self.status.set('');self.render()
    def save_song(self):
        path=self.song_path or filedialog.asksaveasfilename(parent=self,defaultextension='.unosong',filetypes=[('Live Creator song','*.unosong')])
        if not path:return
        try:song.save(path,self.model,self.library)
        except Exception as error:self.status.set(f'Save failed: {error}');return
        self.song_path=path;self.dirty=False;self.status.set('')
    def close(self):
        if self.discard():self.stop();self.destroy()
    def browser_menu(self,event):
        m=tk.Menu(self,tearoff=False,bg=PANEL2,fg=TEXT,activebackground=ORANGE2,activeforeground=TEXT)
        m.add_command(label='Open folder…',command=self.choose_root)
        try:m.tk_popup(event.x_root,event.y_root)
        finally:m.grab_release()
    def choose_root(self):
        folder=filedialog.askdirectory(parent=self)
        if folder:self.set_root(folder)
    def set_root(self,folder):
        self.root_folder=folder;self.expanded=set();self.browser_selected=None;self.populate()
    def populate(self):
        self.tree.delete('all');self.browser_rows=[]
        if self.browser_mode.choice=='HARDWARE PRESETS':
            self.tree.create_text(12,22,text='UNO not connected',anchor='w',fill=MUTED);return
        def walk(folder,depth):
            for path in children(folder):
                self.browser_rows.append((path,depth))
                if path in self.expanded:walk(path,depth+1)
        walk(self.root_folder,0)
        for i,(path,depth) in enumerate(self.browser_rows):
            y=14+i*27
            if path==self.browser_selected:self.tree.create_rectangle(4,y-12,238,y+12,fill=ORANGE2,outline=ORANGE)
            prefix=('▾ ' if path in self.expanded else '▸ ') if path.is_dir() else '  '
            name=path.name if path.is_dir() else path.stem;limit=max(8,26-depth*2)
            self.tree.create_text(10+depth*14,y,text=prefix+(name if len(name)<=limit else name[:limit-1]+'…'),anchor='w',fill=TEXT,font=('Segoe UI',10))
        self.tree.configure(scrollregion=(0,0,240,max(1,len(self.browser_rows)*27)))
    def tree_press(self,event):
        self.source=None;i=int(self.tree.canvasy(event.y)//27)
        if not 0<=i<len(self.browser_rows):return
        path,depth=self.browser_rows[i];self.browser_selected=path
        if path.is_dir():
            if path in self.expanded:self.expanded.remove(path)
            else:self.expanded.add(path)
        else:self.source=path;self.drag_start=(event.x_root,event.y_root)
        self.populate()
    def tree_motion(self,event):
        if self.source:
            self.configure(cursor='hand2');self.timeline.delete('ghost');x=self.timeline.canvasx(event.x_root-self.timeline.winfo_rootx())
            self.timeline.create_line(x,5,x,125,fill=ORANGE,width=2,tags='ghost')
    def drop(self,event):
        self.configure(cursor='');self.timeline.delete('ghost');path=self.source;self.source=None
        if path is None:return
        if abs(event.x_root-self.drag_start[0])+abs(event.y_root-self.drag_start[1])<6:return
        x=event.x_root-self.timeline.winfo_rootx();y=event.y_root-self.timeline.winfo_rooty()
        if not(0<=x<=self.timeline.winfo_width() and 0<=y<=self.timeline.winfo_height()):return
        x=self.timeline.canvasx(x)
        def action():
            preset=self.library.capture(path)
            for i,(x1,x2,b,s,e) in enumerate(self.boxes):
                if x<x1+10:self.model.insert(i,preset);self.model.select(s);return
                if x<x2-10:self.model.replace(b.id,preset);self.model.select(s);return
                if x<=x2+10:self.model.insert(i+1,preset);self.model.select(e+1);return
            self.model.insert(len(self.model.blocks),preset);self.model.select(self.model.length)
        self.perform(action)
    def selected(self):
        return next((b for b,s,e in self.model.ranges() if self.model.selected_step is not None and s<=self.model.selected_step<=e),None)
    def perform(self,fn):
        try:fn();self.stop();self.dirty=True;self.status.set('')
        except (ValueError,OSError) as error:self.status.set(str(error))
        self.render()
    def select(self,n,additive=False):
        self.model.select(n,additive);self.status.set('');self.render()
        for x1,x2,b,s,e in self.boxes:
            if s<=n<=e:
                px=x1+(n-s)*(x2-x1)/b.length;left=self.timeline.canvasx(0)
                if px<left or px>left+self.timeline.winfo_width()-30:self.timeline.xview_moveto(max(0,px-20)/self.total_width)
    def label(self,b):return self.library.names.get(b.preset,b.preset) if b.preset else 'EMPTY'
    def press(self,event):
        x=self.timeline.canvasx(event.x)
        for x1,x2,b,s,e in self.boxes:
            if x1<=x<=x2:
                self.select(min(e,s+int((x-x1)/(x2-x1)*b.length)),bool(getattr(event,'state',0)&5));self.drag=(b.id,self.timeline.canvasx(event.x),b.length,x>=x2-10);return
    def motion(self,event):
        if self.drag:
            self.timeline.delete('ghost');x=self.timeline.canvasx(event.x);self.timeline.create_line(x,5,x,125,fill=ORANGE,width=2,tags='ghost')
    def release(self,event):
        self.timeline.delete('ghost')
        if not self.drag:return
        id,x,length,resizing=self.drag;self.drag=None;delta=round((self.timeline.canvasx(event.x)-x)/64)
        if delta:self.perform(lambda:self.model.resize(id,length+delta) if resizing else self.model.move(id,delta))
    def pad_click(self,event):
        for n,x,y,size in self.pad_boxes:
            if x<=event.x<=x+size and y<=event.y<=y+size and n<=self.model.length:self.select(n,bool(getattr(event,'state',0)&5));return
    def pad_hover(self,event):
        self.grid_canvas.delete('hover')
        for n,x,y,size in self.pad_boxes:
            if n<=self.model.length and x<=event.x<=x+size and y<=event.y<=y+size:
                self.grid_canvas.create_rectangle(x,y,x+size,y+size,outline=TEXT,tags='hover');return
    def render(self):
        self.timeline.delete('all');self.boxes=[];x=12;selected=self.selected()
        for b,s,e in self.model.ranges():
            w=max(48,b.length*20) if b.preset is None else max(80,b.length*64);self.boxes.append((x,x+w,b,s,e));chosen=b.id in self.model.selection
            self.timeline.create_text(x+4,13,text=f'{s:02d}' if s==e else f'{s:02d}–{e:02d}',anchor='w',fill=TEXT,font=('Segoe UI',10))
            if b.preset is None:
                self.timeline.create_line(x+4,63,x+w-4,63,fill=ORANGE if chosen else EDGE,dash=(2,3));self.timeline.create_text(x+w/2,47,text='EMPTY',fill=MUTED,font=('Segoe UI',8))
            else:
                self.timeline.create_rectangle(x+2,27,x+w-2,73,fill=ORANGE2 if chosen else PANEL2,outline=ORANGE if chosen else EDGE)
                self.timeline.create_text(x+w/2,50,text=self.label(b),width=w-16,fill=TEXT,font=('Segoe UI',10))
                self.timeline.create_line(x+w-7,35,x+w-7,65,fill=MUTED,width=2)
            if self.model.loop_range and s<=self.model.loop_range[1] and e>=self.model.loop_range[0]:
                self.timeline.create_line(x+2,79,x+w-2,79,fill=ORANGE,width=2)
            if self.model.playhead is not None and s<=self.model.playhead<=e:
                px=x+(self.model.playhead-s)*w/b.length;self.timeline.create_line(px,25,px,75,fill=TEXT,width=2)
            x+=w
        self.total_width=max(self.timeline.winfo_width(),x+100);self.timeline.configure(scrollregion=(0,0,self.total_width,84));self.render_grid()
        self.play_button.set('■' if self.model.playing else '▶',self.model.playing)
        n=self.model.playhead if self.model.playing else self.model.selected_step
        b=next((b for b,s,e in self.model.ranges() if n is not None and s<=n<=e),None)
        self.current.configure(text=f'{n or 0:02d} / 64 · {self.label(b) if b else "—"}')
    def render_grid(self):
        c=self.grid_canvas;c.delete('all');self.pad_boxes=[];side=max(80,min(c.winfo_width()-24,c.winfo_height()-12));pitch=side/8;size=pitch*.88
        left=(c.winfo_width()-side)/2;top=6;selected=self.selected();steps=self.model.steps()
        for i in range(64):
            x=left+(i%8)*pitch;y=top+(i//8)*pitch;n=i+1;self.pad_boxes.append((n,x,y,size));active=i<len(steps)
            same=active and steps[i].block_id in self.model.selection;exact=n==self.model.selected_step
            c.create_rectangle(x,y,x+size,y+size,fill=ORANGE if exact else ORANGE2 if same else PANEL2 if active else PANEL,outline=TEXT if n==self.model.playhead else EDGE,width=2 if n==self.model.playhead else 1)
            c.create_text(x+size/2,y+size/2,text=f'{n:02d}' if active else '—',fill=BG if exact else TEXT if active else EDGE,font=('Segoe UI',10))
