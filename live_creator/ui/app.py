"""UNO-themed editor for 64 songs. No MIDI or device writes."""
from pathlib import Path
import colorsys,math,time,sys
from dataclasses import replace
import tkinter as tk
try:
    from PIL import Image,ImageDraw,ImageTk,ImageFilter
    PIL_OK=True
except Exception:
    PIL_OK=False
from tkinter import filedialog,font as tkfont
from live_creator.core.session import Session,Song,Transport,Loop,color_for
from live_creator.core.clipboard import Clipboard
from live_creator.core.paths import state_path as default_state_path
from live_creator.devices.uno.timing import sequence_beats
from live_creator.devices.uno.sequence_notes import read_sequence_notes
from live_creator.ui.popups import ObjectMenu,ColorPalette,MarkerPrompt,contrast
from live_creator.ui.layout import Slots,pulse,clipped,wrapped
from live_creator.core import state
from live_creator.devices.uno.library import PresetLibrary,children,default_root
from live_creator.devices.uno.metadata import tags_for,favorite_for,order_for,TAG_COLORS,TAG_NAMES
from live_creator.devices.uno.hardware import HardwareReader,pages_have_sequence
from live_creator.devices.uno.catalog_cache import load_names as load_hardware_names,save_names as save_hardware_names
from live_creator.ui.controls import Button,TransportButton,Dropdown,Scrollbar
from live_creator.ui.theme import BG,PANEL,PANEL2,EDGE,TEXT,MUTED,ORANGE
from live_creator import __version__
import ui_theme

DELAY={'OFF':0,'5 s':5,'10 s':10,'15 s':15,'30 s':30,'45 s':45,'1 min':60}

class LiveCreator(tk.Frame):
    def __init__(self,state_path=None,master=None,midi_engine=None,live_event_callback=None):
        self.standalone=master is None
        if master is None:master=tk.Tk();master.title(f'UnoLive Creator v{__version__}');master.geometry('1200x750');master.minsize(960,600)
        super().__init__(master,bg=BG)
        if self.standalone:self.pack(fill='both',expand=True)
        self.small_font=tkfont.Font(family='Segoe UI',size=9);self.pad_font=tkfont.Font(family='Segoe UI',size=10)
        self.preview=None
        self.ghost=tk.Label(self,bg=PANEL2,fg=TEXT,highlightbackground=ORANGE,highlightthickness=1,font=('Segoe UI',9))
        self.state_path=Path(state_path) if state_path else default_state_path()
        self.session=Session();self.load_failed=False
        try:
            if self.state_path.exists():self.session=state.load(self.state_path)
        except Exception as error:self.load_failed=True;self.load_error=str(error)
        self.session.resolver=self._sequence_beats_for;self.clipboard=Clipboard();self.edit_context='song';self.popup=None;self.drag_position=None
        self.library=PresetLibrary();self.boxes=[];self.pad_boxes=[];self.source=None;self.drag=None;self.save_job=None;self.timer=None;self.syncing=False;self.sequence_notes_cache={};self._clip_images=[];self._playback_notes=set();self._playback_note_key=None;self._playback_preset_key=None;self.playback_midi=midi_engine;self.live_mode=False;self._play_button_active=False;self.live_event_callback=live_event_callback
        self.sequence_filter=False;self.tag_filters=set();self.favorite_filter=False;self.timeline_zoom=1.0;self.hardware_names=load_hardware_names();self.hardware_sequence_status={};self.hardware_pages={};self.hardware_selected=1;self._catalog_slot=1;self._catalog_timeout=None;self._catalog_queue=[];self._catalog_seen=set();self._catalog_retry=0;self._catalog_refresh=None;self._catalog_save=None;self._scan_timeout=None;self._scan_target=None;self._scan_retries=0;self._clip_surface_cache={};self._pad_surface_cache={};self._marker_image_cache={}
        self._restore_hardware_snapshots()
        self.hardware=HardwareReader(self._hardware_event)
        self.status=tk.StringVar(value='State load failed: '+self.load_error if self.load_failed else '')
        self.columnconfigure(1,weight=1);self.rowconfigure(1,weight=1)
        top=tk.Frame(self,bg=BG);top.grid(row=0,column=0,columnspan=3,sticky='ew',padx=12,pady=(12,8));top.columnconfigure(0,weight=1)
        self.timeline=tk.Canvas(top,height=100,bg=PANEL,highlightbackground=EDGE,highlightthickness=1);self.timeline.grid(row=0,column=0,sticky='ew')
        self.timeline_scroll=Scrollbar(top,self.timeline.xview,True);self.timeline_scroll.grid(row=1,column=0,sticky='ew',pady=(3,0));self.timeline.configure(xscrollcommand=self.timeline_scroll.set)
        self.timeline.bind('<Configure>',lambda e:self.render())
        self.timeline.bind('<ButtonPress-1>',self.press);self.timeline.bind('<B1-Motion>',self.motion);self.timeline.bind('<ButtonRelease-1>',self.release)
        self.timeline.bind('<Motion>',self.hover);self.timeline.bind('<Shift-Button-3>',self.loop_selection)
        self.timeline.bind('<Shift-MouseWheel>',lambda e:self.timeline.xview_scroll(-int(e.delta/120),'units'))
        self.timeline.bind('<Control-MouseWheel>',self.timeline_zoom_wheel)
        self.timeline.bind('<Control-Button-4>',lambda e:self.timeline_zoom_step(e,1))
        self.timeline.bind('<Control-Button-5>',lambda e:self.timeline_zoom_step(e,-1))
        self.timeline.bind('<Button-3>',self.block_menu);self.bind('<Delete>',self.delete_blocks)
        self.left=self.panel(0);self.work=self.panel(2)
        self.left.rowconfigure(1,weight=1);self.left.columnconfigure(0,weight=1)
        filter_row=tk.Frame(self.left,bg=PANEL);filter_row.grid(row=0,column=0,columnspan=2,sticky='ew',padx=8,pady=(8,2));filter_row.columnconfigure(1,weight=1)
        self.sequence_button=tk.Canvas(filter_row,width=62,height=30,bg=PANEL,highlightthickness=0,cursor='hand2');self.sequence_button.grid(row=0,column=0,sticky='w');self.sequence_button.bind('<Button-1>',lambda e:self.toggle_sequence_filter());self.sequence_button.bind('<Configure>',lambda e:self.draw_sequence_button())
        self.tags_canvas=tk.Canvas(filter_row,width=174,height=30,bg=PANEL,highlightthickness=0,cursor='hand2');self.tags_canvas.grid(row=0,column=1,sticky='e',padx=(6,0));self.tags_canvas.bind('<Button-1>',self.tag_tool_click);self.tags_canvas.bind('<Configure>',lambda e:self.draw_tag_tools())
        self.tree=tk.Canvas(self.left,bg=PANEL,highlightthickness=0);self.tree.grid(row=1,column=0,sticky='nsew')
        sb=Scrollbar(self.left,self.tree.yview);sb.grid(row=1,column=1,sticky='ns');self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind('<ButtonPress-1>',self.tree_press);self.tree.bind('<B1-Motion>',self.tree_motion);self.tree.bind('<ButtonRelease-1>',self.drop);self.tree.bind('<Button-3>',self.browser_menu)
        self.tree.bind('<MouseWheel>',lambda e:self.tree.yview_scroll(-int(e.delta/120),'units'))
        self.grid_canvas=tk.Canvas(self,bg=BG,highlightthickness=0);self.grid_canvas.grid(row=1,column=1,sticky='nsew',padx=6,pady=(0,12))
        self.grid_canvas.bind('<Configure>',lambda e:self.render_grid());self.grid_canvas.bind('<Button-1>',self.pad_click)
        self.grid_canvas.bind('<Button-3>',self.song_menu)
        self.name=tk.StringVar();self.tempo=tk.StringVar();self.song_length=tk.StringVar();self.metrics=tk.StringVar();self.current=tk.StringVar()
        self._length_palette=None;self.entry('NAME',self.name);self.entry('TEMPO',self.tempo)
        self.name.trace_add('write',self.edit_name)
        tk.Label(self.work,textvariable=self.metrics,bg=PANEL,fg=TEXT,justify='left',font=('Segoe UI',10)).pack(anchor='w',padx=16,pady=10)
        tk.Label(self.work,text='MARKERS',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=16)
        marker_frame=tk.Frame(self.work,bg=PANEL);marker_frame.pack(fill='both',expand=True,padx=12,pady=4)
        self.marker_list=tk.Canvas(marker_frame,bg=PANEL,highlightthickness=0,height=65);self.marker_list.pack(side='left',fill='both',expand=True)
        marker_scroll=Scrollbar(marker_frame,self.marker_list.yview);marker_scroll.pack(side='right',fill='y');self.marker_list.configure(yscrollcommand=marker_scroll.set)
        marker_scroll.configure(height=1)
        self.marker_list.bind('<Button-1>',self.marker_click)
        transport_row=tk.Frame(self.work,bg=PANEL);transport_row.pack(fill='x',padx=16,pady=(8,4))
        self.play_button=TransportButton(transport_row,'PLAY',self.toggle_play,width=105,height=48,label_color='#6fd34f');self.play_button.pack(side='left',fill='x',expand=True,padx=(0,4))
        self.stop_button=TransportButton(transport_row,'STOP',self.stop_playback,width=105,height=48,label_color='#e5c64a');self.stop_button.pack(side='left',fill='x',expand=True,padx=(4,0))
        delay_row=tk.Frame(self.work,bg=PANEL);delay_row.pack(fill='x',padx=16,pady=(4,10))
        tk.Label(delay_row,text='PLAY DELAY',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
        self.delay=Dropdown(delay_row,list(DELAY),self.edit_delay);self.delay.configure(width=105);self.delay.pack(side='right')
        self._last_error_popup=''
        self.status.trace_add('write',self.show_error);self.show_error()
        self.bind('<space>',self.space)
        if self.standalone:self.winfo_toplevel().protocol('WM_DELETE_WINDOW',self.close)
        for key,action in [('c','copy'),('x','cut'),('v','paste')]:self.bind('<Control-'+key+'>',lambda e,a=action:self.edit_action(a,e))
        self.bind('<Control-KeyPress>',self.clipboard_hotkey)
        self.root_folder=self.session.global_settings.get('library_root',str(default_root()));self.expanded=set();self.browser_selected=None
        self.populate();self.sync_editor();self.render();self.draw_sequence_button();self.draw_tag_tools();self.timer=self.after(50,self.tick)
        self.after(120,self._connect_hardware)
        for sequence,callback in [('<space>',self.space),('<Delete>',self.delete_blocks),('<Control-KeyPress>',self.clipboard_hotkey)]:
            self.winfo_toplevel().bind(sequence,lambda e,cb=callback:cb(e) if self.winfo_ismapped() and str(self.focus_get()).startswith(str(self)) else None,add='+')
    def geometry(self,*args):return self.winfo_toplevel().geometry(*args)
    def withdraw(self):return self.winfo_toplevel().withdraw()
    def apply_theme(self):
        import live_creator.ui.controls as controls
        import live_creator.ui.popups as popups
        mapping={'BG':'background','PANEL':'panel','PANEL2':'control','EDGE':'border','TEXT':'text','MUTED':'muted','ORANGE':'primary','ORANGE2':'primary_active'}
        for name,key in mapping.items():
            value=ui_theme.TOKENS[ui_theme.current][key]
            globals()[name]=value;setattr(controls,name,value);setattr(popups,name,value)
        self.populate();self.render()
    @property
    def model(self):return self.session.song.timeline
    def panel(self,column):
        p=tk.Frame(self,bg=PANEL,width=260,highlightbackground=EDGE,highlightthickness=1);p.grid(row=1,column=column,sticky='nsew',padx=(12,6) if column==0 else (6,12),pady=(0,12));p.grid_propagate(False);p.pack_propagate(False);return p
    def entry(self,label,variable):
        parent=self.work
        if label=='NAME':
            # Song title is the header of the right panel: full width, no top/side margins.
            canvas=tk.Canvas(self.work,height=64,bg=PANEL,highlightthickness=0)
            canvas.pack(fill='x',padx=0,pady=(0,8))
            self.name_gradient=canvas
            e=tk.Entry(canvas,textvariable=variable,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',highlightthickness=0,bd=0,font=('Segoe UI Semibold',13),justify='center')
            self.name_entry=e;self.name_entry_window=None
            canvas.bind('<Configure>',lambda ev:self._draw_name_gradient())
            canvas.bind('<Button-1>',self._begin_name_edit)
            e.bind('<Return>',self._finish_name_edit)
            e.bind('<Escape>',self._finish_name_edit)
            e.bind('<FocusOut>',self._finish_name_edit)
            return
        if label=='TEMPO':parent=tk.Frame(self.work,bg=PANEL);parent.pack(fill='x',padx=16,pady=12)
        if label!='NAME':tk.Label(parent,text=label,bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(**({'side':'left'} if label=='TEMPO' else {'anchor':'w','padx':16,'pady':(12,4)}))
        e=tk.Entry(parent,textvariable=variable,width=5,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',highlightthickness=1,highlightbackground=EDGE,highlightcolor=ORANGE,font=('Segoe UI',11),justify='center');e.pack(**({'side':'left','padx':8} if label=='TEMPO' else {'fill':'x','padx':0,'pady':(12,2),'ipady':6}))
        if label=='TEMPO':
            self.tempo_entry=e
            # LIVE tempo: direct numeric entry (Enter/focus-out) plus Ctrl+wheel.
            e.bind('<Return>',self.edit_tempo);e.bind('<FocusOut>',self.edit_tempo)
            e.bind('<Control-MouseWheel>',self.tempo_wheel)
            e.bind('<Control-Button-4>',lambda ev:self.tempo_wheel(ev,1))
            e.bind('<Control-Button-5>',lambda ev:self.tempo_wheel(ev,-1))
            tk.Label(parent,text='LENGTH',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
            self.length_button=Button(parent,self.song_length.get() or '64',self.open_length_palette,width=48,height=28);self.length_button.pack(side='left',padx=4)
    def _begin_name_edit(self,event=None):
        if not hasattr(self,'name_gradient') or not hasattr(self,'name_entry'):return
        c=self.name_gradient
        c.update_idletasks()
        w=max(2,c.winfo_width());h=max(2,c.winfo_height())
        # Tk Entry cannot be transparent. Show it only while the user is editing;
        # the normal header remains pure Canvas so the song-colour gradient stays visible.
        if self.name_entry_window is not None:
            try:c.delete(self.name_entry_window)
            except Exception:pass
        base=self.session.song.color or PANEL2
        edit_bg=self._mix(base,'#ffffff',.46)
        edit_rgb=[int(edit_bg[i:i+2],16) for i in (1,3,5)]
        edit_lum=.2126*edit_rgb[0]+.7152*edit_rgb[1]+.0722*edit_rgb[2]
        edit_fg=self._shade(base,.34) if edit_lum>=150 else self._mix(base,'#ffffff',.84)
        self.name_entry.configure(bg=edit_bg,fg=edit_fg,insertbackground=edit_fg,font=('Segoe UI Semibold',13),justify='center')
        self.name_entry_window=c.create_window(w/2,h/2,anchor='center',window=self.name_entry,width=max(20,w-36),height=30)
        self.name_entry.focus_set();self.name_entry.icursor('end');self.name_entry.selection_range(0,'end')
        return 'break'
    def _finish_name_edit(self,event=None):
        if hasattr(self,'name_gradient') and self.name_entry_window is not None:
            try:self.name_gradient.delete(self.name_entry_window)
            except Exception:pass
            self.name_entry_window=None
        self._draw_name_gradient()
        return 'break' if event is not None and getattr(event,'keysym','') in ('Return','Escape') else None
    def _draw_name_gradient(self):
        if not hasattr(self,'name_gradient'):return
        c=self.name_gradient;w=max(2,c.winfo_width());h=max(2,c.winfo_height())
        editing=self.name_entry_window is not None and self.name_entry.focus_get()==self.name_entry
        c.delete('all');self.name_entry_window=None
        base=self.session.song.color or PANEL2
        # Full-width song-colour header: solid selected song/pad colour.
        c.create_rectangle(0,0,w,h,fill=base,outline='')
        # Square/straight bottom edge across the full panel width.
        c.create_line(0,h-1,w,h-1,fill=self._shade(base,.42),width=1)
        sample=self._mix(base,'#ffffff',.24)
        # Softer colour-related contrast instead of hard black/white.
        rgb=[int(sample[i:i+2],16) for i in (1,3,5)]
        lum=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
        title_fg=self._shade(base,.34) if lum>=150 else self._mix(base,'#ffffff',.84)
        c.create_text(w/2,h/2,text=self.name.get(),anchor='center',
                      fill=title_fg,font=('Segoe UI Semibold',13),tags='song-title')
        c.tag_bind('song-title','<Button-1>',self._begin_name_edit)
        if editing:self.after_idle(self._begin_name_edit)
    def open_length_palette(self):
        # 8x8 numeric palette matching ColorPalette, but in a smaller footprint.
        if self._length_palette is not None:
            try:self._length_palette.destroy()
            except Exception:pass
            self._length_palette=None;return
        cell_w,cell_h=20,16;cols=8;rows=8;ww=cols*cell_w+2;wh=rows*cell_h+2
        win=tk.Toplevel(self);self._length_palette=win;win.withdraw();win.overrideredirect(True);win.configure(bg=EDGE);win.resizable(False,False);win.transient(self.winfo_toplevel())
        try:win.attributes('-topmost',True)
        except Exception:pass
        c=tk.Canvas(win,width=ww-2,height=wh-2,bg=PANEL2,highlightthickness=1,highlightbackground=EDGE);c.pack();cur=int(self.session.song.length)
        for i in range(64):
            n=i+1;r=i//8;col=i%8;x=1+col*cell_w;y=1+r*cell_h;sel=n<=cur
            c.create_rectangle(x+2,y+2,x+cell_w-2,y+cell_h-2,fill=(ORANGE if sel else PANEL2),outline=(ORANGE if sel else EDGE),width=1)
            c.create_text(x+cell_w/2,y+cell_h/2,text=str(n),fill=('#0d1114' if sel else TEXT),font=('Segoe UI',7))
        def pick(ev):
            col=int((ev.x-1)//cell_w);row=int((ev.y-1)//cell_h)
            if 0<=col<8 and 0<=row<8:self.choose_length(row*8+col+1,win)
        c.bind('<Button-1>',pick);win.update_idletasks()
        try:
            panel_left=self.work.winfo_rootx()+2;panel_right=self.work.winfo_rootx()+self.work.winfo_width()-2
            x=self.length_button.winfo_rootx()+self.length_button.winfo_width()-ww
            x=max(panel_left,min(x,panel_right-ww));y=self.length_button.winfo_rooty()+self.length_button.winfo_height()+4
        except Exception:x=self.winfo_pointerx();y=self.winfo_pointery()
        sw,sh=win.winfo_screenwidth(),win.winfo_screenheight();x=max(0,min(int(x),sw-ww));y=max(0,min(int(y),sh-wh));win.geometry(f'{ww}x{wh}+{x}+{y}');win.deiconify();win.lift();win.grab_set();win.focus_force()
        def close(event=None):
            try:win.destroy()
            except Exception:pass
            if self._length_palette is win:self._length_palette=None
        win.bind('<Escape>',close);win.bind('<Destroy>',lambda e:setattr(self,'_length_palette',None) if self._length_palette is win else None)
    def choose_length(self,n,win=None):
        self.session.song.set_length(n);self.song_length.set(str(n));self.length_button.set(str(n),False);self.status.set('');self.persist();self.render()
        if win:
            try:win.destroy()
            except Exception:pass
            if self._length_palette is win:self._length_palette=None
    def edit_length(self,event=None):
        try:self.session.song.set_length(self.song_length.get());self.status.set('');self.persist()
        except ValueError as error:self.status.set(str(error))
        self.song_length.set(str(self.session.song.length));self.render()
    def show_error(self,*args):
        msg=self.status.get().strip()
        if not msg:return
        low=msg.lower()
        # Informational connection messages must not open warnings.
        if low.startswith('connected') or low.startswith('hardware'):return
        if msg==getattr(self,'_last_error_popup',''):return
        self._last_error_popup=msg
        try:
            from tkinter import messagebox
            messagebox.showwarning('LIVE',msg,parent=self.winfo_toplevel())
        except Exception:pass
    def choose_color(self,context,x,y):
        color=self.session.song.color if context=='song' else self.block_color(self.selected())
        def apply(color):
            if context=='song':self.session.song.color=color
            else:self.model.set_color(self.model.selection,color)
            self.persist();self.render()
        self.popup=ColorPalette(self,color,apply,x,y)
    def sync_editor(self):
        self.syncing=True;self.name.set(self.session.song.name);self.tempo.set(str(self.model.tempo));self.song_length.set(str(self.session.song.length));value=next(k for k,v in DELAY.items() if v==self.session.song.delay);self.delay.choice=value;self.delay.set(value+'  ▾');self.syncing=False
        if hasattr(self,'length_button'):self.length_button.set(str(self.session.song.length),False)
    def edit_name(self,*args):
        if self.syncing:return
        self.session.song.name=self.name.get()[:256];self.persist();self.render_grid()
    def edit_tempo(self,event=None):
        if self.syncing:return
        try:self.model.set_tempo(self.tempo.get());self.status.set('');self.persist()
        except ValueError as error:self.status.set(str(error));self.tempo.set(str(self.model.tempo))
        self.render()
    def tempo_wheel(self,event,direction=None):
        if direction is None:
            direction=1 if getattr(event,'delta',0)>0 else -1
        try:value=int(self.tempo.get())
        except Exception:value=int(self.model.tempo)
        value=max(20,min(300,value+int(direction)))
        self.tempo.set(str(value));self.edit_tempo();return 'break'
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
        self._playback_all_notes_off()
        if self.timer:self.after_cancel(self.timer)
        if self.save_job:self.after_cancel(self.save_job)
        self.flush()
        if self.standalone:self.winfo_toplevel().destroy()
        else:self.destroy()
    def space(self,event):
        if isinstance(self.focus_get(),(tk.Entry,tk.Text)):return
        self.toggle_play();return 'break'
    def toggle_play(self):
        was_active=self.session.active
        try:self.session.toggle(time.monotonic());self.status.set('');self.persist()
        except ValueError as error:self.status.set(str(error))
        if was_active and not self.session.active:
            self._play_button_active=False
            self.live_mode=False;self._playback_all_notes_off()
            if self.live_event_callback:self.live_event_callback('STOP',None)
        elif not was_active and self.session.active:
            self._play_button_active=True
            self.live_mode=True
            if self.live_event_callback:self.live_event_callback('PLAY',self.session.selected)
            self._playback_preset_key=None;self._playback_prepare_current_preset()
        self.render()
    def live_stop(self):
        self._play_button_active=False
        self.live_mode=False
        self.stop_playback()
        if self.live_event_callback:self.live_event_callback('STOP',None)
    def launch_pad(self,n):
        n=int(n)
        if not 0<=n<64:return False
        self.drag=None;self.preview=None;self.edit_context='song'
        if self.session.active:
            self._playback_all_notes_off();self._playback_preset_key=None;self.session.stop()
        self.session.select_pad(n);self.grid_canvas.focus_set();self.sync_editor()
        if self.live_mode:
            try:self.session.toggle(time.monotonic());self.status.set('')
            except ValueError as error:self.status.set(str(error));self.persist();self.render();return False
            self._playback_prepare_current_preset()
        self.persist();self.render()
        if self.live_event_callback:self.live_event_callback('PAD',n)
        return True
    def _playback_all_notes_off(self):
        midi=self.playback_midi
        out=getattr(self.hardware,'out',None)
        for note in tuple(self._playback_notes):
            try:
                if midi is not None:midi.note_off(note)
                elif out:out.send_note_off(note,0,0)
            except Exception:pass
        self._playback_notes.clear();self._playback_note_key=None
    def _playback_prepare_current_preset(self,block=None):
        if self.session.playback is None:return False
        if block is None:
            step=self.session.current_step or 1
            block=next((b for b,start,end in self.session.playback.timeline.ranges() if start<=step<=end),None)
        if block is None or not block.preset:return False
        reference=str(block.preset)
        if reference==self._playback_preset_key:return True
        self._playback_all_notes_off();midi=self.playback_midi
        if midi is None:return False
        try:
            slot=self._hardware_slot(reference)
            if slot is not None:
                if not midi.bank_program(slot):raise RuntimeError('UNO MIDI OUT is not connected')
            else:
                from local_store_source import build_current_buffer_load
                if not midi.sysex(build_current_buffer_load(reference)):raise RuntimeError('UNO MIDI OUT is not connected')
            self._playback_preset_key=reference;return True
        except Exception as error:
            self.status.set('Preset load error: '+str(error));return False
    def _playback_midi_tick(self):
        if self.session.transport!=Transport.PLAYING or self.session.playback is None:
            self._playback_all_notes_off();return
        step=self.session.current_step
        if step is None or not 1<=step<=len(self.session.durations):
            self._playback_all_notes_off();return
        block=next((b for b,start,end in self.session.playback.timeline.ranges() if start<=step<=end),None)
        if block is None or not block.preset:
            self._playback_all_notes_off();return
        if not self._playback_prepare_current_preset(block):return
        sequence=self._notes_for(block.preset)
        slot=self._hardware_slot(block.preset)
        if slot is not None and sequence:
            try:
                from live_creator.devices.uno.timing import decode_hardware_sequence_length
                confirmed=decode_hardware_sequence_length(self.hardware_pages.get(slot,{}).get(0,b''))
                if confirmed:sequence=sequence[:confirmed]
            except Exception:pass
        if not sequence:
            self._playback_all_notes_off();return
        slot_start=sum(self.session.durations[:step-1]);slot_duration=self.session.durations[step-1]
        if slot_duration<=0:return
        within=max(0.0,min(slot_duration-1e-9,self.session.position-slot_start))
        seq_step=min(len(sequence)-1,int((within/slot_duration)*len(sequence)))
        key=(self.session.playback_pad,step,block.id,seq_step)
        if key==self._playback_note_key:return
        self._playback_all_notes_off();self._playback_note_key=key
        midi=self.playback_midi
        out=getattr(self.hardware,'out',None)
        if midi is None and not out:return
        for note in sequence[seq_step]:
            try:
                note=int(note)
                if midi is not None:
                    if not midi.note_on(note,100):raise RuntimeError('MIDI OUT is not connected')
                else:out.send_note(note,100,0)
                self._playback_notes.add(note)
            except Exception as error:
                self.status.set('MIDI playback error: '+str(error));break
    def stop_playback(self):
        self._play_button_active=False
        # STOP must always leave performance LIVE mode so pads/clips return to edit/select behaviour.
        self.live_mode=False
        self._playback_all_notes_off();self._playback_preset_key=None;self.session.stop();self.status.set('');self.persist();self.render()
    def tick(self):
        was_active=self.session.active
        self.session.update(time.monotonic());self._playback_midi_tick()
        if was_active and not self.session.active:
            self._play_button_active=False;self._playback_preset_key=None
        if was_active:self.render()
        self.timer=self.after(20,self.tick)
    def selected(self):return next((b for b,s,e in self.model.ranges() if self.model.selected_step is not None and s<=self.model.selected_step<=e),None)
    def select(self,n,additive=False):self.edit_context='block';self.model.select(n,additive);self.render()
    def select_pad(self,n):
        if self.live_mode:return self.launch_pad(n)
        self.drag=None;self.preview=None;self.edit_context='song';self.session.select_pad(n);self.grid_canvas.focus_set();self.sync_editor();self.persist();self.render()
    def loop_selection(self,event=None):self.perform(self.session.assign_loop);return 'break'
    def block_color(self,b):return b.color or self.session.song.colors.get(b.preset,color_for(b.preset)) if b and b.preset else PANEL
    def label(self,b):return self.library.label(b.preset) if b.preset else 'EMPTY'
    def perform(self,action):
        try:action();self.status.set('');self.persist()
        except (ValueError,OSError) as error:self.status.set(str(error))
        self.render()
    def draw_sequence_button(self):
        c=self.sequence_button;c.delete('all');w=max(40,c.winfo_width()-1);h=max(24,c.winfo_height()-1)
        edge='#ff8c18';bar='#ff8c18'
        self.round_block(c,1,1,w-1,h-1,fill=PANEL2,outline=edge,width=2 if self.sequence_filter else 1)
        heights=(8,15,11,19,9,16,7,13);bw=4;gap=2;total=len(heights)*bw+(len(heights)-1)*gap;left=(w-total)/2
        for i,bh in enumerate(heights):c.create_rectangle(left+i*(bw+gap),h-6-bh,left+i*(bw+gap)+bw,h-6,fill=bar,outline='')
    def toggle_sequence_filter(self):
        self.sequence_filter=not self.sequence_filter;self.draw_sequence_button();self.populate()
        if self.sequence_filter:self._start_hardware_sequence_scan()
    def draw_tag_tools(self):
        c=self.tags_canvas;c.delete('all');h=max(24,c.winfo_height()-1);x=2
        c.create_text(x+12,h/2,text='★',fill='#ffd84a' if self.favorite_filter else '#9aa2a7',font=('Segoe UI Symbol',13,'bold'));x+=29
        self._tag_images=[]
        for i,col in enumerate(TAG_COLORS):
            active=i in self.tag_filters;cx=x+8;radius=5
            if PIL_OK:
                try:
                    ss=4;d=radius*2;img=Image.new('RGBA',(d*ss,d*ss),(0,0,0,0));dr=ImageDraw.Draw(img);ow=ss
                    dr.ellipse((ow//2,ow//2,d*ss-1-ow//2,d*ss-1-ow//2),fill=col,outline='#c9ced1' if active else EDGE,width=ow)
                    img=img.resize((d,d),Image.Resampling.LANCZOS);ph=ImageTk.PhotoImage(img);self._tag_images.append(ph);c.create_image(cx,h/2,image=ph,anchor='center')
                except Exception:c.create_oval(cx-radius,h/2-radius,cx+radius,h/2+radius,fill=col,outline='#c9ced1' if active else EDGE,width=1)
            else:c.create_oval(cx-radius,h/2-radius,cx+radius,h/2+radius,fill=col,outline='#c9ced1' if active else EDGE,width=1)
            x+=17
    def tag_tool_click(self,event):
        if event.x<29:self.favorite_filter=not self.favorite_filter
        else:
            i=int((event.x-31)//17)
            if not 0<=i<7:return
            if i in self.tag_filters:self.tag_filters.remove(i)
            else:self.tag_filters.add(i)
        self.draw_tag_tools();self.populate()
    def source_changed(self):
        self.populate()
    def _connect_hardware(self):
        ok,msg=self.hardware.connect_auto()
        if ok:
            # The main Library GET command owns physical catalog refreshes.
            # LIVE opens immediately from the shared persisted catalog.
            self.status.set(msg)
        else:self.status.set(msg)
    def _hardware_event(self,kind,*args):
        try:self.after(0,lambda k=kind,a=args:self._hardware_event_ui(k,*a))
        except Exception:pass
    def _hardware_event_ui(self,kind,*args):
        if kind=='name':
            slot,name=args;slot=int(slot);self.hardware_names[slot]=name;self._catalog_seen.add(slot)
            if self._catalog_save:
                try:self.after_cancel(self._catalog_save)
                except Exception:pass
            self._catalog_save=self.after(250,self._save_hardware_catalog)
            if self._catalog_refresh is None:self._catalog_refresh=self.after(50,self._refresh_hardware_catalog)
        elif kind=='page' and self._scan_target is not None:
            slot,page=args
            if int(slot)!=self._scan_target:return
            if self._scan_timeout:
                try:self.after_cancel(self._scan_timeout)
                except Exception:pass
                self._scan_timeout=None
            if page<4:
                self.hardware.scan_page=page+1;self.hardware.request_page(slot,page+1);self._scan_timeout=self.after(900,self._scan_page_timeout)
            else:
                status=pages_have_sequence(self.hardware.pages);self.hardware_sequence_status[slot]=status
                self.hardware.sequence_status[slot]=status;self.hardware_pages[slot]=dict(self.hardware.pages);self._cache_hardware_snapshot(slot);self._scan_target=None;self._scan_retries=0;self.populate()
                if slot in self._snapshot_restore_slots:
                    self._snapshot_restore_slots.discard(slot);self.after(2,self._read_next_snapshot_restore)
                else:self.after(2,self._scan_next_unknown)
    def _start_hardware_catalog(self):
        if not self.hardware.connected:return
        self._catalog_slot=1;self._catalog_retry=0;self._catalog_seen=set();self._catalog_queue=list(range(1,257));self._request_catalog_slot()
    def _request_catalog_slot(self):
        if not self.hardware.connected:return
        if not self._catalog_queue:
            self._catalog_timeout=self.after(650,self._catalog_slot_timeout);return
        self._catalog_slot=int(self._catalog_queue.pop(0));self.hardware.request_name(self._catalog_slot)
        self.after(30 if self._catalog_retry==0 else 70,self._request_catalog_slot)
    def _catalog_slot_timeout(self):
        self._catalog_timeout=None
        if self._catalog_retry<3:
            self._catalog_retry+=1;self._catalog_queue=[n for n in range(1,257) if n not in self._catalog_seen]
            if self._catalog_queue:self._request_catalog_slot()
            elif self._snapshot_restore_slots:self.after(20,self._read_next_snapshot_restore)
        elif self._snapshot_restore_slots:self.after(20,self._read_next_snapshot_restore)
    def _refresh_hardware_catalog(self):
        self._catalog_refresh=None;self.populate()
    def _save_hardware_catalog(self):
        self._catalog_save=None
        try:save_hardware_names(self.hardware_names)
        except OSError:pass
    def _start_hardware_sequence_scan(self):
        if not self.hardware.connected:return
        if self._scan_target is None:self._scan_next_unknown()
    def _scan_next_unknown(self):
        if not self.sequence_filter:self._scan_target=None;return
        slot=next((n for n in range(1,257) if n not in self.hardware_sequence_status),None)
        if slot is None:self._scan_target=None;return
        self._begin_hardware_read(slot)
    def _begin_hardware_read(self,slot):
        if not self.hardware.connected:return
        if self._scan_timeout:
            try:self.after_cancel(self._scan_timeout)
            except Exception:pass
        self._scan_target=int(slot);self._scan_retries=0;self.hardware.scan_slot=int(slot);self.hardware.scan_page=0;self.hardware.pages={}
        self.hardware_sequence_status.pop(int(slot),None);self.hardware.request_page(int(slot),0);self._scan_timeout=self.after(900,self._scan_page_timeout);self.populate()
    def _scan_page_timeout(self):
        slot=self._scan_target;self._scan_timeout=None
        if slot is None:return
        if self._scan_retries<2:
            self._scan_retries+=1;page=self.hardware.scan_page;self.hardware.request_page(slot,page);self._scan_timeout=self.after(900,self._scan_page_timeout);return
        self.hardware_sequence_status[slot]=None;self._scan_target=None;self._scan_retries=0;self.populate()
        if slot in self._snapshot_restore_slots:
            self._snapshot_restore_slots.discard(slot);self.after(2,self._read_next_snapshot_restore)
        else:self.after(2,self._scan_next_unknown)
    def _read_next_snapshot_restore(self):
        if self._scan_target is not None:return
        slot=next(iter(sorted(self._snapshot_restore_slots)),None)
        if slot is not None:self._begin_hardware_read(slot)
    def _local_has_sequence(self,path):
        seq=self._notes_for(str(path));return any(step for step in seq)
    def browser_menu(self,event):
        index=int(self.tree.canvasy(event.y)//27)
        if 0<=index<len(self.browser_rows):self.browser_selected=self.browser_rows[index][0]
        m=tk.Menu(self,tearoff=False,bg=PANEL2,fg=TEXT,activebackground=ORANGE,activeforeground='#0d1114')
        m.add_command(label='Open folder…',command=self.choose_root)
        try:m.tk_popup(event.x_root,event.y_root)
        finally:m.grab_release()
    def choose_root(self):
        folder=filedialog.askdirectory(parent=self)
        if folder:self.set_root(folder);self.session.global_settings['library_root']=folder;self.persist()
    def set_root(self,folder):self.root_folder=folder;self.expanded=set();self.browser_selected=None;self.populate()
    def populate(self):
        self.tree.delete('all');self.browser_rows=[]
        hwroot=('HWROOT',)
        self.browser_rows.append((hwroot,0))
        if hwroot in self.expanded:
            for n in range(1,257):
                status=self.hardware_sequence_status.get(n,'UNKNOWN')
                if self.sequence_filter and status is not True:continue
                self.browser_rows.append((('HW',n),1))
        def walk(folder,depth):
            items=list(children(folder));items.sort(key=lambda p:(not p.is_dir(), (order_for(p) is None) if p.is_file() else False, order_for(p) if p.is_file() and order_for(p) is not None else 0, p.name.lower()))
            for path in items:
                if path.is_file():
                    if self.favorite_filter and not favorite_for(path):continue
                    if self.tag_filters and not self.tag_filters.issubset(set(tags_for(path))):continue
                    if self.sequence_filter and not self._local_has_sequence(path):continue
                self.browser_rows.append((path,depth))
                if path.is_dir() and path in self.expanded:walk(path,depth+1)
        walk(self.root_folder,0)
        number=0
        for i,(path,depth) in enumerate(self.browser_rows):
            y=14+i*27
            if path==hwroot:
                prefix='▾ ' if hwroot in self.expanded else '▸ '
                self.tree.create_text(40,y,text=prefix+'UnoSynthPro',anchor='w',fill=TEXT,font=self.small_font);continue
            if isinstance(path,tuple) and path and path[0]=='HW':
                n=int(path[1]);name=self.hardware_names.get(n,'') or '—';status=self.hardware_sequence_status.get(n,'UNKNOWN')
                if n==self.hardware_selected:self.tree.create_rectangle(4,y-12,238,y+12,fill=PANEL2,outline='#c9ced1',width=1)
                self.tree.create_text(7,y,text=f'{n:03d}',anchor='w',fill='#c9ced1' if n==self.hardware_selected else MUTED,font=('Segoe UI',9))
                self.tree.create_text(54,y,text=clipped(name,144,self.small_font),anchor='w',fill=TEXT if name!='—' else MUTED,font=self.small_font)
                glyph='SEQ' if status is True else ('—' if status is False else '?')
                self.tree.create_text(230,y,text=glyph,anchor='e',fill=ORANGE if status is True else MUTED,font=('Segoe UI',7,'bold'));continue
            if path==self.browser_selected:self.tree.create_rectangle(4,y-12,238,y+12,fill='#30363a',outline=ORANGE)
            prefix=('▾ ' if path in self.expanded else '▸ ') if path.is_dir() else '  ';name=path.name if path.is_dir() else path.stem
            if not path.is_dir():
                number+=1;self.tree.create_text(7,y,text=f'{number:03d}',anchor='w',fill=MUTED,font=('Segoe UI',9),tags='preset-number')
            text=prefix+name;available=max(10,205-(40+depth*14))
            self.tree.create_text(40+depth*14,y,text=clipped(text,available,self.small_font),anchor='w',fill=TEXT,font=self.small_font)
        self.tree.configure(scrollregion=(0,0,240,max(1,len(self.browser_rows)*27)))
    def tree_press(self,event):
        self.source=None;i=int(self.tree.canvasy(event.y)//27)
        if not 0<=i<len(self.browser_rows):return
        path,depth=self.browser_rows[i];self.browser_selected=path
        if path==('HWROOT',):
            if path in self.expanded:self.expanded.remove(path)
            else:self.expanded.add(path)
            self.populate();return
        if isinstance(path,tuple) and path and path[0]=='HW':
            n=int(path[1]);self.hardware_selected=n;self.source=None
            if self.hardware.connected:
                self.hardware.request_name(n)
                if n in self.hardware_pages and self.hardware_sequence_status.get(n) in (True,False):
                    name=self.hardware_names.get(n,'') or f'Preset {n:03d}';self.source=f'hardware://{n:03d}/{name}';self.drag_start=(event.x_root,event.y_root)
                else:self._begin_hardware_read(n)
            self.populate();return
        if path.is_dir():
            if path in self.expanded:self.expanded.remove(path)
            else:self.expanded.add(path)
        else:self.source=path;self.drag_start=(event.x_root,event.y_root)
        self.populate()
    def geometry_slots(self):return Slots(self.timeline.winfo_width(),self.timeline_zoom)
    def timeline_zoom_wheel(self,event):
        direction=1 if event.delta>0 else -1 if event.delta<0 else 0
        return self.timeline_zoom_step(event,direction)
    def timeline_zoom_step(self,event,direction):
        if not direction:return 'break'
        old_zoom=self.timeline_zoom
        new_zoom=max(.25,min(1.0,round(old_zoom+(.05 if direction>0 else -.05),2)))
        if new_zoom==old_zoom:return 'break'
        old_geom=Slots(self.timeline.winfo_width(),old_zoom)
        view_x=float(getattr(event,'x',self.timeline.winfo_width()/2))
        anchor_x=self.timeline.canvasx(view_x)
        logical=(anchor_x-old_geom.margin)/old_geom.pitch
        self.timeline_zoom=new_zoom
        self.render();self.update_idletasks()
        new_geom=Slots(self.timeline.winfo_width(),new_zoom)
        # Keep the same logical Timeline point under the mouse while zooming.
        # Tk Canvas xview_moveto() takes a fraction of the complete scrollregion,
        # not a fraction of only the scrollable remainder.
        target=new_geom.margin+logical*new_geom.pitch-view_x
        max_left=max(0.0,new_geom.total_width-self.timeline.winfo_width())
        target=max(0.0,min(max_left,target))
        self.timeline.xview_moveto(target/max(1.0,new_geom.total_width))
        return 'break'
    def target(self,x,y):
        if not(0<=x<=self.timeline.winfo_width() and 0<=y<100):return None
        pos=self.geometry_slots().position(self.timeline.canvasx(x),y);slot=min(64,int(pos))
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
        source_name=self.library.label(self.source) if isinstance(self.source,str) else self.source.stem
        self.ghost.configure(text=source_name);self.ghost.place(x=max(0,min(self.winfo_width()-180,event.x_root-self.winfo_rootx()+12)),y=event.y_root-self.winfo_rooty()+12,width=170);self.ghost.lift()
        x=event.x_root-self.timeline.winfo_rootx();y=event.y_root-self.timeline.winfo_rooty()
        target=self.target(x,y);self.preview=(target,source_name) if target else None
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
            parameters=self._hardware_snapshot(preset)
            if mode=='REPLACE':self.model.replace(id,preset,parameters)
            else:
                self.model.insert_at_slot(index,preset,slot,parameters)
            self.model.select(slot);self.session.song.colors.setdefault(preset,color_for(preset))
        self.perform(action)
    def hit(self,x,y):return next((box for box in self.boxes if box[0]<=x<=box[2] and box[1]<=y<=box[3]),None)
    def edge(self,box,x):
        x1,y,x2,y2,b,s,e,start,end=box
        if s==start and abs(x-x1)<=4:return 'left'
        if e==end and abs(x-x2)<=4:return 'right'
    def hover(self,event):
        x=self.timeline.canvasx(event.x);box=self.hit(x,event.y)
        self.timeline.configure(cursor=('sb_h_double_arrow' if self.edge(box,x) else 'fleur') if box else '')
    def press(self,event):
        self.timeline.focus_set();x=self.timeline.canvasx(event.x);box=self.hit(x,event.y)
        if not box:
            self.model.selection.clear();self.model.selected_step=None;self.render();return
        x1,y,x2,y2,b,s,e,start,end=box
        self.select(start,bool(getattr(event,'state',0)&5))
        self.drag=(b.id,self.geometry_slots().position(x,event.y),b.length,self.edge(box,x))
        self.drag_position=self.drag[1];self.render()
    def motion(self,event):
        if self.drag:
            self.drag_position=self.geometry_slots().position(self.timeline.canvasx(event.x),event.y);self.render()
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
        delta=round(self.geometry_slots().position(self.timeline.canvasx(event.x),event.y)-pos)
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
        box=self.hit(self.timeline.canvasx(event.x),event.y)
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
    @staticmethod
    def _mix(a,b,amount):
        amount=max(0.0,min(1.0,float(amount)))
        av=[int(a.lstrip('#')[i:i+2],16) for i in (0,2,4)];bv=[int(b.lstrip('#')[i:i+2],16) for i in (0,2,4)]
        return '#'+''.join(f'{round(x+(y-x)*amount):02x}' for x,y in zip(av,bv))
    def _clip_surface(self,c,x,y,x2,y2,color,outline,width,tags,glow=False):
        """Unified clip surface: solid color with square corners."""
        x=int(round(x));y=int(round(y));x2=int(round(x2));y2=int(round(y2));w=max(2,x2-x);h=max(2,y2-y)
        fill=self._mix(PANEL,color,.82)
        if PIL_OK:
            try:
                cache_key=(w,h,color,outline,int(width),bool(glow));cached=self._clip_surface_cache.get(cache_key)
                if cached is not None:
                    self._clip_images.append(cached);c.create_image(x,y,image=cached,anchor='nw',tags=tags);return
                ss=6;W=w*ss;H=h*ss
                image=Image.new('RGBA',(W,H),(0,0,0,0));rgb=tuple(int(fill[i:i+2],16) for i in (1,3,5))
                ImageDraw.Draw(image).rectangle((1,1,W-2,H-2),fill=rgb+(218,))
                if glow:
                    haze=Image.new('RGBA',(W,H),(0,0,0,0));hd=ImageDraw.Draw(haze);hc=(201,206,209,150)
                    hd.line((1,3,W-2,3),fill=hc,width=10)
                    haze=haze.filter(ImageFilter.GaussianBlur(5));image.alpha_composite(haze)
                dr=ImageDraw.Draw(image);ow=max(1,int(width*ss));oc=outline
                dr.rectangle((ow//2,ow//2,W-1-ow//2,H-1-ow//2),outline=oc,width=ow)
                image=image.resize((w,h),Image.Resampling.LANCZOS);photo=ImageTk.PhotoImage(image);self._clip_surface_cache[cache_key]=photo;self._clip_images.append(photo);c.create_image(x,y,image=photo,anchor='nw',tags=tags);return
            except Exception:pass
        c.create_rectangle(x,y,x2,y2,fill=fill,stipple='gray25',outline=outline,width=width,tags=tags)
    def _hardware_slot(self,reference):
        if isinstance(reference,str) and reference.startswith('hardware://'):
            try:return int(reference.split('/')[2])
            except (ValueError,IndexError):return None
        return None
    def _hardware_snapshot(self,reference):
        """Embed the read-only hardware sequence data needed after restart."""
        slot=self._hardware_slot(reference)
        if slot is None:return {}
        pages=self.hardware_pages.get(slot,{})
        if any(page not in pages for page in range(5)):
            raise ValueError(f'HARDWARE {slot:03d} sequence is not fully loaded')
        return {'hardware_slot':slot,'hardware_name':self.hardware_names.get(slot,''),
                'hardware_pages':{str(page):bytes(pages[page]).hex() for page in range(5)}}
    def _restore_hardware_snapshots(self):
        """Rehydrate factory clips from pad state without a local preset file."""
        self._snapshot_restore_slots=set()
        for song in self.session.pads:
            for block in song.timeline.blocks:
                slot=self._hardware_slot(block.preset)
                raw=block.parameters.get('hardware_pages',{}) if isinstance(block.parameters,dict) else {}
                if slot is None:continue
                if not isinstance(raw,dict) or not raw:
                    self._snapshot_restore_slots.add(slot);continue
                try:pages={int(page):bytes.fromhex(value) for page,value in raw.items()}
                except (TypeError,ValueError):self._snapshot_restore_slots.add(slot);continue
                if any(page not in pages for page in range(5)):
                    self._snapshot_restore_slots.add(slot);continue
                self.hardware_pages[slot]=pages;self.hardware_sequence_status[slot]=pages_have_sequence(pages)
                name=block.parameters.get('hardware_name','')
                if isinstance(name,str) and name:self.hardware_names[slot]=name
    def _cache_hardware_snapshot(self,slot):
        pages=self.hardware_pages.get(int(slot),{})
        if any(page not in pages for page in range(5)):return
        payload={'hardware_slot':int(slot),'hardware_name':self.hardware_names.get(int(slot),''),
                 'hardware_pages':{str(page):bytes(pages[page]).hex() for page in range(5)}}
        changed=False
        for song in self.session.pads:
            items=[];song_changed=False
            for block in song.timeline.blocks:
                if self._hardware_slot(block.preset)==int(slot):
                    block=replace(block,parameters=dict(payload));changed=True;song_changed=True
                items.append(block)
            if song_changed:song.timeline.blocks=tuple(items)
        if changed:self.persist()
    def _hardware_notes(self,slot):
        pages=self.hardware_pages.get(int(slot),{})
        if any(p not in pages for p in range(5)):return ()
        try:
            from live_creator.devices.uno.unosyp_seq_decoder import decode_payload_note_steps
            result=[]
            for page in range(1,5):
                for step in decode_payload_note_steps(bytes(pages[page]),page-1):
                    result.append(tuple(int(v['note_raw']) for v in step['voices'] if not v['empty'] and 0<=int(v['note_raw'])<=127))
            return tuple(result[:64])
        except Exception:return ()
    def _sequence_beats_for(self,reference):
        slot=self._hardware_slot(reference)
        if slot is None:return sequence_beats(reference)
        pages=self.hardware_pages.get(slot,{})
        try:
            from live_creator.devices.uno.timing import decode_hardware_sequence_length
            length=decode_hardware_sequence_length(pages.get(0,b''));return length/4 if length is not None else None
        except Exception:return None
    def _notes_for(self,reference):
        if not reference:return ()
        slot=self._hardware_slot(reference)
        if slot is not None:return self._hardware_notes(slot)
        try:stamp=(Path(reference).stat().st_mtime_ns,Path(reference).stat().st_size)
        except OSError:stamp=None
        cached=self.sequence_notes_cache.get(reference)
        if cached and cached[0]==stamp:return cached[1]
        notes=read_sequence_notes(reference);self.sequence_notes_cache[reference]=(stamp,notes);return notes
    def _draw_clip_content(self,c,b,x,y,x2,y2,playing=False,slot_pitch=None,clip_color=None):
        if not b.preset:return
        width=max(1,x2-x);header_y=y+8;divider=y+15
        title=clipped(self.label(b),max(1,width-10),self.small_font);surface=self._mix(PANEL,clip_color or self.block_color(b),.82);ink=contrast(surface);soft=self._mix(surface,ink,.55)
        c.create_text(x+5,header_y,text=title,anchor='w',fill=ink,font=('Segoe UI',8,'bold'),tags=('clip-title',b.id))
        c.create_line(x+3,divider,x2-3,divider,fill=soft,width=1,tags=('clip-divider',b.id))
        sequence=self._notes_for(b.preset);active=[note for step in sequence for note in step]
        pitch=max(1,float(slot_pitch or width));count=max(1,int(round(width/pitch)))
        low=min(active) if active else 0;high=max(active) if active else 1;span=max(1,high-low)
        # Each occupied Timeline slot renders its own complete sequence; the title remains one for the whole block.
        for slot_index in range(count):
            sx=x+slot_index*pitch;ex=min(x2,sx+pitch);left=sx+4;right=ex-4;top=divider+3;bottom=y2-3
            if right<=left:continue
            if not active:
                text=clipped('NO SEQUENCE',max(1,right-left),self.small_font)
                c.create_text((left+right)/2,divider+(y2-divider)/2,text=text,fill=soft,font=('Segoe UI',7),tags=('clip-notes',b.id));continue
            # Note geometry follows the same horizontal scale as its clip slot.
            # Clamp every note to the slot bounds so compressed clips can never
            # leave stale-looking note tails outside their container.
            step_w=(right-left)/max(1,len(sequence))
            for index,notes in enumerate(sequence):
                for note in notes:
                    yy=bottom-(note-low)/span*max(1,bottom-top)
                    xx=left+index*step_w
                    note_right=min(right,xx+max(.25,step_w*.82))
                    if note_right<=xx:continue
                    c.create_rectangle(xx,yy-1,note_right,yy+1,fill=ink if not playing else '#ffffff',outline='',tags=('clip-notes',b.id))
    def _draw_marker(self,c,x,y,text,width):
        if PIL_OK:
            try:
                key=('marker',ORANGE);ph=self._marker_image_cache.get(key)
                if ph is None:
                    ss=4;W,H=13*ss,18*ss;img=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(img);rgb=tuple(int(ORANGE[i:i+2],16) for i in (1,3,5))
                    d.rounded_rectangle((1*ss,0,2*ss,16*ss),radius=ss,fill=rgb+(255,));d.polygon(((2*ss,0),(11*ss,4*ss),(2*ss,8*ss)),fill=rgb+(255,))
                    img=img.resize((13,18),Image.Resampling.LANCZOS);ph=ImageTk.PhotoImage(img);self._marker_image_cache[key]=ph
                c.create_image(round(x),round(y-17),image=ph,anchor='nw',tags='marker');c.create_text(round(x+13),round(y-12),text=clipped(text,width,self.small_font),anchor='w',fill=TEXT,font=self.small_font,tags='marker');return
            except Exception:pass
        c.create_line(round(x+2),round(y-17),round(x+2),round(y-2),fill=ORANGE,tags='marker');c.create_polygon(round(x+2),round(y-17),round(x+10),round(y-14),round(x+2),round(y-10),fill=ORANGE,tags='marker');c.create_text(round(x+13),round(y-12),text=clipped(text,width,self.small_font),anchor='w',fill=TEXT,font=self.small_font,tags='marker')
    def render(self):
        c=self.timeline;c.delete('all');self.boxes=[];self._clip_images=[];geom=self.geometry_slots();now=time.monotonic();c.configure(scrollregion=(0,0,geom.total_width,100))
        for col in range(65):
            x=10+col*geom.pitch
            c.create_line(x,37,x,91,fill=self._mix(EDGE,TEXT,.18) if col%8==0 else self._mix(PANEL2,EDGE,.34),tags='slot-grid')
            if col<64:c.create_text(x+geom.pitch/2,13,text=f'{col+1:02d}',fill=MUTED,font=('Segoe UI',8),tags='slot-number')
        for b,start,end in self.model.ranges():
            playing=self.session.playing_pad==self.session.selected and b.id==self.session.playing_block_id
            color=self.block_color(b)
            if playing:color=pulse(color,now)
            if self.drag and self.drag[0]==b.id and not self.drag[3]:color=PANEL2
            for x,y,x2,y2,s,e in geom.segments(start,end):
                self.boxes.append((x,y,x2,y2,b,s,e,start,end))
                selected=b.id in self.model.selection
                edge='#c9ced1' if selected else self._mix(color,'#ffffff',.35)
                self._clip_surface(c,x,y,x2,y2,color,edge,1,('block',b.id),glow=selected)
                for boundary in range(s+1,e+1):
                    bx=x+(boundary-s)*geom.pitch;c.create_line(bx,y+1,bx,y2-1,fill=self._mix(EDGE,TEXT,.18),width=1,tags=('clip-slot-divider',b.id))
                self._draw_clip_content(c,b,x+1,y,x2-1,y2,playing,geom.pitch,color)
                if self.model.loop_range and s<=self.model.loop_range[1] and e>=self.model.loop_range[0]:
                    ls=max(s,self.model.loop_range[0]);le=min(e,self.model.loop_range[1])
                    active=self.session.playing_pad==self.session.selected and self.session.loop_state==Loop.ACTIVE
                    c.create_line(x+(ls-s)*geom.pitch,y2+4,x+(le-s+1)*geom.pitch,y2+4,fill=ORANGE,width=4 if active else 2,dash=() if active else (4,3),tags='loop')
        for slot in range(self.session.song.length+1,65):
            x,y=geom.point(slot);c.create_rectangle(x,y,x+geom.pitch,y+geom.clip_height,fill=PANEL,stipple='gray50',outline='',tags='inactive')
        for step,end,text in self.model.sections():
            if step>self.session.song.length:continue
            end=min(end,self.session.song.length)
            x,y=geom.point(step);width=max(4,(end-step+1)*geom.pitch-14)
            self._draw_marker(c,x,y,text,width)
        self.render_grid();self.draw_preview();self.draw_drag()
        is_playback=self.session.playback is not None and self.session.playback_pad==self.session.selected
        duration=sum(self.session.durations) if is_playback and self.session.active else self.session.duration(self.session.song)
        elapsed=min(self.session.position,duration) if is_playback and duration is not None else 0
        def clock(value):
            if value is None:return '—'
            seconds=int(value);return f'{seconds//60:02d}:{seconds%60:02d}'
        self.metrics.set(f'DURATION     {clock(duration)}\nELAPSED        {clock(elapsed if duration is not None else None)}\nREMAINING   {clock(max(0,duration-elapsed) if duration is not None else None)}\n\nSTEPS             {min(self.model.length,self.session.song.length)} / 64\nBLOCKS          {sum(b.preset is not None and s<=self.session.song.length for b,s,e in self.model.ranges())}')
        self.play_button.set('PLAY',self._play_button_active and self.session.active)
        self.stop_button.set('STOP',self.session.active)
        self._draw_name_gradient()
        self.marker_list.delete('all')
        for i,(step,label) in enumerate(sorted(self.model.markers.items())):
            self.marker_list.create_text(4,i*22+11,text=f'{step:02d}   '+clipped(label,165,self.small_font),anchor='w',fill=TEXT,font=self.small_font)
        self.marker_list.configure(scrollregion=(0,0,200,len(self.model.markers)*22))
    @staticmethod
    def _shade(color,f):
        c=color.lstrip('#');v=[int(c[i:i+2],16) for i in (0,2,4)];return '#'+''.join(f'{max(0,min(255,round(n*f))):02x}' for n in v)
    @staticmethod
    def _pad_led_color(color):
        """Turn the stored song color into the saturated LED color of an MPC pad."""
        raw=color.lstrip('#');rgb=tuple(int(raw[i:i+2],16)/255 for i in (0,2,4));h,s,v=colorsys.rgb_to_hsv(*rgb)
        return '#'+''.join(f'{round(channel*255):02x}' for channel in colorsys.hsv_to_rgb(h,max(.78,s),max(.92,v)))
    def _pad_surface(self,c,x,y,size,color,outline,width=2,glow=False,intense=False,dim=False):
        # Akai MPC-style rubber pad with four illuminated corner brackets.
        x=int(round(x));y=int(round(y));size=max(2,int(round(size)))
        if PIL_OK:
            try:
                cache_key=(size,outline,int(width),bool(glow),bool(intense),bool(dim));cached=self._pad_surface_cache.get(cache_key)
                if cached is not None:
                    self._pad_images.append(cached);c.create_image(x,y,image=cached,anchor='nw');return
                ss=4;W=size*ss;H=W;r=max(3*ss,int(size*.07*ss));base='#202428';br=[int(base[i:i+2],16) for i in (1,3,5)]
                img=Image.new('RGBA',(W,H),(0,0,0,0));mask=Image.new('L',(W,H),0);md=ImageDraw.Draw(mask);md.rounded_rectangle((2*ss,2*ss,W-2*ss-1,H-2*ss-1),radius=r,fill=255)
                shadow=Image.new('RGBA',(W,H),(0,0,0,0));ImageDraw.Draw(shadow).rounded_rectangle((2*ss,3*ss,W-2*ss-1,H-ss-1),radius=r,fill=(0,0,0,170));shadow=shadow.filter(ImageFilter.GaussianBlur(2*ss));img.alpha_composite(shadow)
                grad=Image.new('RGBA',(W,H),(0,0,0,0));gd=ImageDraw.Draw(grad);cy=(H-1)/2
                for yy in range(H):
                    d=abs(yy-cy)/max(1,cy);f=.90+.12*d;col=tuple(max(0,min(255,round(v*f))) for v in br)+(255,);gd.line((0,yy,W,yy),fill=col)
                grad.putalpha(mask);img.alpha_composite(grad)
                rgb=tuple(int(outline[i:i+2],16) for i in (1,3,5))
                inset=max(5*ss,int(size*.10*ss));gap=max(3*ss,int(size*.065*ss));mid=W//2;led_w=max(2*ss,int(size*.065*ss));end=mid-gap
                paths=[((mid+gap,inset),(W-inset,inset),(W-inset,end)),((W-inset,mid+gap),(W-inset,H-inset),(mid+gap,H-inset)),((end,H-inset),(inset,H-inset),(inset,mid+gap)),((inset,end),(inset,inset),(end,inset))]
                glow_layer=Image.new('RGBA',(W,H),(0,0,0,0));g=ImageDraw.Draw(glow_layer)
                glow_alpha=45 if dim else (235 if intense else 175)
                for path in paths:g.line(path,fill=rgb+(glow_alpha,),width=led_w+(2*ss if intense else 0),joint='curve')
                glow_layer=glow_layer.filter(ImageFilter.GaussianBlur(3*ss if intense or glow else 2*ss));img.alpha_composite(glow_layer)
                led=Image.new('RGBA',(W,H),(0,0,0,0));ld=ImageDraw.Draw(led)
                core=tuple(min(255,round(v*1.08)) for v in rgb)+((105 if dim else 255),)
                for path in paths:ld.line(path,fill=core,width=led_w,joint='curve')
                img.alpha_composite(led)
                if intense:ImageDraw.Draw(img).rounded_rectangle((2*ss,2*ss,W-2*ss-1,H-2*ss-1),radius=r,outline=(215,220,223,190),width=ss)
                img=img.resize((size,size),Image.Resampling.LANCZOS);ph=ImageTk.PhotoImage(img);self._pad_surface_cache[cache_key]=ph
                if not hasattr(self,'_pad_images'):self._pad_images=[]
                self._pad_images.append(ph);c.create_image(x,y,image=ph,anchor='nw');return
            except Exception:pass
        fallback_edge=self._mix('#202428',outline,.42) if dim else outline
        self.round_block(c,x,y,x+size,y+size,fill='#202428',outline=fallback_edge,width=1)
    def render_grid(self):
        c=self.grid_canvas;c.delete('all');self._pad_images=[];self.pad_boxes=[];side=max(80,min(c.winfo_width()-24,c.winfo_height()-12));pitch=side/8;size=pitch*.88;left=(c.winfo_width()-side)/2
        for i,song in enumerate(self.session.pads):
            x=int(round(left+(i%8)*pitch));y=int(round(6+(i//8)*pitch));psize=max(2,int(round(size)));self.pad_boxes.append((i,x,y,psize));selected=i==self.session.selected;playing=i==self.session.playing_pad
            occupied=bool(song.timeline.length);color=song.color;led=self._pad_led_color(color)
            if playing:edge=led if int(time.monotonic()*3)%2==0 else self._shade(led,.72);glow=True;intense=True
            elif selected:edge=led;glow=True;intense=True
            else:edge=led;glow=False;intense=False
            self._pad_surface(c,x,y,psize,'#1b2024',edge,2,glow,intense,dim=not occupied);size=psize
            c.create_text(x+size*.18,y+size*.17,text=f'{i+1:02d}',anchor='nw',fill='#aeb5b9',font=('Segoe UI',7),tags=f'pad-number-{i}')
    @staticmethod
    def round_block(canvas,x,y,x2,y2,**options):
        r=min(4,(x2-x)/2,(y2-y)/2)
        return canvas.create_polygon(x+r,y,x2-r,y,x2,y,x2,y+r,x2,y2-r,x2,y2,x2-r,y2,x+r,y2,x,y2,x,y2-r,x,y+r,x,y,smooth=True,splinesteps=24,**options)
