"""UNO-themed editor for 64 songs. No MIDI or device writes."""
from pathlib import Path
from types import SimpleNamespace
import math,time
import tkinter as tk
from tkinter import filedialog
from live_creator.core.session import Session,color_for
from live_creator.core import state
from live_creator.devices.uno.library import PresetLibrary,children,default_root
from live_creator.ui.controls import Button,Dropdown,Scrollbar
from live_creator.ui.theme import BG,PANEL,PANEL2,EDGE,TEXT,MUTED,ORANGE

DELAY={'OFF':0,'5 s':5,'10 s':10,'15 s':15,'30 s':30,'45 s':45,'1 min':60}

class LiveCreator(tk.Tk):
    def __init__(self,state_path=None):
        super().__init__();self.title('Live Creator v0.4-alpha');self.geometry('1200x750');self.minsize(960,600);self.configure(bg=BG)
        self.state_path=Path(state_path) if state_path else Path(__file__).resolve().parents[2]/'LiveCreatorState.json'
        self.session=Session();self.load_failed=False
        try:
            if self.state_path.exists():self.session=state.load(self.state_path)
        except Exception as error:self.load_failed=True;self.load_error=str(error)
        self.library=PresetLibrary();self.boxes=[];self.pad_boxes=[];self.source=None;self.drag=None;self.save_job=None;self.timer=None;self.syncing=False
        self.status=tk.StringVar(value='State load failed: '+self.load_error if self.load_failed else '')
        self.columnconfigure(1,weight=1);self.rowconfigure(1,weight=1)
        top=tk.Frame(self,bg=BG);top.grid(row=0,column=0,columnspan=3,sticky='ew',padx=12,pady=(12,8));top.columnconfigure(0,weight=1)
        self.timeline=tk.Canvas(top,height=86,bg=PANEL,highlightbackground=EDGE,highlightthickness=1);self.timeline.grid(row=0,column=0,sticky='ew')
        scroll=Scrollbar(top,self.timeline.xview,horizontal=True);scroll.grid(row=1,column=0,sticky='ew');self.timeline.configure(xscrollcommand=scroll.set)
        self.timeline.bind('<ButtonPress-1>',self.press);self.timeline.bind('<B1-Motion>',self.motion);self.timeline.bind('<ButtonRelease-1>',self.release)
        self.timeline.bind('<Motion>',self.hover);self.timeline.bind('<Leave>',lambda e:self.timeline.delete('hover'));self.timeline.bind('<Shift-Button-3>',self.loop_selection)
        self.left=self.panel(0);self.work=self.panel(2)
        self.left.rowconfigure(1,weight=1);self.left.columnconfigure(0,weight=1)
        self.browser_mode=Dropdown(self.left,['LOCAL PRESETS','HARDWARE PRESETS'],lambda v:self.populate());self.browser_mode.grid(row=0,column=0,sticky='ew',padx=8,pady=8)
        self.tree=tk.Canvas(self.left,bg=PANEL,highlightthickness=0);self.tree.grid(row=1,column=0,sticky='nsew')
        sb=Scrollbar(self.left,self.tree.yview);sb.grid(row=1,column=1,sticky='ns');self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind('<ButtonPress-1>',self.tree_press);self.tree.bind('<B1-Motion>',self.tree_motion);self.tree.bind('<ButtonRelease-1>',self.drop);self.tree.bind('<Button-3>',self.browser_menu)
        self.tree.bind('<MouseWheel>',lambda e:self.tree.yview_scroll(-int(e.delta/120),'units'))
        self.grid_canvas=tk.Canvas(self,bg=BG,highlightthickness=0);self.grid_canvas.grid(row=1,column=1,sticky='nsew',padx=6,pady=(0,12))
        self.grid_canvas.bind('<Configure>',lambda e:self.render_grid());self.grid_canvas.bind('<Button-1>',self.pad_click)
        self.name=tk.StringVar();self.tempo=tk.StringVar();self.metrics=tk.StringVar();self.current=tk.StringVar();self.context=tk.StringVar()
        self.entry('NAME',self.name);self.entry('TEMPO',self.tempo)
        self.name.trace_add('write',self.edit_name)
        tk.Label(self.work,textvariable=self.metrics,bg=PANEL,fg=TEXT,justify='left',font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=10)
        tk.Label(self.work,text='PLAY DELAY',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=(10,4))
        self.delay=Dropdown(self.work,list(DELAY),self.edit_delay);self.delay.pack(padx=16,fill='x')
        self.play_button=Button(self.work,'PLAY',self.toggle_play,width=222,height=38);self.play_button.pack(padx=16,pady=18)
        for variable,color in [(self.current,TEXT),(self.context,MUTED),(self.status,ORANGE)]:tk.Label(self.work,textvariable=variable,bg=PANEL,fg=color,wraplength=224,justify='left',font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=6)
        self.bind('<space>',self.space);self.protocol('WM_DELETE_WINDOW',self.close)
        self.root_folder=self.session.global_settings.get('library_root',str(default_root()));self.expanded=set();self.browser_selected=None
        self.populate();self.sync_editor();self.render();self.timer=self.after(50,self.tick)
    @property
    def model(self):return self.session.song.timeline
    def panel(self,column):
        p=tk.Frame(self,bg=PANEL,width=260,highlightbackground=EDGE,highlightthickness=1);p.grid(row=1,column=column,sticky='nsew',padx=(12,6) if column==0 else (6,12),pady=(0,12));p.grid_propagate(False);p.pack_propagate(False);return p
    def entry(self,label,variable):
        tk.Label(self.work,text=label,bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=(12,4))
        e=tk.Entry(self.work,textvariable=variable,bg=PANEL2,fg=TEXT,insertbackground=ORANGE,relief='flat',highlightthickness=1,highlightbackground=EDGE,highlightcolor=ORANGE,font=('Segoe UI',11));e.pack(fill='x',padx=16)
        if label=='TEMPO':e.bind('<Return>',self.edit_tempo);e.bind('<FocusOut>',self.edit_tempo)
    def sync_editor(self):
        self.syncing=True;self.name.set(self.session.song.name);self.tempo.set(str(self.model.tempo));value=next(k for k,v in DELAY.items() if v==self.session.song.delay);self.delay.choice=value;self.delay.set(value+'  ▾');self.syncing=False
    def edit_name(self,*args):
        if self.syncing:return
        self.session.song.name=self.name.get()[:256];self.persist();self.render_grid()
    def edit_tempo(self,event=None):
        if self.syncing:return
        try:self.model.set_tempo(self.tempo.get());self.status.set('');self.persist()
        except ValueError as error:self.status.set(str(error));self.tempo.set(str(self.model.tempo))
        self.render()
    def edit_delay(self,value):self.session.song.delay=DELAY[value];self.persist()
    def persist(self):
        if self.save_job:self.after_cancel(self.save_job)
        self.save_job=self.after(300,self.flush)
    def flush(self):
        self.save_job=None
        if self.load_failed:return
        try:state.save(self.state_path,self.session)
        except OSError as error:self.status.set('State save failed: '+str(error))
    def close(self):
        if self.timer:self.after_cancel(self.timer)
        if self.save_job:self.after_cancel(self.save_job)
        self.flush();self.destroy()
    def space(self,event):
        if isinstance(self.focus_get(),(tk.Entry,tk.Text)):return
        self.toggle_play();return 'break'
    def toggle_play(self):
        self.session.toggle(time.monotonic());self.render()
    def tick(self):
        was_active=self.session.active
        self.session.update(time.monotonic())
        if was_active:self.render()
        self.timer=self.after(50,self.tick)
    def selected(self):return next((b for b,s,e in self.model.ranges() if self.model.selected_step is not None and s<=self.model.selected_step<=e),None)
    def select(self,n,additive=False):self.model.select(n,additive);self.render()
    def select_pad(self,n):
        self.drag=None;self.session.select_pad(n);self.timeline.xview_moveto(0);self.sync_editor();self.persist();self.render()
    def loop_selection(self,event=None):self.model.toggle_loop();self.persist();self.render();return 'break'
    def label(self,b):return self.library.label(b.preset) if b.preset else 'EMPTY'
    def perform(self,action):
        try:action();self.status.set('');self.persist()
        except (ValueError,OSError) as error:self.status.set(str(error))
        self.render()
    def browser_menu(self,event):
        m=tk.Menu(self,tearoff=False,bg=PANEL2,fg=TEXT,activebackground='#8a4b12',activeforeground=TEXT)
        m.add_command(label='Open folder…',command=self.choose_root)
        try:m.tk_popup(event.x_root,event.y_root)
        finally:m.grab_release()
    def choose_root(self):
        folder=filedialog.askdirectory(parent=self)
        if folder:self.set_root(folder);self.session.global_settings['library_root']=folder;self.persist()
    def set_root(self,folder):self.root_folder=folder;self.expanded=set();self.browser_selected=None;self.populate()
    def populate(self):
        self.tree.delete('all');self.browser_rows=[]
        if self.browser_mode.choice=='HARDWARE PRESETS':self.tree.create_text(12,22,text='UNO not connected',anchor='w',fill=MUTED);return
        def walk(folder,depth):
            for path in children(folder):
                self.browser_rows.append((path,depth))
                if path in self.expanded:walk(path,depth+1)
        walk(self.root_folder,0)
        for i,(path,depth) in enumerate(self.browser_rows):
            y=14+i*27
            if path==self.browser_selected:self.tree.create_rectangle(4,y-12,238,y+12,fill='#8a4b12',outline=ORANGE)
            prefix=('▾ ' if path in self.expanded else '▸ ') if path.is_dir() else '  ';name=path.name if path.is_dir() else path.stem;limit=max(8,26-depth*2)
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
        if self.source:self.configure(cursor='hand2')
    def drop(self,event):
        self.configure(cursor='');path=self.source;self.source=None
        if path is None:return
        if abs(event.x_root-self.drag_start[0])+abs(event.y_root-self.drag_start[1])<6:return
        x=event.x_root-self.timeline.winfo_rootx();y=event.y_root-self.timeline.winfo_rooty()
        if not(0<=x<=self.timeline.winfo_width() and 0<=y<=self.timeline.winfo_height()):return
        x=self.timeline.canvasx(x)
        def action():
            preset=self.library.capture(path)
            for i,(x1,x2,b,s,e) in enumerate(self.boxes):
                if x<x1+10:self.model.insert(i,preset);self.model.select(s);break
                if x<x2-10:self.model.replace(b.id,preset);self.model.select(s);break
                if x<=x2+10:self.model.insert(i+1,preset);self.model.select(e+1);break
            else:self.model.insert(len(self.model.blocks),preset);self.model.select(self.model.length)
            self.session.song.colors.setdefault(preset,color_for(preset))
        self.perform(action)
    def hit(self,x):return next((box for box in self.boxes if box[0]<=x<=box[1]),None)
    def hover(self,event):
        c=self.timeline;c.delete('hover');box=self.hit(c.canvasx(event.x));c.configure(cursor='')
        if not box:return
        x1,x2,b,s,e=box;x=c.canvasx(event.x)
        if min(abs(x-x1),abs(x-x2))<=5:c.configure(cursor='sb_h_double_arrow');return
        if b.preset and (x<x1+25 or x>x2-25):
            direction=-1 if x<x1+25 else 1;cx=x1+16 if direction<0 else x2-16
            c.create_polygon(cx+direction*9,50,cx-direction*2,42,cx-direction*2,47,cx-direction*9,47,cx-direction*9,53,cx-direction*2,53,cx-direction*2,58,fill='white',stipple='gray50',outline='',tags='hover')
    def press(self,event):
        x=self.timeline.canvasx(event.x);box=self.hit(x)
        if not box:
            self.model.selection.clear();self.model.selected_step=None;self.render();return
        x1,x2,b,s,e=box;self.select(s,bool(getattr(event,'state',0)&5));edge='left' if abs(x-x1)<=5 else 'right' if abs(x-x2)<=5 else None
        self.drag=(b.id,x,b.length,edge)
    def motion(self,event):
        if self.drag:
            self.timeline.delete('hover');x=self.timeline.canvasx(event.x);self.timeline.create_line(x,26,x,74,fill=TEXT,tags='hover')
    def release(self,event):
        self.timeline.delete('hover')
        if not self.drag:return
        id,x,length,edge=self.drag;self.drag=None;delta=round((self.timeline.canvasx(event.x)-x)/64)
        if delta:self.perform(lambda:self.model.resize(id,length+(-delta if edge=='left' else delta)) if edge else self.model.move(id,delta))
    def pad_click(self,event):
        for n,x,y,size in self.pad_boxes:
            if x<=event.x<=x+size and y<=event.y<=y+size:self.select_pad(n);return
    def render(self):
        c=self.timeline;c.delete('all');self.boxes=[];x=12
        for b,s,e in self.model.ranges():
            w=max(48,b.length*20) if b.preset is None else max(80,b.length*64);self.boxes.append((x,x+w,b,s,e))
            c.create_text(x+4,13,text=f'{s:02d}' if s==e else f'{s:02d}–{e:02d}',anchor='w',fill=TEXT,font=('Segoe UI',10))
            if b.preset is None:c.create_line(x+4,63,x+w-4,63,fill=EDGE,dash=(2,3));c.create_text(x+w/2,47,text='EMPTY',fill=MUTED,font=('Segoe UI',8))
            else:
                color=self.session.song.colors.get(b.preset,color_for(b.preset));c.create_rectangle(x+2,27,x+w-2,71,fill=color,outline=ORANGE if b.id in self.model.selection else EDGE,width=2 if b.id in self.model.selection else 1)
                c.create_text(x+w/2,49,text=self.label(b),width=w-16,fill=TEXT,font=('Segoe UI',10))
            if self.model.loop_range and s<=self.model.loop_range[1] and e>=self.model.loop_range[0]:c.create_line(x+2,77,x+w-2,77,fill=ORANGE,width=2)
            if self.model.playhead is not None and s<=self.model.playhead<=e:
                px=x+(self.model.playhead-s)*w/b.length;c.create_line(px,25,px,73,fill=TEXT,width=2)
            x+=w
        c.configure(scrollregion=(0,0,max(c.winfo_width(),x+100),82));self.render_grid()
        seconds=round(self.session.song.duration);self.metrics.set(f'DURATION   {seconds//60:02d}:{seconds%60:02d}\nSTEPS         {self.model.length} / 64\nBLOCKS      {sum(b.preset is not None for b in self.model.blocks)}')
        self.play_button.set('STOP' if self.session.active else 'PLAY',self.session.active)
        if self.session.pending_pad is not None:self.current.set(f'{self.session.pending_pad+1:02d} · {max(0,math.ceil(self.session.deadline-time.monotonic()))} s')
        elif self.session.playing_pad is not None:
            song=self.session.pads[self.session.playing_pad];self.current.set(f'{self.session.playing_pad+1:02d} · {song.name}\n{song.timeline.playhead:02d} / {song.timeline.length:02d}')
        else:self.current.set('')
        block=self.selected();self.context.set(f'{self.label(block)} · {block.length} steps' if block else '')
        px,py=c.winfo_pointerxy();px-=c.winfo_rootx();py-=c.winfo_rooty()
        if not self.drag and 0<=px<c.winfo_width() and 27<=py<=71:self.hover(SimpleNamespace(x=px))
    def render_grid(self):
        c=self.grid_canvas;c.delete('all');self.pad_boxes=[];side=max(80,min(c.winfo_width()-24,c.winfo_height()-12));pitch=side/8;size=pitch*.88;left=(c.winfo_width()-side)/2
        for i,song in enumerate(self.session.pads):
            x=left+(i%8)*pitch;y=6+(i//8)*pitch;self.pad_boxes.append((i,x,y,size));selected=i==self.session.selected;playing=i==self.session.playing_pad
            c.create_rectangle(x,y,x+size,y+size,fill=song.color if song.timeline.length else PANEL,outline=ORANGE if selected else EDGE,width=2 if selected else 1)
            if playing:c.create_rectangle(x+4,y+4,x+size-4,y+size-4,outline=TEXT,width=2)
            c.create_text(x+5,y+7,text=f'{i+1:02d}',anchor='nw',fill=MUTED,font=('Segoe UI',8))
            limit=max(2,int((size-8)/6));name=song.name;name=name if len(name)<=limit else name[:limit-1]+'…'
            c.create_text(x+size/2,y+size*.64,text=name,fill=TEXT,font=('Segoe UI',9))
