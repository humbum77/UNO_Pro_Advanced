"""UNO-themed editor for 64 songs. No MIDI or device writes."""
from pathlib import Path
import math,time,sys
import tkinter as tk
from tkinter import filedialog,font as tkfont
from live_creator.core.session import Session,Song,Transport,Loop,color_for
from live_creator.core.clipboard import Clipboard
from live_creator.core.paths import state_path as default_state_path
from live_creator.devices.uno.timing import sequence_beats
from live_creator.ui.popups import ObjectMenu,ColorPalette,MarkerPrompt,contrast
from live_creator.ui.layout import Slots,pulse,clipped,wrapped
from live_creator.core import state
from live_creator.devices.uno.library import PresetLibrary,children,default_root
from live_creator.ui.controls import Button,Dropdown,Scrollbar
from live_creator.ui.theme import BG,PANEL,PANEL2,EDGE,TEXT,MUTED,ORANGE

DELAY={'OFF':0,'5 s':5,'10 s':10,'15 s':15,'30 s':30,'45 s':45,'1 min':60}

class LiveCreator(tk.Tk):
    def __init__(self,state_path=None):
        super().__init__();self.title('Live Creator v0.6-alpha');self.geometry('1200x750');self.minsize(960,600);self.configure(bg=BG)
        self.small_font=tkfont.Font(family='Segoe UI',size=9);self.pad_font=tkfont.Font(family='Segoe UI',size=10)
        self.preview=None
        self.ghost=tk.Label(self,bg=PANEL2,fg=TEXT,highlightbackground=ORANGE,highlightthickness=1,font=('Segoe UI',9))
        self.state_path=Path(state_path) if state_path else default_state_path()
        self.session=Session();self.load_failed=False
        try:
            if self.state_path.exists():self.session=state.load(self.state_path)
        except Exception as error:self.load_failed=True;self.load_error=str(error)
        self.session.resolver=sequence_beats;self.clipboard=Clipboard();self.edit_context='song';self.popup=None;self.drag_position=None
        self.library=PresetLibrary();self.boxes=[];self.pad_boxes=[];self.source=None;self.drag=None;self.save_job=None;self.timer=None;self.syncing=False
        self.status=tk.StringVar(value='State load failed: '+self.load_error if self.load_failed else '')
        self.columnconfigure(1,weight=1);self.rowconfigure(1,weight=1)
        top=tk.Frame(self,bg=BG);top.grid(row=0,column=0,columnspan=3,sticky='ew',padx=12,pady=(12,8));top.columnconfigure(0,weight=1)
        self.timeline=tk.Canvas(top,height=172,bg=PANEL,highlightbackground=EDGE,highlightthickness=1);self.timeline.grid(row=0,column=0,sticky='ew')
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
        self.grid_canvas.bind('<Button-3>',self.song_menu)
        self.name=tk.StringVar();self.tempo=tk.StringVar();self.metrics=tk.StringVar();self.current=tk.StringVar()
        self.play_button=Button(self.work,'PLAY',self.toggle_play,width=222,height=38);self.play_button.pack(padx=16,pady=(16,12))
        delay_row=tk.Frame(self.work,bg=PANEL);delay_row.pack(fill='x',padx=16,pady=4)
        tk.Label(delay_row,text='PLAY DELAY',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
        self.delay=Dropdown(delay_row,list(DELAY),self.edit_delay);self.delay.configure(width=105);self.delay.pack(side='right')
        self.entry('NAME',self.name);self.entry('TEMPO',self.tempo)
        self.name.trace_add('write',self.edit_name)
        tk.Label(self.work,textvariable=self.metrics,bg=PANEL,fg=TEXT,justify='left',font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=10)
        tk.Label(self.work,text='MARKERS',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=16)
        marker_frame=tk.Frame(self.work,bg=PANEL);marker_frame.pack(fill='both',expand=True,padx=12,pady=4)
        self.marker_list=tk.Canvas(marker_frame,bg=PANEL,highlightthickness=0,height=65);self.marker_list.pack(side='left',fill='both',expand=True)
        marker_scroll=Scrollbar(marker_frame,self.marker_list.yview);marker_scroll.pack(side='right',fill='y');self.marker_list.configure(yscrollcommand=marker_scroll.set)
        marker_scroll.configure(height=1)
        self.marker_list.bind('<Button-1>',self.marker_click)
        self.error_label=tk.Label(self.work,textvariable=self.status,bg=PANEL,fg=ORANGE,wraplength=224,justify='left',font=('Segoe UI',10))
        self.status.trace_add('write',self.show_error);self.show_error()
        self.bind('<space>',self.space);self.protocol('WM_DELETE_WINDOW',self.close)
        for key,action in [('c','copy'),('x','cut'),('v','paste')]:self.bind('<Control-'+key+'>',lambda e,a=action:self.edit_action(a,e))
        self.bind('<Control-KeyPress>',self.clipboard_hotkey)
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
        e=tk.Entry(parent,textvariable=variable,width=3,bg=PANEL2,fg=TEXT,insertbackground=ORANGE,relief='flat',highlightthickness=1,highlightbackground=EDGE,highlightcolor=ORANGE,font=('Segoe UI',11));e.pack(**({'side':'left','padx':8} if label=='TEMPO' else {'fill':'x','padx':10}))
        if label=='NAME':self.name_entry=e;e.configure(justify='center')
        if label=='TEMPO':e.bind('<Return>',self.edit_tempo);e.bind('<FocusOut>',self.edit_tempo)
    def show_error(self,*args):
        if self.status.get():self.error_label.pack(anchor='w',padx=16,pady=6)
        else:self.error_label.pack_forget()
    def choose_color(self,context,x,y):
        color=self.session.song.color if context=='song' else self.block_color(self.selected())
        def apply(color):
            if context=='song':self.session.song.color=color
            else:self.model.set_color(self.model.selection,color)
            self.persist();self.render()
        self.popup=ColorPalette(self,color,apply,x,y)
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
        try:self.session.toggle(time.monotonic());self.status.set('');self.persist()
        except ValueError as error:self.status.set(str(error))
        self.render()
    def tick(self):
        was_active=self.session.active
        self.session.update(time.monotonic())
        if was_active:self.render()
        self.timer=self.after(50,self.tick)
    def selected(self):return next((b for b,s,e in self.model.ranges() if self.model.selected_step is not None and s<=self.model.selected_step<=e),None)
    def select(self,n,additive=False):self.edit_context='block';self.model.select(n,additive);self.render()
    def select_pad(self,n):
        self.drag=None;self.preview=None;self.edit_context='song';self.session.select_pad(n);self.grid_canvas.focus_set();self.sync_editor();self.persist();self.render()
    def loop_selection(self,event=None):self.perform(self.session.assign_loop);return 'break'
    def block_color(self,b):return b.color or self.session.song.colors.get(b.preset,color_for(b.preset)) if b and b.preset else PANEL
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
        if not(10<=x<=self.timeline.winfo_width()-10 and 0<=y<172):return None
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
        self.timeline.configure(cursor=('sb_h_double_arrow' if self.edge(box,event.x) else 'fleur') if box else '')
    def press(self,event):
        self.timeline.focus_set();box=self.hit(event.x,event.y)
        if not box:
            self.model.selection.clear();self.model.selected_step=None;self.render();return
        x1,y,x2,y2,b,s,e,start,end=box
        self.select(start,bool(getattr(event,'state',0)&5))
        self.drag=(b.id,self.geometry_slots().position(event.x,event.y),b.length,self.edge(box,event.x))
        self.drag_position=self.drag[1];self.render()
    def motion(self,event):
        if self.drag:
            self.drag_position=self.geometry_slots().position(event.x,event.y);self.render()
    def draw_drag(self):
        if not self.drag:return
        id,pos,length,edge=self.drag;delta=round(self.drag_position-pos)
        b,start,end=next((b,s,e) for b,s,e in self.model.ranges() if b.id==id)
        first=start if edge!='left' else start+delta
        last=end+delta if edge=='right' else end
        if not edge:first=start+delta;last=end+delta
        c=self.timeline;geom=self.geometry_slots();valid=1<=first<=last<=64
        # Geometry previews the same atomic operation, including the following ripple.
        from copy import deepcopy
        trial=deepcopy(self.model)
        try:
            if edge=='left':trial.resize_left(id,delta)
            elif edge:trial.resize(id,length+delta)
            else:trial.move(id,delta)
        except ValueError:valid=False
        color=ORANGE if valid else '#e36868'
        if edge:
            changed_start,changed_end=(min(start,first),max(start,first)-1) if edge=='left' else (min(end,last)+1,max(end,last))
            for x,y,x2,y2,s,e in geom.segments(max(1,changed_start),min(64,changed_end)):
                c.create_rectangle(x+1,y,x2-1,y2,fill=self.block_color(b),outline='',tags='drag')
        for x,y,x2,y2,s,e in geom.segments(max(1,first),min(64,last)):
            if edge:c.create_rectangle(x+1,y,x2-1,y2,outline=color,width=2,tags='drag')
            else:c.create_rectangle(x+1,y,x2-1,y2,fill=self.block_color(b),stipple='gray50',outline=color,width=2,tags='drag')
            if edge:
                boundary=first if edge=='left' else last
                if s<=boundary<=e:
                    bx=x if edge=='left' else x2;c.create_line(bx,y-4,bx,y2+4,fill=color,width=4,tags='drag')
            else:c.create_text(x+4,y+15,text=clipped(self.label(b),x2-x-8,self.small_font),anchor='w',fill=TEXT,font=self.small_font,tags='drag')
    def release(self,event):
        self.timeline.delete('drag')
        if not self.drag:return
        id,pos,length,edge=self.drag;self.drag=None
        delta=round(self.geometry_slots().position(event.x,event.y)-pos)
        if delta:self.perform(lambda:self.model.resize_left(id,delta) if edge=='left' else self.model.resize(id,length+delta) if edge else self.model.move(id,delta))
        else:self.render()
    def delete_blocks(self,event=None):
        return self.edit_action('delete',event)
    def edit_action(self,action,event=None):
        if event is not None and isinstance(self.focus_get(),(tk.Entry,tk.Text)):return
        self.drag=None;self.preview=None
        def apply():
            if self.edit_context=='song':
                if action in ('copy','cut'):self.clipboard.copy_song(self.session.song)
                if action in ('delete','cut'):self.session.pads[self.session.selected]=Song(self.session.selected)
                if action=='paste' and self.clipboard.kind=='song':self.session.pads[self.session.selected]=self.clipboard.paste_song()
                self.sync_editor()
            else:
                if action in ('copy','cut'):self.clipboard.copy_blocks(self.session.song)
                if action in ('delete','cut'):self.model.delete_selected()
                if action=='paste':
                    selected=self.selected();index=self.model.index(selected.id) if selected else len(self.model.blocks)
                    self.clipboard.paste_blocks(self.session.song,index)
        self.perform(apply);return 'break'
    def clipboard_hotkey(self,event):
        action={67:'copy',88:'cut',86:'paste'}.get(event.keycode) if sys.platform.startswith('win') else None
        action=action or {'c':'copy','x':'cut','v':'paste'}.get(event.keysym.lower())
        if action:return self.edit_action(action,event)
    def clipboard_items(self,kind,exists):
        return [('Cut',lambda:self.edit_action('cut'),exists,'Ctrl+X'),('Copy',lambda:self.edit_action('copy'),exists,'Ctrl+C'),('Paste',lambda:self.edit_action('paste'),self.clipboard.kind==kind,'Ctrl+V'),None,('Delete',lambda:self.edit_action('delete'),exists,'Del')]
    def block_menu(self,event):
        box=self.hit(event.x,event.y)
        if not box:return
        self.edit_context='block';self.timeline.focus_set()
        if box[4].id not in self.model.selection:self.select(box[7])
        step=box[7]
        items=[('Set Marker',lambda:self.marker_prompt(step,event.x_root,event.y_root),True,''),('Delete Marker',lambda:self.perform(lambda:self.model.markers.pop(step,None)),step in self.model.markers,''),None,('Color...',lambda:self.choose_color('block',event.x_root,event.y_root),True,''),None,('Loop',self.loop_selection,True,''),None]+self.clipboard_items('blocks',True)
        self.popup=ObjectMenu(self,items,event.x_root,event.y_root)
    def song_menu(self,event):
        self.pad_click(event)
        items=[('Color...',lambda:self.choose_color('song',event.x_root,event.y_root),True,''),None]+self.clipboard_items('song',bool(self.model.length))
        self.popup=ObjectMenu(self,items,event.x_root,event.y_root)
    def marker_prompt(self,step,x,y):
        self.popup=MarkerPrompt(self,self.model.markers.get(step,''),lambda text:self.perform(lambda:self.model.set_marker(step,text)),x,y)
    def marker_click(self,event):
        index=int(self.marker_list.canvasy(event.y)//22);steps=sorted(self.model.markers)
        if 0<=index<len(steps):self.select(steps[index]);self.timeline.focus_set()
    def pad_click(self,event):
        for n,x,y,size in self.pad_boxes:
            if x<=event.x<=x+size and y<=event.y<=y+size:self.select_pad(n);return
    def render(self):
        c=self.timeline;c.delete('all');self.boxes=[];geom=self.geometry_slots();now=time.monotonic()
        for row in range(2):
            for col in range(33):
                x=10+col*geom.pitch;y=row*86
                c.create_line(x,y+43,x,y+77,fill=EDGE if col%8==0 else PANEL2,tags='slot-grid')
                if col<32:c.create_text(x+geom.pitch/2,y+12,text=f'{row*32+col+1:02d}',fill=MUTED,font=('Segoe UI',8),tags='slot-number')
        for b,start,end in self.model.ranges():
            playing=self.session.playing_pad==self.session.selected and b.id==self.session.playing_block_id
            color=self.block_color(b)
            if playing:color=pulse(color,now)
            if self.drag and self.drag[0]==b.id and not self.drag[3]:color=PANEL2
            for x,y,x2,y2,s,e in geom.segments(start,end):
                self.boxes.append((x,y,x2,y2,b,s,e,start,end))
                c.create_rectangle(x+1,y,x2-1,y2,fill=color,outline=ORANGE if b.id in self.model.selection else EDGE,width=2 if b.id in self.model.selection else 1,tags=('block',b.id))
                label=self.label(b) if b.preset else ''
                label=('‹ ' if s>start else '')+label+(' ›' if e<end else '')
                c.create_text(x+4,(y+y2)/2,text=clipped(label,x2-x-8,self.small_font),anchor='w',fill='#101417' if playing else contrast(color),font=self.small_font,tags='block-name')
                if self.model.loop_range and s<=self.model.loop_range[1] and e>=self.model.loop_range[0]:
                    ls=max(s,self.model.loop_range[0]);le=min(e,self.model.loop_range[1])
                    active=self.session.playing_pad==self.session.selected and self.session.loop_state==Loop.ACTIVE
                    c.create_line(x+(ls-s)*geom.pitch,y2+4,x+(le-s+1)*geom.pitch,y2+4,fill=ORANGE,width=4 if active else 2,dash=() if active else (4,3),tags='loop')
        for step,end,text in self.model.sections():
            x,y=geom.point(step);next_on_row=min(end+1,((step-1)//32+1)*32+1)
            width=max(4,(next_on_row-step)*geom.pitch-14)
            c.create_line(x+2,y-17,x+2,y-2,fill=ORANGE,tags='marker')
            c.create_polygon(x+2,y-17,x+10,y-14,x+2,y-10,fill=ORANGE,tags='marker')
            c.create_text(x+13,y-12,text=clipped(text,width,self.small_font),anchor='w',fill=TEXT,font=self.small_font,tags='marker')
        self.render_grid();self.draw_preview();self.draw_drag()
        is_playback=self.session.playback is not None and self.session.playback_pad==self.session.selected
        duration=sum(self.session.durations) if is_playback and self.session.active else self.session.duration(self.session.song)
        elapsed=min(self.session.position,duration) if is_playback and duration is not None else 0
        def clock(value):
            if value is None:return '—'
            seconds=int(value);return f'{seconds//60:02d}:{seconds%60:02d}'
        self.metrics.set(f'DURATION     {clock(duration)}\nELAPSED        {clock(elapsed if duration is not None else None)}\nREMAINING   {clock(max(0,duration-elapsed) if duration is not None else None)}\n\nSTEPS             {self.model.length} / 64\nBLOCKS          {sum(b.preset is not None for b in self.model.blocks)}')
        text='STOP' if self.session.active else 'PLAY'
        if self.session.loop_state==Loop.ACTIVE:text='PLAY'
        if self.session.pending_pad is not None:text+=f' · {max(0,math.ceil(self.session.deadline-now))} s'
        self.play_button.set(text,self.session.active)
        self.name_entry.configure(bg=self.session.song.color,fg=contrast(self.session.song.color),insertbackground=contrast(self.session.song.color))
        self.marker_list.delete('all')
        for i,(step,label) in enumerate(sorted(self.model.markers.items())):
            self.marker_list.create_text(4,i*22+11,text=f'{step:02d}   '+clipped(label,165,self.small_font),anchor='w',fill=TEXT,font=self.small_font)
        self.marker_list.configure(scrollregion=(0,0,200,len(self.model.markers)*22))
    def render_grid(self):
        c=self.grid_canvas;c.delete('all');self.pad_boxes=[];side=max(80,min(c.winfo_width()-24,c.winfo_height()-12));pitch=side/8;size=pitch*.88;left=(c.winfo_width()-side)/2
        for i,song in enumerate(self.session.pads):
            x=left+(i%8)*pitch;y=6+(i//8)*pitch;self.pad_boxes.append((i,x,y,size));selected=i==self.session.selected;playing=i==self.session.playing_pad
            color=song.color if song.timeline.length else PANEL
            if playing:color=pulse(color,time.monotonic())
            c.create_rectangle(x,y,x+size,y+size,fill=color,outline=ORANGE if selected else EDGE,width=2 if selected else 1,tags=f'pad-{i}')
            if song.timeline.length:
                text=wrapped(song.name,size-10,max(1,int((size-12)/self.pad_font.metrics('linespace'))),self.pad_font)
                c.create_text(x+size/2,y+size/2-2,text=text,justify='center',fill='#101417' if playing else contrast(color),font=self.pad_font,tags=f'pad-label-{i}')
            else:c.create_text(x+size/2,y+size/2,text=f'{i+1:02d}',fill=MUTED,font=self.small_font,tags=f'pad-label-{i}')
