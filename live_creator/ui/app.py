"""UNO-themed editor for 64 songs. No MIDI or device writes."""
from pathlib import Path
import math,time
import tkinter as tk
from tkinter import filedialog,font as tkfont
from live_creator.core.session import Session,color_for,COLORS
from live_creator.ui.layout import Slots,pulse,clipped,wrapped
from live_creator.core import state
from live_creator.devices.uno.library import PresetLibrary,children,default_root
from live_creator.ui.controls import Button,Dropdown,Scrollbar
from live_creator.ui.theme import BG,PANEL,PANEL2,EDGE,TEXT,MUTED,ORANGE

DELAY={'OFF':0,'5 s':5,'10 s':10,'15 s':15,'30 s':30,'45 s':45,'1 min':60}

class LiveCreator(tk.Tk):
    def __init__(self,state_path=None):
        super().__init__();self.title('Live Creator v0.5-alpha');self.geometry('1200x750');self.minsize(960,600);self.configure(bg=BG)
        self.small_font=tkfont.Font(family='Segoe UI',size=9);self.pad_font=tkfont.Font(family='Segoe UI',size=10)
        self.preview=None
        self.ghost=tk.Label(self,bg=PANEL2,fg=TEXT,highlightbackground=ORANGE,highlightthickness=1,font=('Segoe UI',9))
        self.state_path=Path(state_path) if state_path else Path(__file__).resolve().parents[2]/'LiveCreatorState.json'
        self.session=Session();self.load_failed=False
        try:
            if self.state_path.exists():self.session=state.load(self.state_path)
        except Exception as error:self.load_failed=True;self.load_error=str(error)
        self.library=PresetLibrary();self.boxes=[];self.pad_boxes=[];self.source=None;self.drag=None;self.save_job=None;self.timer=None;self.syncing=False
        self.status=tk.StringVar(value='State load failed: '+self.load_error if self.load_failed else '')
        self.columnconfigure(1,weight=1);self.rowconfigure(1,weight=1)
        top=tk.Frame(self,bg=BG);top.grid(row=0,column=0,columnspan=3,sticky='ew',padx=12,pady=(12,8));top.columnconfigure(0,weight=1)
        self.timeline=tk.Canvas(top,height=132,bg=PANEL,highlightbackground=EDGE,highlightthickness=1);self.timeline.grid(row=0,column=0,sticky='ew')
        self.timeline.bind('<Configure>',lambda e:self.render())
        self.timeline.bind('<ButtonPress-1>',self.press);self.timeline.bind('<B1-Motion>',self.motion);self.timeline.bind('<ButtonRelease-1>',self.release)
        self.timeline.bind('<Motion>',self.hover);self.timeline.bind('<Shift-Button-3>',self.loop_selection)
        self.timeline.bind('<Button-3>',self.block_menu);self.bind('<Delete>',self.delete_blocks)
        self.left=self.panel(0);self.work=self.panel(2)
        self.left.rowconfigure(1,weight=1);self.left.columnconfigure(0,weight=1)
        self.browser_mode=Dropdown(self.left,['LOCAL PRESETS','HARDWARE PRESETS'],lambda v:self.populate());self.browser_mode.grid(row=0,column=0,sticky='ew',padx=8,pady=8)
        self.tree=tk.Canvas(self.left,bg=PANEL,highlightthickness=0);self.tree.grid(row=1,column=0,sticky='nsew')
        sb=Scrollbar(self.left,self.tree.yview);sb.grid(row=1,column=1,sticky='ns');self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind('<ButtonPress-1>',self.tree_press);self.tree.bind('<B1-Motion>',self.tree_motion);self.tree.bind('<ButtonRelease-1>',self.drop);self.tree.bind('<Button-3>',self.browser_menu)
        self.tree.bind('<MouseWheel>',lambda e:self.tree.yview_scroll(-int(e.delta/120),'units'))
        self.grid_canvas=tk.Canvas(self,bg=BG,highlightthickness=0);self.grid_canvas.grid(row=1,column=1,sticky='nsew',padx=6,pady=(0,12))
        self.grid_canvas.bind('<Configure>',lambda e:self.render_grid());self.grid_canvas.bind('<Button-1>',self.pad_click)
        self.name=tk.StringVar();self.tempo=tk.StringVar();self.metrics=tk.StringVar();self.current=tk.StringVar()
        self.play_button=Button(self.work,'PLAY',self.toggle_play,width=222,height=38);self.play_button.pack(padx=16,pady=(16,12))
        delay_row=tk.Frame(self.work,bg=PANEL);delay_row.pack(fill='x',padx=16,pady=4)
        tk.Label(delay_row,text='PLAY DELAY',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
        self.delay=Dropdown(delay_row,list(DELAY),self.edit_delay);self.delay.configure(width=105);self.delay.pack(side='right')
        self.entry('NAME',self.name);self.entry('TEMPO',self.tempo)
        self.name.trace_add('write',self.edit_name)
        tk.Label(self.work,textvariable=self.metrics,bg=PANEL,fg=TEXT,justify='left',font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=10)
        self.colors=tk.Canvas(self.work,height=28,bg=PANEL,highlightthickness=0);self.colors.pack(fill='x',padx=16,pady=8)
        self.colors.bind('<Button-1>',self.choose_color)
        self.error_label=tk.Label(self.work,textvariable=self.status,bg=PANEL,fg=ORANGE,wraplength=224,justify='left',font=('Segoe UI',10))
        self.status.trace_add('write',self.show_error);self.show_error()
        self.bind('<space>',self.space);self.protocol('WM_DELETE_WINDOW',self.close)
        self.root_folder=self.session.global_settings.get('library_root',str(default_root()));self.expanded=set();self.browser_selected=None
        self.populate();self.sync_editor();self.render();self.timer=self.after(50,self.tick)
    @property
    def model(self):return self.session.song.timeline
    def panel(self,column):
        p=tk.Frame(self,bg=PANEL,width=260,highlightbackground=EDGE,highlightthickness=1);p.grid(row=1,column=column,sticky='nsew',padx=(12,6) if column==0 else (6,12),pady=(0,12));p.grid_propagate(False);p.pack_propagate(False);return p
    def entry(self,label,variable):
        parent=self.work
        if label=='TEMPO':parent=tk.Frame(self.work,bg=PANEL);parent.pack(fill='x',padx=16,pady=12)
        tk.Label(parent,text=label,bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(**({'side':'left'} if label=='TEMPO' else {'anchor':'w','padx':16,'pady':(12,4)}))
        e=tk.Entry(parent,textvariable=variable,width=3,bg=PANEL2,fg=TEXT,insertbackground=ORANGE,relief='flat',highlightthickness=1,highlightbackground=EDGE,highlightcolor=ORANGE,font=('Segoe UI',11));e.pack(**({'side':'right'} if label=='TEMPO' else {'fill':'x','padx':16}))
        if label=='TEMPO':e.bind('<Return>',self.edit_tempo);e.bind('<FocusOut>',self.edit_tempo)
    def show_error(self,*args):
        if self.status.get():self.error_label.pack(anchor='w',padx=16,pady=6)
        else:self.error_label.pack_forget()
    def choose_color(self,event):
        index=int(event.x//32)
        if 0<=index<len(COLORS):self.session.song.color=COLORS[index];self.persist();self.render()
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
        self.drag=None;self.preview=None;self.session.select_pad(n);self.sync_editor();self.persist();self.render()
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
        number=0
        for i,(path,depth) in enumerate(self.browser_rows):
            y=14+i*27
            if path==self.browser_selected:self.tree.create_rectangle(4,y-12,238,y+12,fill='#8a4b12',outline=ORANGE)
            prefix=('▾ ' if path in self.expanded else '▸ ') if path.is_dir() else '  ';name=path.name if path.is_dir() else path.stem;limit=max(8,26-depth*2)
            if not path.is_dir():
                number+=1;self.tree.create_text(7,y,text=f'{number:03d}',anchor='w',fill=MUTED,font=('Segoe UI',9),tags='preset-number')
            text=prefix+name;available=max(10,230-(40+depth*14))
            self.tree.create_text(40+depth*14,y,text=clipped(text,available,self.small_font),anchor='w',fill=TEXT,font=self.small_font)
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
    def geometry_slots(self):return Slots(self.timeline.winfo_width())
    def target(self,x,y):
        if not(10<=x<=self.timeline.winfo_width()-10 and 0<=y<132):return None
        pos=self.geometry_slots().position(x,y);slot=min(64,int(pos))
        for i,(b,s,e) in enumerate(self.model.ranges()):
            if s<=slot<=e:
                near=round(pos)
                if near==s and abs(pos-s)<.22:return ('INSERT',i,s,None)
                if near==e+1 and abs(pos-(e+1))<.22:return ('INSERT',i+1,e+1,None)
                return ('REPLACE',i,s,b.id)
        return ('INSERT',len(self.model.blocks),slot,None)
    def tree_motion(self,event):
        if not self.source:return
        self.configure(cursor='hand2')
        self.ghost.configure(text=self.source.stem);self.ghost.place(x=max(0,min(self.winfo_width()-180,event.x_root-self.winfo_rootx()+12)),y=event.y_root-self.winfo_rooty()+12,width=170);self.ghost.lift()
        x=event.x_root-self.timeline.winfo_rootx();y=event.y_root-self.timeline.winfo_rooty()
        target=self.target(x,y);self.preview=(target,self.source.stem) if target else None
        self.draw_preview()
    def draw_preview(self):
        c=self.timeline;c.delete('preview')
        if not self.preview:return
        target,name=self.preview;mode,index,slot,id=target
        geom=self.geometry_slots();end=slot
        if id:
            b,s,end=next((b,s,e) for b,s,e in self.model.ranges() if b.id==id);slot=s
        for x,y,x2,y2,s,e in geom.segments(slot,min(64,end)):
            c.create_rectangle(x+1,y,x2-1,y2,fill=PANEL2,stipple='gray50',outline=ORANGE,width=2,tags='preview')
            if mode=='INSERT':c.create_line(x,y-4,x,y2+4,fill=ORANGE,width=3,tags='preview')
        x,y=geom.point(min(64,slot));text=clipped(mode+' · '+name,min(250,c.winfo_width()-20),self.small_font)
        width=self.small_font.measure(text)+12;x=min(x,c.winfo_width()-width-3)
        c.create_rectangle(x,y-24,x+width,y-6,fill=PANEL2,outline=ORANGE,tags='preview')
        c.create_text(x+6,y-15,text=text,anchor='w',fill=TEXT,font=self.small_font,tags='preview')
    def drop(self,event):
        self.ghost.place_forget()
        self.configure(cursor='');path=self.source;self.source=None;self.preview=None;self.timeline.delete('preview')
        if path is None:return
        if abs(event.x_root-self.drag_start[0])+abs(event.y_root-self.drag_start[1])<6:return
        target=self.target(event.x_root-self.timeline.winfo_rootx(),event.y_root-self.timeline.winfo_rooty())
        if not target:return
        mode,index,slot,id=target
        def action():
            preset=self.library.capture(path)
            if mode=='REPLACE':self.model.replace(id,preset)
            else:
                self.model.insert_at_slot(index,preset,slot)
            self.model.select(slot);self.session.song.colors.setdefault(preset,color_for(preset))
        self.perform(action)
    def hit(self,x,y):return next((box for box in self.boxes if box[0]<=x<=box[2] and box[1]<=y<=box[3]),None)
    def edge(self,box,x):
        x1,y,x2,y2,b,s,e,start,end=box
        if s==start and abs(x-x1)<=4:return 'left'
        if e==end and abs(x-x2)<=4:return 'right'
    def hover(self,event):
        box=self.hit(event.x,event.y)
        self.timeline.configure(cursor='sb_h_double_arrow' if box and self.edge(box,event.x) else '')
    def press(self,event):
        self.timeline.focus_set();box=self.hit(event.x,event.y)
        if not box:
            self.model.selection.clear();self.model.selected_step=None;self.render();return
        x1,y,x2,y2,b,s,e,start,end=box
        self.select(start,bool(getattr(event,'state',0)&5))
        self.drag=(b.id,self.geometry_slots().position(event.x,event.y),b.length,self.edge(box,event.x))
    def motion(self,event):
        if self.drag:
            self.timeline.delete('drag')
            slot=min(64,int(self.geometry_slots().position(event.x,event.y)));x,y=self.geometry_slots().point(slot)
            self.timeline.create_rectangle(x,y,x+self.geometry_slots().pitch,y+30,outline=ORANGE,width=2,tags='drag')
    def release(self,event):
        self.timeline.delete('drag')
        if not self.drag:return
        id,pos,length,edge=self.drag;self.drag=None
        delta=round(self.geometry_slots().position(event.x,event.y)-pos)
        if delta:self.perform(lambda:self.model.resize(id,length+(-delta if edge=='left' else delta)) if edge else self.model.move(id,delta))
    def delete_blocks(self,event=None):
        if isinstance(self.focus_get(),(tk.Entry,tk.Text)):return
        self.drag=None;self.preview=None;self.perform(self.model.delete_selected);return 'break'
    def block_menu(self,event):
        box=self.hit(event.x,event.y)
        if not box:return
        if box[4].id not in self.model.selection:self.select(box[7])
        menu=tk.Menu(self,tearoff=False,bg=PANEL2,fg=TEXT,activebackground='#8a4b12',activeforeground=TEXT)
        menu.add_command(label='Delete',command=lambda:self.perform(self.model.delete_selected))
        try:menu.tk_popup(event.x_root,event.y_root)
        finally:menu.grab_release()
    def pad_click(self,event):
        for n,x,y,size in self.pad_boxes:
            if x<=event.x<=x+size and y<=event.y<=y+size:self.select_pad(n);return
    def render(self):
        c=self.timeline;c.delete('all');self.boxes=[];geom=self.geometry_slots();now=time.monotonic()
        for row in range(2):
            for col in range(33):
                x=10+col*geom.pitch;y=row*66
                c.create_line(x,y+23,x,y+57,fill=EDGE if col%8==0 else PANEL2,tags='slot-grid')
                if col<32:c.create_text(x+geom.pitch/2,y+12,text=f'{row*32+col+1:02d}',fill=MUTED,font=('Segoe UI',8),tags='slot-number')
        for b,start,end in self.model.ranges():
            playing=self.session.playing_pad==self.session.selected and self.model.playing and self.model.playhead is not None and start<=self.model.playhead<=end
            color=self.session.song.colors.get(b.preset,color_for(b.preset)) if b.preset else PANEL
            if playing:color=pulse(color,now)
            for x,y,x2,y2,s,e in geom.segments(start,end):
                self.boxes.append((x,y,x2,y2,b,s,e,start,end))
                c.create_rectangle(x+1,y,x2-1,y2,fill=color,outline=ORANGE if b.id in self.model.selection else EDGE,width=2 if b.id in self.model.selection else 1,tags=('block',b.id))
                label=self.label(b) if b.preset else ''
                label=('‹ ' if s>start else '')+label+(' ›' if e<end else '')
                c.create_text(x+4,(y+y2)/2,text=clipped(label,x2-x-8,self.small_font),anchor='w',fill=TEXT if b.preset else MUTED,font=self.small_font,tags='block-name')
                if self.model.loop_range and s<=self.model.loop_range[1] and e>=self.model.loop_range[0]:
                    ls=max(s,self.model.loop_range[0]);le=min(e,self.model.loop_range[1])
                    c.create_line(x+(ls-s)*geom.pitch,y2+4,x+(le-s+1)*geom.pitch,y2+4,fill=ORANGE,width=2,tags='loop')
        self.render_grid();self.draw_preview()
        seconds=round(self.session.song.duration);self.metrics.set(f'DURATION   {seconds//60:02d}:{seconds%60:02d}\nSTEPS         {self.model.length} / 64\nBLOCKS      {sum(b.preset is not None for b in self.model.blocks)}')
        text='STOP' if self.session.active else 'PLAY'
        if self.session.pending_pad is not None:text+=f' · {max(0,math.ceil(self.session.deadline-now))} s'
        self.play_button.set(text,self.session.active)
        self.colors.delete('all')
        for i,color in enumerate(COLORS):self.colors.create_rectangle(i*32+2,3,i*32+26,25,fill=color,outline=ORANGE if color==self.session.song.color else EDGE,width=2)
    def render_grid(self):
        c=self.grid_canvas;c.delete('all');self.pad_boxes=[];side=max(80,min(c.winfo_width()-24,c.winfo_height()-12));pitch=side/8;size=pitch*.88;left=(c.winfo_width()-side)/2
        for i,song in enumerate(self.session.pads):
            x=left+(i%8)*pitch;y=6+(i//8)*pitch;self.pad_boxes.append((i,x,y,size));selected=i==self.session.selected;playing=i==self.session.playing_pad
            color=song.color if song.timeline.length else PANEL
            if playing:color=pulse(color,time.monotonic())
            c.create_rectangle(x,y,x+size,y+size,fill=color,outline=ORANGE if selected else EDGE,width=2 if selected else 1,tags=f'pad-{i}')
            if song.timeline.length:
                text=wrapped(song.name,size-10,max(1,int((size-12)/self.pad_font.metrics('linespace'))),self.pad_font)
                c.create_text(x+size/2,y+size/2-2,text=text,justify='center',fill=TEXT,font=self.pad_font,tags=f'pad-label-{i}')
            else:c.create_text(x+size/2,y+size/2,text=f'{i+1:02d}',fill=MUTED,font=self.small_font,tags=f'pad-label-{i}')
