import json
import tkinter as tk
from tkinter import filedialog,messagebox,simpledialog
from pathlib import Path
import math,json,copy,threading,queue,time,logging,random,shutil
try:
 from PIL import Image,ImageDraw,ImageTk
 PIL_OK=True
except Exception:
 Image=ImageDraw=ImageTk=None;PIL_OK=False
from data_model import Preset,Song,SongSlot,Sequence
import storage
import ui_theme
from ui_theme import widgets as tk
from automation_metadata import AUTOMATABLE,PARAMETERS,parameter_line,display_value
from midi_engine import MidiEngine
from protocol_map import *
from state_decoder import decode_state_0x37
from unosyp_state_decoder import decode_0x37_raw,decode_extended_preset_fields
from hardware_seq_0x29 import parse_0x29_response,apply_to_sequence

MATRIX_SOURCES=['Velocity','Mod Wheel','Aftertouch','Key Pitch','Key Gate','Osc 1 Tune','Osc 1 Level','Osc 2 Tune','Osc 2 Level','Osc 3 Tune','Osc 3 Level','Noise','Filter 1 Cutoff','Filter 1 Res','Filter 2 Cutoff','Filter 2 Res','Filter Spacing','LFO 1','LFO 1 Fade In','LFO 2','LFO 2 Fade In','Filter Env','Amp Env','CV 1 IN','GATE 1 IN','CV 2 IN','GATE 2 IN','Accent','Gate','Tie']
MATRIX_DESTINATIONS=['OFF','Osc 1 Tune','Osc 1 Wave','Osc 1 Level','Osc 2 Tune','Osc 2 Wave','Osc 2 Level','Osc 2 FM Amount','Osc 3 Tune','Osc 3 Wave','Osc 3 Level','Osc 3 FM Amount','Noise level','Filter 1 Cutoff','Filter 1 Res','Filter 2 Cutoff','Filter 2 Res','Filter Spacing','LFO 1 Wave','LFO 1 Rate','LFO 2 Wave','LFO 2 Rate','Filter 1 Env Amount','Filter 2 Env Amount','Amp Env Amount','Drive Amount','Delay Amount','Reverb Amount','Mod Amount','CV OUT 1','GATE OUT 1','CV OUT 2','GATE OUT 2','Accent Amount']+[f'Mod {i} Amount' for i in range(1,17)]

BG='#101417'; PANEL='#1b2024'; PANEL2='#22282d'; EDGE='#3b444a'; TEXT='#e7e9ea'; MUTED='#8e989f'; LIGHT_GREY='#c9ced1'; ORANGE='#ff8c18'; ORANGE2='#8a4b12'; BLUE='#4db8ff'; GREEN='#8ecb18'; RED='#d83a3a'; WHITE='#f5f5f5'
BASE_W,BASE_H=1600,1000
logger=logging.getLogger(__name__)

def clamp(v,a,b):return max(a,min(b,v))

class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title('UNO Pro Advanced v0.9.6-beta'); self.configure(bg=BG)
  sw,sh=self.winfo_screenwidth(),self.winfo_screenheight(); w,h=1440,900; self.geometry(f'{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}'); self.resizable(False,False)
  self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0);self.canvas.pack(fill='both',expand=True)
  self.settings=storage.load_settings();self.settings.setdefault('ui_scale','100%');self.settings.setdefault('pitch_bend_range',2);self.settings['midi_clock']='MIDI MASTER' if self.settings.get('midi_clock')=='MIDI' else ('Off' if self.settings.get('midi_clock') not in ('Off','MIDI MASTER') else self.settings.get('midi_clock'));self.settings_dirty=False;self._applied_settings=copy.deepcopy(self.settings);self.keyboard_visible=bool(self.settings.get('keyboard_visible',False));self.keyboard_octave_shift=0;self._clock_master_job=None;self.page='SYNTH';self._apply_ui_scale(self.settings.get('ui_scale','100%'),save=False)
  self.song_mode='SONG';self.preset=Preset();self.song=Song();self.selected_song_file=None
  self.live_editor=None;self.automation_parameter='CUTOFF 1';ui_theme.set_theme(self.settings.get('theme','dark'))
  self.configure(bg=ui_theme.color(BG));self.canvas.configure(bg=ui_theme.color(BG))
  self.scale=1;self.ox=0;self.oy=0;self.hit=[];self.drag=None;self.popup=None;self.status='OFFLINE';self._closing=False;self._graph_images=[];self.selected_seq_step=0;self.selected_seq_note=None;self.seq_visible=16;self.seq_hscroll=0;self.seq_note_low=36;self.seq_param='GATE';self.seq_mod=0;self.seq_overdub='MONO';self.seq_resolution='1/16';self.seq_timing='STRAIGHT';self.seq_swing=0;self.seq_clipboard=None;self.selected_song_slot=0;self.selected_live_slot=0;self.song_preset_folder=storage.PRESETS;self.song_folder_scroll=0;self.live_slots=(list(self.settings.get('live_slots',[]))[:64]+[None]*64)[:64];self.lib_category='All';self.lib_query='';self.lib_selected=None;self.hardware_selected=1;self.preview=True;self.preset_source='HARDWARE';self.preset_folder=None;self.lib_panel_source=['LOCAL','UNO'];self.lib_panel_folder=[storage.PRESETS,None];self.lib_scroll=[0,0];self.lib_hscroll=[0,0];self.lib_expanded=set();self.lib_star_filter=False;self.lib_color_filters=set();self.lib_right_mode='UNO';self.lib_right_folder=None;self._lib_folder_entry=None;self._lib_folder_entry_window=None;self._lib_tooltip_job=None;self._lib_tooltip=None;self._mod_tooltip_job=None;self._mod_tooltip=None;self.keys_down=set();self.hw_keys_down=set();self.pitch_visual=0;self.open_dropdown=None;self.dropdown_scroll=0;self.dropdown_hover=None;self._lib_search_entry=None;self._lib_clipboard=None;self._lib_folder_clipboard=None;self._lib_drag_origin=None;self._lib_drag_started=False;self._lib_drag_pos=None;self.lib_focus=0;self.lib_hw_selected=1;self._seq_fill_flash=False;self.song_tree_expanded={str(storage.PRESETS)};self.song_tree_selected=storage.PRESETS;self.matrix_scroll=0;self.seq_playing=False;self.seq_recording=False;self.seq_record_step=0;self._seq_clock_count=0;self.arp_on=False;self._seq_active_notes=set();self._seq_noteoff_jobs={};self._seq_last_clock_time=None;self._seq_clock_interval=0.020833;self._rx_bank=0;self.hardware_names={};self._catalog_slot=0;self._catalog_active=False;self._catalog_job=None;self._catalog_timeout_job=None;self._catalog_retry=0;self._hw_refresh_job=None;self._hw_name_job=None;self._hw_seq_job=None;self._hw_seq_timeout_job=None;self._hw_seq_slot=None;self._hw_seq_pages={};self._hw_seq_expected_page=None;self._last_state_dump=None;self.sequence_origin='HARDWARE_STATE_ONLY';self.live_delay=int(self.settings.get('live_delay',0));self.live_playing=False;self.live_countdown_remaining=0;self._live_countdown_job=None
  self.values={}
  self.env_gate=False;self.env_release=False;self.env_phase_start=0.0;self.env_level_at_release=0.0;self.env_release_levels={'FENV':0.0,'AENV':0.0};self.anim_values={};self.filter_link=64;self._numeric_entry=None;self._anim_last=time.monotonic();self._anim_job=None;self._env_hover=None
  self._defaults();self.midi=MidiEngine(self._midi_rx);self._midi_inputs=[];self._midi_outputs=[];self._midi_apply_busy=False;self._midi_apply_result=queue.Queue();self._midi_ports_busy=False;self._midi_ports_result=queue.Queue();self._midi_close_result=queue.Queue();self._midi_close_deadline=0.0;self._cc_last_sent={};self._cc_pending={};self._cc_jobs={};self._cc_interval=0.008;self._midi_rx_queue=queue.Queue();self._midi_rx_job=None;self._popup_clear_job=None
  self._aspect_adjusting=False;self._last_window_size=(w,h)
  self.canvas.bind('<Configure>',lambda e:self.redraw());self.canvas.bind('<Button-1>',self.click);self.canvas.bind('<Button-3>',self.right_click);self.canvas.bind('<Double-Button-1>',self.double_click);self.canvas.bind('<Motion>',self.hover_motion);self.canvas.bind('<B1-Motion>',self.motion);self.canvas.bind('<ButtonRelease-1>',self.release);self.canvas.bind('<MouseWheel>',self.wheel);self.bind('<KeyPress>',self.keypress)
  self.protocol('WM_DELETE_WINDOW',self.close)
  # Poll the thread-safe MIDI queue at 10 ms. High-rate CC bursts are coalesced to the latest value.
  self._midi_rx_job=self.after(10,self._drain_midi_rx)
  # v1.28: restore automatic MIDI connection to saved ports at startup.
  self.after(250,self._start_port_refresh)
  self.after(30,self._restore_session_preset)
 def _defaults(self):
  for k in CC:self.values[k]=64
  self.values.update({'F1_CUTOFF':127,'F1_RES':0,'F1_ENV':0,'F1_TRACK':0,'F2_CUTOFF':127,'F2_RES':0,'F2_ENV':0,'F2_TRACK':0,'OSC1_WAVE':42,'OSC2_WAVE':0,'OSC3_WAVE':0,'OSC1_TUNE':0,'OSC2_TUNE':0,'OSC3_TUNE':0,'OSC1_FINE':0,'OSC2_FINE':0,'OSC3_FINE':0,'LFO1_WAVE':0,'LFO2_WAVE':0,'OSC1_LEVEL':127,'OSC2_LEVEL':0,'OSC3_LEVEL':0,'NOISE_LEVEL':0,'GLIDE':0,'FENV_A':4,'FENV_D':20,'FENV_S':127,'FENV_R':20,'AENV_A':4,'AENV_D':20,'AENV_S':127,'AENV_R':20,'LFO1_RATE':45,'LFO2_RATE':60,'LFO1_FADE':0,'LFO2_FADE':0,'SWING':50,'FILTER_SPACING':0,'ARP_GATE':64,'SEQ_SWING':0})
  self.choice={'F1_MODE':0,'F2_MODE':0,'MOD_TYPE':0,'MOD_SUB':0,'DELAY_TYPE':3,'REVERB_TYPE':0,'VOICE':0,'LFO1_SHAPE':0,'LFO2_SHAPE':0,'ARP_MODE':0,'ARP_OCT':1,'SEQ_DIR':0,'LFO1_CURVE':0,'LFO2_CURVE':0}
  self.toggle={'SYNC2':False,'SYNC3':False,'RING':False,'FENV_LOOP':False,'FENV_RETRIG':False,'AENV_LOOP':False,'AENV_RETRIG':False,'LFO1_SYNC':False,'LFO1_RETRIG':False,'LFO2_SYNC':False,'LFO2_RETRIG':False,'ARP_HOLD':False,'DELAY_SYNC':False}
  
  for i in range(16):
   self.values[f'MAMT{i}']=0
   self.values[f'MFADE{i}']=0
  self.arp_trig=[True]*16
 def _refresh_midi_ports(self):
  # Explicit/manual refresh only. Never enumerate WinMM devices during application startup.
  try:self._midi_inputs=list(self.midi.inputs())
  except Exception:self._midi_inputs=[]
  try:self._midi_outputs=list(self.midi.outputs())
  except Exception:self._midi_outputs=[]
 def _start_port_refresh(self):
  if self._closing or self._midi_ports_busy:return
  self._midi_ports_busy=True;self.status='SCANNING MIDI PORTS…';self.redraw()
  def worker():
   try:ins=list(self.midi.inputs());outs=list(self.midi.outputs());err=''
   except Exception as e:ins=[];outs=[];err=str(e)
   self._midi_ports_result.put((ins,outs,err))
  threading.Thread(target=worker,daemon=True).start();self.after(50,self._poll_port_refresh)
 def _poll_port_refresh(self):
  if self._closing:return
  try:ins,outs,err=self._midi_ports_result.get_nowait()
  except queue.Empty:
   if self._midi_ports_busy:self.after(50,self._poll_port_refresh)
   return
  self._midi_ports_busy=False;self._midi_inputs=ins;self._midi_outputs=outs
  if not err:
   def uno_port(names):
    return next((n for n in names if str(n).strip().lower()=='uno synth pro'),next((n for n in names if 'uno synth pro' in str(n).lower()),''))
   inn=uno_port(ins);outn=uno_port(outs);changed=False
   if inn and self.settings.get('midi_in')!=inn:self.settings['midi_in']=inn;changed=True
   if outn and self.settings.get('midi_out')!=outn:self.settings['midi_out']=outn;changed=True
   self.settings['pr_change']=True
   if changed:storage.save_settings(self.settings);self.settings_dirty=False
   self.status='MIDI PORTS READY';self.redraw()
   if (inn or outn) and not self._midi_apply_busy:self._start_midi_connect(save=True,initial=True)
   return
  self.status=f'MIDI PORT SCAN FAILED — {err}';self.redraw()
 def _apply_ui_scale(self,value,save=True):
  sizes={'100%':(1200,750),'125%':(1440,900),'150%':(1600,1000)};value=str(value)
  if value not in sizes:value='100%'
  w,base_h=sizes[value]
  # Keep the SYNTH/SEQ design scale unchanged when the drop-down keyboard is open.
  # The window grows vertically by the keyboard design height instead of shrinking
  # the entire 1600x1000 interface to fit the extra panel.
  base_scale=min(w/BASE_W,base_h/BASE_H)
  h=round((BASE_H+(170 if self.keyboard_visible and self.page!='SETTINGS' else 0))*base_scale)
  sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
  self.geometry(f'{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}');self.resizable(False,False)
  self.settings['ui_scale']=value
  if save:storage.save_settings(self.settings)
  self.after_idle(self.redraw)
 def _show_scale_menu(self):
  m=self._dark_menu(self)
  cur=str(self.settings.get('ui_scale','100%'))
  for value in ('100%','125%','150%'):
   m.add_command(label=('✓  ' if value==cur else '    ')+value,command=lambda v=value:self._apply_ui_scale(v,save=True))
  # Anchor the popup to the actual scaled canvas position of the ⛶ button.
  px=self.winfo_rootx()+int(self.X(1496))
  py=self.winfo_rooty()+int(self.Y(8+34))+2
  try:m.tk_popup(px,py)
  finally:m.grab_release()
 def _mod_routes_for_dest(self,dest):
  out=[]
  for i in range(16):
   if self.values.get(f'MDST{i}')==dest:
    amt=int(self.values.get(f'MAMT{i}',0));src=str(self.values.get(f'MSRC{i}','SOURCE'))
    if amt:out.append((src,amt))
  return out

 def _show_mod_tooltip(self,x,y,routes):
  self._mod_tooltip_job=None
  if not routes:return
  lines=[f'{src}  {amt:+d}' for src,amt in routes]
  self._mod_tooltip=(x,y,'\n'.join(lines));self.redraw()

 def settings_dropdown(self,x,y,w,h,label,key,opts):
  self.dropdown(x,y,w,h,label,key,opts)
 def _display_setting(self,v):
  if v is True:return 'ON'
  if v is False:return 'OFF'
  return str(v)
 def _select_setting(self,key,value):
  self.settings[key]=value
  if key=='preview':self.preview=bool(value)
  if key=='pr_change':self.settings[key]=True
  if key=='ui_scale':self._apply_ui_scale(value,save=False)
  storage.save_settings(self.settings);self.settings_dirty=False
  if key in ('midi_in','midi_out','midi_in_channel','midi_out_channel','midi_controller'):
   self.status='APPLYING MIDI…';self.redraw();self._start_midi_connect(save=True,initial=False)
  else:self.status='Settings saved';self.redraw()
 def autoconnect(self):
  # Restore the previously working behaviour: connect saved MIDI IN/OUT automatically.
  if self._closing or self._midi_apply_busy:return
  inn=self.settings.get('midi_in','');outn=self.settings.get('midi_out','')
  if not inn and not outn:
   self.status='OFFLINE — select MIDI ports in SETTINGS once';self.redraw();return
  self._start_midi_connect(save=False,initial=True)
 def _start_midi_connect(self,save=False,initial=False):
  if self._closing or self._midi_apply_busy:return
  self._midi_apply_busy=True;self.status='CONNECTING MIDI…' if initial else 'APPLYING MIDI…';self.redraw()
  cfg=(self.settings.get('midi_in',''),self.settings.get('midi_out',''),self.settings.get('midi_in_channel',1),self.settings.get('midi_out_channel',1),self.settings.get('midi_controller','Off'))
  def worker():
   try:result=self.midi.connect(*cfg)
   except Exception as e:result=(False,str(e))
   self._midi_apply_result.put((result[0],result[1],save,initial))
  threading.Thread(target=worker,daemon=True).start();self.after(50,self._poll_midi_connect)
 def _poll_midi_connect(self):
  if self._closing:return
  try:ok,msg,save,initial=self._midi_apply_result.get_nowait()
  except queue.Empty:
   if self._midi_apply_busy:self.after(50,self._poll_midi_connect)
   return
  if save:storage.save_settings(self.settings);self.settings_dirty=False
  self._midi_apply_busy=False;self.status=('CONNECTED' if initial and ok else ('OFFLINE' if initial else ('MIDI APPLIED — CONNECTED' if ok else f'MIDI APPLY FAILED — {msg}')))
  self.redraw()
  if ok:self.after(80,self._initial_hardware_sync)
 def _initial_hardware_sync(self):
  if self._closing:return
  self.midi.read_state();self._start_hardware_catalog()
 def _start_hardware_catalog(self):
  if self._closing:return
  self._catalog_active=True;self._catalog_slot=1;self._catalog_retry=0
  if self._catalog_job is not None:
   try:self.after_cancel(self._catalog_job)
   except Exception:pass
  self._catalog_job=self.after(30,self._request_catalog_slot)
 def _request_catalog_slot(self):
  self._catalog_job=None
  if self._closing or not self._catalog_active:return
  if not (1<=self._catalog_slot<=256):
   self._catalog_active=False;self.status='HARDWARE catalog loaded';self.redraw();return
  self.midi.read_preset_name(self._catalog_slot)
  self._catalog_timeout_job=self.after(250,self._catalog_timeout)
 def _catalog_timeout(self):
  self._catalog_timeout_job=None
  if self._closing or not self._catalog_active:return
  if self._catalog_retry<1:
   self._catalog_retry+=1;self._catalog_job=self.after(20,self._request_catalog_slot)
  else:
   self._catalog_retry=0;self._catalog_slot+=1;self._catalog_job=self.after(5,self._request_catalog_slot)
 def _schedule_hardware_refresh(self,n=None):
  if n is not None:
   n=max(1,min(256,int(n)));self.preset.number=n;self.hardware_selected=n;self.preset_source='HARDWARE'
  self._cancel_hardware_sequence_read()
  for attr in ('_hw_refresh_job','_hw_name_job','_hw_seq_job'):
   job=getattr(self,attr,None)
   if job is not None:
    try:self.after_cancel(job)
    except Exception:pass
    setattr(self,attr,None)
  self._hw_refresh_job=self.after(8,self._request_current_state)
  self._hw_seq_job=self.after(40,lambda slot=self.hardware_selected:self._start_hardware_sequence_read(slot))
  self._hw_name_job=self.after(500,self._request_current_name)
 def _cancel_hardware_sequence_read(self):
  job=getattr(self,'_hw_seq_timeout_job',None)
  if job is not None:
   try:self.after_cancel(job)
   except Exception:pass
  self._hw_seq_timeout_job=None;self._hw_seq_slot=None;self._hw_seq_pages={};self._hw_seq_expected_page=None
 def _start_hardware_sequence_read(self,slot):
  self._hw_seq_job=None
  if self._closing or self.preset_source!='HARDWARE':return
  slot=max(1,min(256,int(slot)))
  if slot!=self.hardware_selected:return
  self._cancel_hardware_sequence_read();self._hw_seq_slot=slot;self._request_hardware_sequence_page(0)
 def _request_hardware_sequence_page(self,page):
  if self._closing or self._hw_seq_slot!=self.hardware_selected:return
  page=int(page)
  if not 0<=page<=4:return
  self._hw_seq_expected_page=page
  if not self.midi.read_preset_page(self._hw_seq_slot,page):
   self._cancel_hardware_sequence_read();return
  self._hw_seq_timeout_job=self.after(500,self._hardware_sequence_timeout)
 def _hardware_sequence_timeout(self):
  self._hw_seq_timeout_job=None;self._hw_seq_slot=None;self._hw_seq_pages={};self._hw_seq_expected_page=None
  if self.preset_source=='HARDWARE':self.status=f'HARDWARE {self.hardware_selected:03d} — sequence read timeout';self.redraw()
 def _accept_hardware_sequence_page(self,data):
  parsed=parse_0x29_response(data,self._hw_seq_slot)
  if parsed is None:return False
  page,payload=parsed
  if self._hw_seq_slot is None or self._hw_seq_slot!=self.hardware_selected:return True
  if page!=self._hw_seq_expected_page:return True
  if self._hw_seq_timeout_job is not None:
   try:self.after_cancel(self._hw_seq_timeout_job)
   except Exception:pass
   self._hw_seq_timeout_job=None
  self._hw_seq_pages[page]=bytes(payload)
  if page<4:
   self._request_hardware_sequence_page(page+1);return True
  try:
   apply_to_sequence(self.preset.sequence,{p:self._hw_seq_pages[p] for p in range(1,5)})
   self._autofit_sequence_note_view()
   self.sequence_origin='HARDWARE_0x29'
   self.status=f'HARDWARE {self.hardware_selected:03d} — 64-step sequence read'
  except Exception:
   logger.exception('Failed to decode hardware 0x29 sequence pages');self._set_hardware_sequence_unavailable(reset=False);self.status='HARDWARE sequence decode failed'
  finally:
   self._hw_seq_slot=None;self._hw_seq_pages={};self._hw_seq_expected_page=None
  self.redraw();return True
 def _request_current_state(self):
  self._hw_refresh_job=None
  if not self._closing:self.midi.read_state()
 def _request_current_name(self):
  self._hw_name_job=None
  if not self._closing:self.midi.read_preset_name(self.hardware_selected)
 def _hardware_label(self,n):
  n=max(1,min(256,int(n)));name=self.hardware_names.get(n,'').strip()
  return f'{n:03d}  {name}' if name else f'{n:03d}'
 def _design_height(self):
  # Keyboard is part of the layout, never an overlay: opening it extends the design area.
  return BASE_H+(170 if self.keyboard_visible and self.page!='SETTINGS' else 0)
 def _on_window_configure(self,e):
  # Kept as a no-op for compatibility; forced geometry correction caused resize jitter.
  return
 def _clear_aspect_adjusting(self):
  self._aspect_adjusting=False

 def _restore_session_preset(self):
  """Restore editor selection/state only; never transmit MIDI during startup restore."""
  try:
   src=str(self.settings.get('last_preset_source','HARDWARE')).upper()
   if src=='LOCAL':
    raw=self.settings.get('last_local_preset','');path=Path(raw) if raw else None
    if path and path.exists():
     self.preset_source='LOCAL';self.lib_selected=path;self.preset_folder=path.parent;self.lib_panel_folder[0]=path.parent
     self.load_local_preset(path,preview=False);self.status=f'RESTORED LOCAL: {path.name}';return
   n=max(1,min(256,int(self.settings.get('last_hardware_preset',1))))
   self.hardware_selected=n;self.preset.number=n;self.preset_source='HARDWARE';self._set_hardware_sequence_unavailable(reset=True);self.status=f'RESTORED HARDWARE {n:03d} — no MIDI sent';self.redraw()
  except Exception:
   logger.exception('Failed to restore previous preset selection')
 def close(self):
  # Keep Tk alive while WinMM closes so callbacks cannot race a destroyed window.
  if self._closing:return
  self._closing=True
  if self.live_editor is not None:self.live_editor.close();self.live_editor=None
  self._flush_pending_cc()
  self._cancel_live_countdown();self._clock_master_stop()
  if self._anim_job is not None:
   try:self.after_cancel(self._anim_job)
   except Exception as e:logger.debug('after_cancel failed during shutdown: %s',e)
   self._anim_job=None
  try:
   self.settings['keyboard_visible']=self.keyboard_visible;self.settings['live_delay']=self.live_delay;self.settings['live_slots']=list(self.live_slots);self.settings['last_preset_source']=self.preset_source;self.settings['last_hardware_preset']=int(self.hardware_selected);self.settings['last_local_preset']=(str(self.lib_selected) if self.preset_source=='LOCAL' and self.lib_selected else '');storage.save_settings(self.settings)
  except Exception:logger.exception('Failed to save settings during shutdown')
  self.midi.on_message=None
  try:self.withdraw()
  except tk.TclError as e:logger.debug('withdraw failed during shutdown: %s',e)
  self._midi_close_deadline=time.monotonic()+1.5
  threading.Thread(target=self._close_midi_worker,daemon=True).start()
  self.after(20,self._poll_midi_close)
 def _close_midi_worker(self):
  err=None
  try:self.midi.close()
  except Exception as e:err=e;logger.exception('MIDI shutdown failed')
  finally:self._midi_close_result.put(err)
 def _poll_midi_close(self):
  try:self._midi_close_result.get_nowait();done=True
  except queue.Empty:done=False
  if done or time.monotonic()>=self._midi_close_deadline:
   if not done:logger.warning('MIDI shutdown timed out; closing UI')
   try:self.destroy()
   except tk.TclError:pass
   return
  self.after(20,self._poll_midi_close)
 def X(self,x):return self.ox+x*self.scale
 def Y(self,y):return self.oy+y*self.scale
 def S(self,v):return max(1,v*self.scale)
 def rect(self,x,y,w,h,fill=PANEL,outline=EDGE,width=1,r=0):
  fill=ui_theme.color(fill);outline=ui_theme.color(outline)
  self.canvas.create_rectangle(self.X(x),self.Y(y),self.X(x+w),self.Y(y+h),fill=fill,outline=outline,width=self.S(width))
 def play_indicator(self,x,y,w,h):
  # Deliberately unobtrusive playhead: a single low-contrast vertical line.
  self.line(x+w/2,y,x+w/2,y+h,'#59636a',1)
 def text(self,x,y,s,size=12,fill=TEXT,anchor='nw',bold=False):
  fill=ui_theme.color(fill)
  self.canvas.create_text(self.X(x),self.Y(y),text=s,fill=fill,anchor=anchor,font=('Segoe UI',max(7,int(size*self.scale)),'bold' if bold else 'normal'))
 def vlabel(self,x,y,s,size=8,fill=MUTED,anchor='n',bold=False):
  fill=ui_theme.color(fill)
  # For 90-degree labels Tk's 'n' anchor centers the rotated bbox around y.
  # 'ne' pins the top edge of the rotated label to y, matching the fader-line top exactly.
  if anchor=='n': anchor='ne'
  self.canvas.create_text(self.X(x),self.Y(y),text=s,fill=fill,anchor=anchor,angle=90,font=('Segoe UI',max(7,int(size*self.scale)),'bold' if bold else 'normal'))
 def asset_icon(self,path,x,y,w,h):
  if not PIL_OK:return
  try:
   img=Image.open(path).convert('RGBA')
   tw=max(1,int(round(w*self.scale)));th=max(1,int(round(h*self.scale)))
   img.thumbnail((tw,th),Image.Resampling.LANCZOS)
   ph=ImageTk.PhotoImage(img);self._graph_images.append(ph)
   self.canvas.create_image(self.X(x+w/2),self.Y(y+h/2),image=ph,anchor='center')
  except Exception:pass
 def _aa_circle_image(self,color,diameter,outline=None,outline_width=0,scale_with_ui=True,owner=None):
  if not PIL_OK:return None
  try:
   scale=self.scale if scale_with_ui else 1.0;d=max(5,int(round(diameter*scale)));ss=4
   img=Image.new('RGBA',(d*ss,d*ss),(0,0,0,0));dr=ImageDraw.Draw(img)
   ow=max(0,int(round(outline_width*ss)))
   box=(ow//2,ow//2,d*ss-1-ow//2,d*ss-1-ow//2)
   dr.ellipse(box,fill=color,outline=outline,width=ow if outline and ow else 1)
   img=img.resize((d,d),Image.Resampling.LANCZOS);ph=ImageTk.PhotoImage(img)
   if owner is not None:
    if not hasattr(owner,'_tag_images'):owner._tag_images=[]
    owner._tag_images.append(ph)
   else:self._graph_images.append(ph)
   return ph
  except Exception:return None
 def _draw_aa_circle(self,cx,cy,diameter,color,outline=None,outline_width=0):
  ph=self._aa_circle_image(color,diameter,outline,outline_width,True)
  if ph:self.canvas.create_image(self.X(cx),self.Y(cy),image=ph,anchor='center')
  else:
   r=diameter/2;self.canvas.create_oval(self.X(cx-r),self.Y(cy-r),self.X(cx+r),self.Y(cy+r),fill=color,outline=outline or '')
 def line(self,x1,y1,x2,y2,fill=EDGE,width=1):self.canvas.create_line(self.X(x1),self.Y(y1),self.X(x2),self.Y(y2),fill=ui_theme.color(fill),width=self.S(width))
 def hitbox(self,x,y,w,h,kind,key=None,data=None):self.hit.append((x,y,w,h,kind,key,data))
 def button(self,x,y,w,h,label,active=False,action=None,key=None,size=11):
  transport=ui_theme.TOKENS[ui_theme.current]['play' if label.startswith(('PLAY','STOP')) else 'rec'] if label.startswith(('PLAY','STOP','REC')) else None
  self.rect(x,y,w,h,transport if transport and active else (ORANGE2 if active else PANEL2),transport or (ORANGE if active else EDGE));self.text(x+w/2,y+h/2,label,size,MUTED if label=='Dupl' and action is None else ('#101418' if transport and active else (transport or (ORANGE if active else TEXT))),'center',True);self.hitbox(x,y,w,h,'action',key,action)
 def checkbox(self,x,y,label,key):
  active=bool(self.toggle.get(key,False));box=16
  self.rect(x,y,box,box,'#11171a',ORANGE if active else EDGE)
  if active:self.text(x+box/2,y+box/2,'✓',10,ORANGE,'center',True)
  self.text(x+box+7,y+box/2,label,9,TEXT,'w',True);self.hitbox(x,y,box+7+max(34,len(label)*8),box,'action',key,lambda:self.toggle_param(key))
 def dropdown(self,x,y,w,h,label,key,opts):
  # Inline canvas drop-down. Selection is direct; values are never cycled by click.
  self.rect(x,y,w,h,'#11171a',EDGE);self.text(x+10,y+h/2,label,11,TEXT,'w');self.text(x+w-12,y+h/2,'▼',9,ORANGE,'center');self.hitbox(x,y,w,h,'choice',key,opts)
 def cycler(self,x,y,w,h,label,key,opts):
  # SETTINGS selector: enumerate values with left/right arrows; no drop-down menu.
  aw=38
  self.rect(x,y,w,h,'#11171a',EDGE)
  self.rect(x,y,aw,h,PANEL2,EDGE);self.rect(x+w-aw,y,aw,h,PANEL2,EDGE)
  self.text(x+aw/2,y+h/2,'◀',11,ORANGE,'center',True)
  self.text(x+w-aw/2,y+h/2,'▶',11,ORANGE,'center',True)
  self.text(x+w/2,y+h/2,label,11,TEXT,'center')
  self.hitbox(x,y,aw,h,'choice_dir',key,(opts,-1))
  self.hitbox(x+aw,y,w-2*aw,h,'choice_dir',key,(opts,1))
  self.hitbox(x+w-aw,y,aw,h,'choice_dir',key,(opts,1))
 @staticmethod
 def _vertical_fader_geometry(x,top,height):
  return {'top':top,'bottom':top+height,'height':height,'label_x':x-12,'label_y':top+height/2}
 def slider(self,x,y,w,label,key,lo=0,hi=127,bipolar=False,vertical=False,show_label=True):
  v=self.values.get(key,lo);t=(v-lo)/(hi-lo) if hi!=lo else 0;t=clamp(t,0,1)
  if show_label and not vertical:self.text(x,y-18,label,10,MUTED)
  # Thin blue modulation overlay when a Matrix route targets this visible control.
  dest_names={'OSC1_TUNE':'Osc 1 Tune','OSC1_WAVE':'Osc 1 Wave','OSC1_LEVEL':'Osc 1 Level','OSC2_TUNE':'Osc 2 Tune','OSC2_WAVE':'Osc 2 Wave','OSC2_LEVEL':'Osc 2 Level','FM12':'Osc 2 FM Amount','OSC3_TUNE':'Osc 3 Tune','OSC3_WAVE':'Osc 3 Wave','OSC3_LEVEL':'Osc 3 Level','FM13':'Osc 3 FM Amount','NOISE_LEVEL':'Noise level','F1_CUTOFF':'Filter 1 Cutoff','F1_RES':'Filter 1 Res','F2_CUTOFF':'Filter 2 Cutoff','F2_RES':'Filter 2 Res','FILTER_SPACING':'Filter Spacing','LFO1_WAVE':'LFO 1 Wave','LFO1_RATE':'LFO 1 Rate','LFO2_WAVE':'LFO 2 Wave','LFO2_RATE':'LFO 2 Rate','F1_ENV':'Filter 1 Env Amount','F2_ENV':'Filter 2 Env Amount','DRIVE':'Drive Amount','DELAY_AMOUNT':'Delay Amount','REV_AMOUNT':'Reverb Amount','MOD_AMOUNT':'Mod Amount'}
  dn=dest_names.get(key);routes=self._mod_routes_for_dest(dn) if dn else [];mod_amt=sum(a for _,a in routes)
  if vertical:
   g=self._vertical_fader_geometry(x,y,w);h=g['height']
   if label:self.vlabel(g['label_x'],g['label_y'],label,8,MUTED,'center',True)
   self.line(x+6,y,x+6,y+h,EDGE,3)
   if bipolar:
    c=y+h/2;end=y+h*(1-t);self.line(x+6,c,x+6,end,ORANGE,3)
   else:
    yy=y+h*(1-t);self.line(x+6,yy,x+6,y+h,ORANGE,3)
   
   if mod_amt:
    zero=y+h/2;end=clamp(zero-clamp(mod_amt/64,-1,1)*(h/2),y,y+h);self.line(x+10,zero,x+10,end,BLUE,2)
   self.hitbox(x-7,y,26,h,'slider',key,(lo,hi,True,bipolar))
   if mod_amt:self.hitbox(x+7,min(zero,end)-4,8,abs(end-zero)+8,'modamount',key,(dn,routes))
  else:
   self.line(x,y+4,x+w,y+4,EDGE,3)
   if bipolar:
    c=x+w/2;end=x+w*t;self.line(c,y+4,end,y+4,ORANGE,3)
   else:self.line(x,y+4,x+w*t,y+4,ORANGE,3)
   if mod_amt:
    zero=x+w/2;end=clamp(zero+clamp(mod_amt/64,-1,1)*(w/2),x,x+w);self.line(zero,y+1,end,y+1,BLUE,2)
   self.hitbox(x,y-8,w,24,'slider',key,(lo,hi,False,bipolar))
   if mod_amt:self.hitbox(min(zero,end)-4,y-3,abs(end-zero)+8,8,'modamount',key,(dn,routes))
 def _curve(self,pts,fill=ORANGE,width=2,smooth=True):
  # Canvas fallback only. Graph screens use supersampled Pillow rendering below.
  if pts:self.canvas.create_line(*pts,fill=ui_theme.color(fill),width=self.S(width),smooth=smooth,splinesteps=24,capstyle=tk.ROUND,joinstyle=tk.ROUND)
 def _filter_points(self,w,h,cut,res,mode,is_f2=False):
  # Approximate amplitude response for the UNO Synth Pro screen:
  # F1 = 2-pole OTA LP/HP (~12 dB/oct), F2 = 2-pole/4-pole LP (~12/24 dB/oct).
  c=clamp(cut/127,.02,.98);q=clamp(res/127,0,1);pts=[]
  bypass='BYPASS' in mode.upper();hp=(not is_f2) and mode.upper().startswith('HP');pole4=is_f2 and mode.upper().startswith('4P')
  steep=30 if pole4 else 16
  for i in range(260):
   xx=i/259
   if bypass:amp=.78
   elif hp:
    amp=.12+.72/(1+math.exp(-(xx-c)*steep));amp+=q*.18*math.exp(-((xx-c)/.04)**2)
   else:
    amp=.84-.72/(1+math.exp(-(xx-c)*steep));amp-=q*.18*math.exp(-((xx-c)/.04)**2)
   yy=1-clamp(amp,.05,.95);pts.append((6+xx*(w-12),6+yy*(h-12)))
  return pts
 def _draw_aa_graph(self,x,y,w,h,lines):
  # Real anti-aliasing: draw at 4x the final pixel size, then downsample.
  # Geometry is not rounded/smoothed; only edge rasterization is anti-aliased.
  if not PIL_OK:return False
  tw=max(2,int(round(w*self.scale)));th=max(2,int(round(h*self.scale)));ss=4
  img=Image.new('RGBA',(tw*ss,th*ss),(0,0,0,0));dr=ImageDraw.Draw(img)
  def rgb(hexv):
   hexv=ui_theme.color(hexv).lstrip('#');return tuple(int(hexv[i:i+2],16) for i in (0,2,4))+(255,)
  for pts,color,width in lines:
   if len(pts)<2:continue
   sp=[(int(px/w*tw*ss),int(py/h*th*ss)) for px,py in pts]
   dr.line(sp,fill=rgb(color),width=max(1,int(width*self.scale*ss)),joint='curve')
  img=img.resize((tw,th),Image.Resampling.LANCZOS)
  ph=ImageTk.PhotoImage(img);self._graph_images.append(ph)
  self.canvas.create_image(self.X(x),self.Y(y),image=ph,anchor='nw')
  return True
 def _env_seconds(self,raw,stage='A'):
  # Visual time model follows the documented 0..30 s envelope range.
  # Zero is instantaneous; values 1..127 are exponentially distributed from 0.1 ms to 30 s.
  r=max(0,min(127,int(round(raw))))
  if r<=0:return 0.0
  return 0.0001*((30.0/0.0001)**((r-1)/126.0))
 def _env_visual_norm(self,raw):
  """Nonlinear graph-only time mapping; MIDI/raw ADSR values are untouched."""
  sec=self._env_seconds(raw)
  if sec<=0:return 0.0
  return clamp(math.log1p(sec/0.020)/math.log1p(30.0/0.020),0.0,1.0)
 def _env_visual_raw(self,normv):
  q=clamp(float(normv),0.0,1.0)
  if q<=0:return 0
  sec=0.020*(math.exp(q*math.log1p(30.0/0.020))-1.0)
  if sec<=0.0001:return 1
  raw=1+126*math.log(sec/0.0001)/math.log(30.0/0.0001)
  return int(round(clamp(raw,1,127)))
 def _env_level(self,prefix,now=None):
  now=time.monotonic() if now is None else now
  A=self._env_seconds(self.values.get(prefix+'_A',0),'A');D=self._env_seconds(self.values.get(prefix+'_D',0),'D');S=self.values.get(prefix+'_S',127)/127;R=self._env_seconds(self.values.get(prefix+'_R',0),'R')
  t=max(0,now-self.env_phase_start)
  if self.env_gate:
   if A>0 and t<A:return t/A
   td=max(0,t-A)
   if D>0 and td<D:return 1-(1-S)*(td/D)
   return S
  if self.env_release:
   if R<=0:return 0
   return max(0,self.env_release_levels.get(prefix,self.env_level_at_release)*(1-t/R))
  return 0
 def _lfo_hz(self,n):
  raw=max(0,min(127,float(self.values.get(f'LFO{n}_RATE',0))))
  return 0.1*(1000.0**(raw/127.0))
 def _lfo_value(self,n,now=None):
  now=time.monotonic() if now is None else now;ph=(now*self._lfo_hz(n))%1.0;shape=min(7,int(max(0,min(127,self.values.get(f'LFO{n}_WAVE',0)))*8/128))
  if shape==0:return math.sin(ph*2*math.pi)
  if shape==1:return 1-4*abs(ph-.5)
  if shape==2:return ph*2-1
  if shape==3:return 1-ph*2
  if shape==4:return 1 if ph<.5 else -1
  if shape==5:return math.sin(ph*6*math.pi)*.65+math.sin(ph*14*math.pi)*.25
  if shape==6:return 1 if int(ph*8)%2 else -1
  return math.sin(ph*26*math.pi)*.45+math.sin(ph*58*math.pi)*.25
 def _matrix_mod_delta(self,dest,now=None):
  now=time.monotonic() if now is None else now;delta=0.0
  for i in range(16):
   if self.values.get(f'MDST{i}')!=dest:continue
   amt=float(self.values.get(f'MAMT{i}',0));src=self.values.get(f'MSRC{i}','')
   if src=='LFO 1':sv=self._lfo_value(1,now)
   elif src=='LFO 2':sv=self._lfo_value(2,now)
   elif src=='Filter Env':sv=self._env_level('FENV',now)
   elif src=='Amp Env':sv=self._env_level('AENV',now)
   elif src=='Mod Wheel':sv=float(self.values.get('MOD_WHEEL',0))/127.0
   else:continue
   delta+=sv*amt
  return delta
 def _has_live_modulation(self):
  if self.page!='SYNTH':return False
  for i in range(16):
   if self.values.get(f'MAMT{i}',0) and self.values.get(f'MDST{i}','OFF')!='OFF' and self.values.get(f'MSRC{i}') in ('LFO 1','LFO 2'):
    return True
  return False
 def _env_is_dynamic(self,now=None):
  now=time.monotonic() if now is None else now
  if self.env_gate:
   # During attack/decay the value is changing; once sustain is reached no timer is needed.
   a=max(self._env_seconds(self.values.get('FENV_A',0),'A'),self._env_seconds(self.values.get('AENV_A',0),'A'))
   d=max(self._env_seconds(self.values.get('FENV_D',0),'D'),self._env_seconds(self.values.get('AENV_D',0),'D'))
   return (now-self.env_phase_start) < (a+d)
  if self.env_release:
   r=max(self._env_seconds(self.values.get('FENV_R',0),'R'),self._env_seconds(self.values.get('AENV_R',0),'R'))
   if r<=0 or (now-self.env_phase_start)>=r:
    self.env_release=False
    return False
   return True
  return False
 def _ensure_animation(self):
  if self._closing or self._anim_job is not None:return
  if self._env_is_dynamic() or self._has_live_modulation():
   self._anim_job=self.after(33,self._animation_tick)
 def _animation_tick(self):
  self._anim_job=None
  if self._closing:return
  try:
   if not self.winfo_exists():return
  except Exception:return
  active=self._env_is_dynamic() or self._has_live_modulation()
  if active and self.page=='SYNTH':self.redraw()
  if active and not self._closing:self._anim_job=self.after(33,self._animation_tick)
 def graph(self,x,y,w,h,kind,key=None):
  # v1.33: graph content is drawn directly on the panel: no dark screen fill or border.
  lines=[]
  if kind=='osc':
   # One continuous morph for OSC1/2/3: Triangle -> Saw -> Square 50% -> PWM 98%.
   # The Saw->Square segment is interpolated continuously; there is no waveform jump.
   v=clamp(float(self.values.get(key,0))/127.0,0.0,1.0);pts=[]
   for i in range(260):
    xx=i/259;morph=v*3.0
    tri=1.0-4.0*abs(xx-0.5)
    saw=2.0*xx-1.0
    square=1.0 if xx<0.5 else -1.0
    if morph<1.0:
     t=morph;yy=tri*(1.0-t)+saw*t
    elif morph<2.0:
     t=morph-1.0;yy=saw*(1.0-t)+square*t
    else:
     duty=0.5+0.48*(morph-2.0);yy=1.0 if xx<duty else -1.0
    pts.append((6+xx*(w-12),h/2-yy*(h*.34)))
   lines.append((pts,ORANGE,2))
  elif kind=='lfo':
   v=self.values.get(key,0)/127;shape=min(7,int(v*8));pts=[]
   for i in range(240):
    xx=i/239;ph=xx*2*math.pi
    if shape==0:yy=math.sin(ph)
    elif shape==1:yy=2*abs(2*(xx-math.floor(xx+.5)))-1
    elif shape==2:yy=2*xx-1
    elif shape==3:yy=1-2*xx
    elif shape==4:yy=1 if xx<.5 else -1
    elif shape==5:yy=math.sin(ph*3)*.65+math.sin(ph*7)*.25
    elif shape==6:yy=(math.floor(xx*8)%2)*2-1
    else:yy=math.sin(ph*13)*.45+math.sin(ph*29)*.25
    pts.append((5+xx*(w-10),h/2-yy*(h*.32)))
   lines.append((pts,ORANGE,2))
  elif kind=='noise':
   # Deterministic visual-only noise preview; no extra parameter or MIDI mapping.
   pts=[]
   for i in range(160):
    xx=i/159;yy=(math.sin(i*12.9898)*43758.5453)%1.0;yy=(yy-.5)*1.55
    pts.append((5+xx*(w-10),h/2-yy*(h*.34)))
   lines.append((pts,ORANGE,1))
  elif kind=='env':
   A=self._env_visual_norm(self.values.get(key+'_A',0));D=self._env_visual_norm(self.values.get(key+'_D',0));S=self.values.get(key+'_S',127)/127;R=self._env_visual_norm(self.values.get(key+'_R',0))
   xa=.03+.27*A;xd=xa+.27*D;sx=(.69 if S>=.03 else xd);xr=sx+.27*R
   coords=[(.03,.90),(xa,.08),(xd,.10+.78*(1-S)),(sx,.10+.78*(1-S)),(xr,.90)]
   pts=[(5+xx*(w-10),5+yy*(h-10)) for xx,yy in coords];lines.append((pts,ORANGE,2))
  elif kind=='filter':
   now=time.monotonic();spacing=self.values.get('FILTER_SPACING',0);base1=self.values.get('F1_CUTOFF',127);base2=self.values.get('F2_CUTOFF',127)
   env=self._env_level('FENV',now);e1=self.values.get('F1_ENV',0);e2=self.values.get('F2_ENV',0)
   # Screen = result of modulation over time: direct Filter ENV plus supported Matrix sources.
   m1=self._matrix_mod_delta('Filter 1 Cutoff',now);m2=self._matrix_mod_delta('Filter 2 Cutoff',now)
   c1=clamp(base1+env*(e1*127.0/64.0 if e1>=0 else e1*127.0/63.0)+m1,0,127);c2=clamp(base2+spacing+env*(e2*127.0/64.0 if e2>=0 else e2*127.0/63.0)+m2,0,127)
   # Visual placement only: lower the response drawing ~2 mm on the 1100 px layout and
   # separate F1/F2 slightly so coincident curves remain individually readable.
   f1=self._filter_points(w,h,c1,self.values.get('F1_RES',0),FILTER1_MODES[self.choice['F1_MODE']],False)
   f2=self._filter_points(w,h,c2,self.values.get('F2_RES',0),FILTER2_MODES[self.choice['F2_MODE']],True)
   f1=[(px,clamp(py+8,3,h-3)) for px,py in f1]
   f2=[(px,clamp(py+18,3,h-3)) for px,py in f2]
   lines.append((f1,ORANGE,2));lines.append((f2,BLUE,2))
  if not self._draw_aa_graph(x,y,w,h,lines):
   # Pillow-free fallback; functional but without supersampled AA.
   for pts,color,width in lines:
    flat=[]
    for px,py in pts:flat.extend([self.X(x+px),self.Y(y+py)])
    self._curve(flat,color,width,False)
 def env_graph(self,x,y,w,h,key):
  self.graph(x,y,w,h,'env',key)
  A=self._env_visual_norm(self.values.get(key+'_A',0));D=self._env_visual_norm(self.values.get(key+'_D',0));S=self.values.get(key+'_S',127)/127;R=self._env_visual_norm(self.values.get(key+'_R',0))
  xa=.03+.27*A;xd=xa+.27*D;sx=(.69 if S>=.03 else xd);xr=sx+.27*R;sy=.10+.78*(1-S)
  coords=[(xa,.08),(xd,sy),(sx,sy),(xr,.90)]
  # Editing is point-only. Control points stay invisible until the pointer is over them
  # (or while the point is being dragged), leaving the envelope curve visually clean.
  # Sustain can be edited by dragging the horizontal S→R segment vertically.
  if S>=.03 and sx>xd:
   x1=x+5+xd*(w-10);x2=x+5+sx*(w-10);py=y+5+sy*(h-10)
   self.hitbox(x1,py-9,max(1,x2-x1),18,'envseg',key,(2,x,y,w,h,x1,py,x2,py))
  dragging=self.drag if self.drag and self.drag[4]=='envpoint' and self.drag[5]==key else None
  drag_idx=dragging[6][0] if dragging else None
  for idx,(xx,yy) in enumerate(coords):
   px=x+5+xx*(w-10);py=y+5+yy*(h-10)
   self.hitbox(px-11,py-11,22,22,'envpoint',key,(idx,x,y,w,h))
   if self._env_hover==(key,idx) or drag_idx==idx:
    r=4
    self.canvas.create_oval(self.X(px-r),self.Y(py-r),self.X(px+r),self.Y(py+r),fill=ui_theme.color(ORANGE),outline=ui_theme.color(ORANGE),width=0)
  # Separate live envelope indicator. This marker is visual only and never edits parameters.
  marker=self._env_marker_position(key,coords)
  if marker is not None:
   mx,my=marker;px=x+5+mx*(w-10);py=y+5+my*(h-10);r=2.8
   self.canvas.create_oval(self.X(px-r),self.Y(py-r),self.X(px+r),self.Y(py+r),fill=WHITE,outline=WHITE,width=0)
 def _env_marker_position(self,key,coords):
  if not (self.env_gate or self.env_release):return None
  now=time.monotonic();t=max(0.0,now-self.env_phase_start)
  A0=self._env_seconds(self.values.get(key+'_A',0),'A');D0=self._env_seconds(self.values.get(key+'_D',0),'D');R0=self._env_seconds(self.values.get(key+'_R',0),'R');A=0 if A0<=0 else max(A0,.020);D=0 if D0<=0 else max(D0,.020);R=0 if R0<=0 else max(R0,.020)
  S=clamp(float(self.values.get(key+'_S',127))/127.0,0.0,1.0)
  start=(.03,.90);attack=coords[0];decay=coords[1];sustain=coords[2];release=coords[3]
  def lerp(p0,p1,q):
   q=clamp(q,0.0,1.0);return (p0[0]+(p1[0]-p0[0])*q,p0[1]+(p1[1]-p0[1])*q)
  if self.env_gate:
   if A>0 and t<A:return lerp(start,attack,t/A)
   td=max(0.0,t-A)
   if D>0 and td<D:return lerp(attack,decay,td/D)
   # Sustain is a held horizontal line; indicator remains at its beginning.
   return decay
  if R<=0:return None
  level=clamp(self.env_release_levels.get(key,S),0.0,1.0)
  # Release starts from the actual envelope level at Note Off, not blindly from sustain.
  sy=.10+.78*(1-level);release_start=(sustain[0],sy)
  if t>=R:return None
  return lerp(release_start,release,t/R)
 def param_value(self,key):
  return self.values.get(key,0)
 def redraw(self):
  if self._closing:return
  if not self.winfo_exists():return
  self.canvas.delete('all');self.hit=[];self._graph_images=[];w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height());design_h=self._design_height();self.scale=min(w/BASE_W,h/design_h);self.ox=(w-BASE_W*self.scale)/2;self.oy=0
  self.rect(0,0,BASE_W,design_h,BG,BG);self.topbar()
  if self.page=='SYNTH':self.draw_synth()
  elif self.page=='ARP + SEQUENCER':self.draw_seq()
  elif self.page=='SONG':self.draw_live_creator()
  elif self.page=='LIBRARY':self.draw_library()
  else:self.draw_settings()
  if self.page!='SONG' and self.live_editor is not None:self.live_editor.place_forget()
  if self.keyboard_visible and self.page!='SETTINGS':self.draw_keyboard()
  if self.open_dropdown:self._draw_dropdown_overlay()
  if self.popup:self._draw_value_popup()
  if self._mod_tooltip:
   tx,ty,msg=self._mod_tooltip;lines=msg.split('\n');ww=max(120,max(len(a) for a in lines)*7+18);hh=18+len(lines)*17;self.rect(tx,ty,ww,hh,'#11171a',EDGE);[self.text(tx+9,ty+12+i*17,line,8,TEXT,'w') for i,line in enumerate(lines)]
  if getattr(self,'_toolbar_tip',None):
   tx,ty,msg=self._toolbar_tip;self.rect(tx,ty,100,25,PANEL2,EDGE);self.text(tx+8,ty+5,msg,9,TEXT)
  if self._numeric_entry:self._restore_numeric_entry_window()
  if self._lib_drag_started and self._lib_drag_pos:self._draw_library_drag_feedback()
  # Bottom MIDI service status intentionally hidden in the production UI.
 def topbar(self):
  self.rect(0,0,BASE_W,52,'#0d1113','#0d1113')
  x=12
  for p,w in [('SYNTH',95),('ARP + SEQUENCER',180),('LIBRARY',95),('SONG',80)]:self.button(x,8,w,34,'LIVE' if p=='SONG' else p,self.page==p,lambda p=p:self.set_page(p),size=11);x+=w+6
  if self.page in ('SYNTH','ARP + SEQUENCER'):
   rand_action=self.randomize_synth if self.page=='SYNTH' else self.seq_randomize
   init_action=self.init_patch if self.page=='SYNTH' else self.seq_clear_request
   self.button(590,8,104,34,'RANDOM',False,rand_action,size=9)
   self.button(700,8,34,34,'◀',False,lambda:self.change_preset(-1));self.button(740,8,190,34,self._preset_selector_label(),False,self.open_preset_tree,size=9);self.button(936,8,34,34,'▶',False,lambda:self.change_preset(1))
   self.button(982,8,72,34,'INIT',False,init_action,size=9)
  self.button(1066,8,100,34,'SAVE AS',False,self.save_local_preset_as,size=10)
  self.button(1174,8,82,34,'SAVE',False,self.save_local_preset,size=10);self.button(1260,8,82,34,'STORE',False,self.store_locked,size=10);self.button(1350,8,43,34,'⚙',self.page=='SETTINGS',lambda:self.set_page('SETTINGS'),key='Settings',size=16)
  self.button(1447,8,43,34,'◐',False,self.toggle_theme,key='Theme',size=16)
  self.button(1496,8,43,34,'⛶',False,self._show_scale_menu,size=15)
  self.keyboard_icon_button(1545,8,43,34)

 def keyboard_icon_button(self,x,y,w,h):
  active=self.keyboard_visible;self.rect(x,y,w,h,ORANGE2 if active else PANEL2,ORANGE if active else EDGE)
  ix=x+8;iy=y+8;iw=w-16;ih=h-15;kw=iw/3
  for i in range(3):self.rect(ix+i*kw,iy,kw,ih,WHITE if not active else '#ffd0a2','#555')
  self.rect(ix+kw*.72,iy,kw*.55,ih*.58,'#101214','#050505');self.rect(ix+kw*1.72,iy,kw*.55,ih*.58,'#101214','#050505')
  self.hitbox(x,y,w,h,'action',None,self.toggle_keyboard)
 def set_page(self,p):
  self.open_dropdown=None;self.page=p;self.redraw()
  if p=='SETTINGS':self._start_port_refresh()
  elif p=='SYNTH':self._ensure_animation()
 def draw_live_creator(self):
  if self.live_editor is None:
   from live_creator.ui.app import LiveCreator
   self.live_editor=LiveCreator(master=self)
   self.live_editor.apply_theme()
  top=self.Y(52);height=self.S(BASE_H-52)
  self.live_editor.place(x=self.X(0),y=top,width=self.S(BASE_W),height=height)
  self.live_editor.lift()
 def toggle_theme(self):
  previous=ui_theme.current;ui_theme.set_theme('light' if previous=='dark' else 'dark')
  self.settings['theme']=ui_theme.current;storage.save_settings(self.settings)
  ui_theme.recolor_widgets(self,previous)
  if self.live_editor is not None:self.live_editor.apply_theme()
  self.redraw()
 def toggle_keyboard(self):
  self.keyboard_visible=not self.keyboard_visible
  # Re-apply the current window preset so the keyboard gets its own vertical area
  # without changing the scale of the main interface.
  self._apply_ui_scale(self.settings.get('ui_scale','100%'),save=False)
  self.redraw()
 def _collect_params(self):
  # Local editor state only. Official opaque/binary .unosyp files remain binary-safe and are never rewritten by this path.
  return {'values':copy.deepcopy(self.values),'choice':copy.deepcopy(self.choice),'toggle':copy.deepcopy(self.toggle),'filter_link':self.filter_link}
 def _apply_params(self,params):
  if not isinstance(params,dict):return False
  if isinstance(params.get('values'),dict):self.values.update(copy.deepcopy(params['values']))
  if isinstance(params.get('choice'),dict):self.choice.update(copy.deepcopy(params['choice']))
  if isinstance(params.get('toggle'),dict):self.toggle.update(copy.deepcopy(params['toggle']))
  if 'filter_link' in params:self.filter_link=params['filter_link']
  return True
 def _preview_value_range(self,key):
  if key in ('OSC1_TUNE','OSC2_TUNE','OSC3_TUNE'):return (-24,24)
  if key in ('FILTER_SPACING','F1_ENV','F2_ENV'):return (-63,64)
  if key in ('F1_TRACK','F2_TRACK'):return (-200,200)
  if key.startswith('MAMT'):return (-64,64)
  return (0,127)
 def _send_local_preview(self):
  # Temporary current-buffer preview only. No Program Change and no permanent STORE/bulk write.
  skip={'BANK','MOD_WHEEL','F1_MODE','F2_MODE','MOD_TYPE','DELAY_TYPE','REVERB_TYPE','FILTER_LINK'}
  sent=0
  for key,val in list(self.values.items()):
   if key not in CC or key in skip:continue
   try:
    lo,hi=self._preview_value_range(key);self.midi.send_cc(CC[key],self._encode_cc_value(key,val,lo,hi));sent+=1
   except Exception:logger.exception('LOCAL preview CC failed for %s',key)
  for key,raws in (('F1_MODE',FILTER1_MODE_RAW),('F2_MODE',FILTER2_MODE_RAW),('MOD_TYPE',MOD_TYPE_RAW),('DELAY_TYPE',DELAY_TYPE_RAW),('REVERB_TYPE',REVERB_TYPE_RAW)):
   try:
    idx=max(0,min(len(raws)-1,int(self.choice.get(key,0))));self.midi.send_cc(CC[key],raws[idx]);sent+=1
   except Exception:logger.exception('LOCAL preview enum failed for %s',key)
  try:self.midi.send_cc(CC['FILTER_LINK'],max(0,min(127,int(self.filter_link))));sent+=1
  except Exception:logger.exception('LOCAL preview FILTER_LINK failed')
  for key,state in list(self.toggle.items()):
   if key in CC:
    try:self.midi.send_cc(CC[key],127 if state else 0);sent+=1
    except Exception:logger.exception('LOCAL preview toggle failed for %s',key)
  mt=max(0,min(2,int(self.choice.get('MOD_TYPE',0))));sub=max(0,int(self.choice.get('MOD_SUB',0)))
  try:
   if mt==0:self.midi.send_cc(CC['CHORUS_MODE'],[0,42,84][min(2,sub)]);sent+=1
   elif mt==1:self.midi.send_cc(CC['MOD_INTENSITY'],[0,127][min(1,sub)]);sent+=1
  except Exception:logger.exception('LOCAL preview MOD sub-mode failed')
  self.status=f'PREVIEW LOCAL: {self.preset.name} ({sent} live parameters)'
 def _binary_unosyp_preview_sysex(self,path):
  # v1.55 TEST path for official UNO Synth Pro binary .unosyp files.
  # External reverse-engineering evidence identifies command 0x36 as a current-buffer
  # load (not STORE). Keep this deliberately strict until our real hardware confirms it.
  try:data=Path(path).read_bytes()
  except OSError:return None
  # Known Pro files begin with 25 01 00 00 and provide bytes 4..0x128 inclusive.
  if len(data)<0x129 or data[:4]!=bytes((0x25,0x01,0x00,0x00)):return None
  payload=data[4:0x129]
  if len(payload)!=0x125 or any(b>0x7f for b in payload):return None
  return bytes((0xF0,0x00,0x21,0x1A,0x02,0x03,0x36,0x00,0x60))+payload+bytes((0xF7,))
 def _preview_binary_unosyp(self,path):
  msg=self._binary_unosyp_preview_sysex(path)
  if not msg:
   self.status='LOCAL PREVIEW: unsupported .unosyp binary format';self.redraw();return False
  if not self.midi.sysex(msg):
   self.status='LOCAL PREVIEW: UNO is not connected';self.redraw();return False
  self.lib_selected=Path(path);self.preset_source='LOCAL'
  self.status=f'PREVIEW LOCAL: {Path(path).stem} — 0x36 test load'
  # Pull the resulting current state back into the GUI; no Program Change and no STORE.
  self.after(120,self.midi.read_state);self.redraw();return True
 def load_local_preset(self,path=None,preview=False):
  path=Path(path or self.lib_selected) if (path or self.lib_selected) else None
  if not path:return False
  try:
   p=storage.load_preset(path);self.preset=p;self._apply_params(p.params);self.lib_selected=path;self.sequence_origin='LOCAL_JSON';self._autofit_sequence_note_view()
   if preview:self._send_local_preview()
   else:self.status=f'LOADED LOCAL: {path.name}'
   self.redraw();return True
  except (UnicodeDecodeError,json.JSONDecodeError,TypeError,ValueError):
   try:state=storage.load_binary_unosyp_state(path)
   except Exception:
    logger.exception('Binary .unosyp state decode failed for %s',path);state=None
   try:seq=storage.load_binary_unosyp_sequence(path)
   except Exception:
    logger.exception('Binary .unosyp sequence decode failed for %s',path);seq=None
   if state is not None or seq is not None:
    self.preset=Preset(name=Path(path).stem,sequence=(seq or Sequence()),source='local');self.lib_selected=path;self.preset_source='LOCAL';self.sequence_origin=('LOCAL_BINARY_1081' if seq is not None else 'LOCAL_STATE_ONLY');self._autofit_sequence_note_view()
    applied=0
    if state is not None:
     for cc,decoded in state.get('resolved',{}).items():
      if self._apply_state_cc(cc,decoded):applied+=1
     self._apply_extended_preset_fields(state.get('extended',{}))
    active=sum(1 for st in self.preset.sequence.steps if st.notes)
    self.status=(f'LOCAL PRESET: {applied} synth fields / {active} active sequence steps' if seq is not None else f'LOCAL PRESET: {applied} synth fields / sequence not decoded for this file variant')
    if preview:
     ok=self._preview_binary_unosyp(path)
     # Local sequence load succeeded independently of optional hardware synth preview.
     if not ok:
      self.status=((f'LOCAL PRESET: {applied} synth fields / {active} active sequence steps' if seq is not None else f'LOCAL PRESET: {applied} synth fields / sequence not decoded for this file variant')+' — hardware preview unavailable')
      self.redraw()
     return True
    self.redraw();return True
   if preview:return self._preview_binary_unosyp(path)
   self.status='Official/binary .unosyp selected — sequence format not decoded';self.redraw();return False
  except Exception as e:self._notify('Load preset',str(e),True);return False
 def init_patch(self):
  self.preset=Preset();self._defaults();self.status='INIT — default patch';self.redraw()
  # Send only validated live CC parameters; do not write permanent hardware memory.
  for key,val in list(self.values.items()):
   if key in CC and key not in ('BANK','MOD_WHEEL','F1_MODE','F2_MODE','MOD_TYPE','DELAY_TYPE','REVERB_TYPE') and not key.startswith('MAMT'):
    try:self.midi.send_cc(CC[key],self._encode_cc_value(key,val,-24 if key.startswith('OSC') and key.endswith('TUNE') else 0,24 if key.startswith('OSC') and key.endswith('TUNE') else 127))
    except Exception:logger.exception('INIT CC send failed for %s',key)
  for key,raws in (('F1_MODE',FILTER1_MODE_RAW),('F2_MODE',FILTER2_MODE_RAW),('MOD_TYPE',MOD_TYPE_RAW),('DELAY_TYPE',DELAY_TYPE_RAW),('REVERB_TYPE',REVERB_TYPE_RAW)):
   try:self.midi.send_cc(CC[key],raws[self.choice[key]])
   except Exception:logger.exception('INIT enum send failed for %s',key)
 def _rand_tri(self,lo,hi,mode=None):
  return int(round(random.triangular(lo,hi,(lo+hi)/2 if mode is None else mode)))
 def randomize_synth(self):
  # Musical randomizer: weighted ranges and correlated groups; sequence is intentionally untouched.
  keep_seq=self.preset.sequence
  # Oscillators: one strong source, secondary layers less likely to dominate.
  vals={
   'OSC1_WAVE':random.randint(0,127),'OSC2_WAVE':random.randint(0,127),'OSC3_WAVE':random.randint(0,127),
   'OSC1_TUNE':random.choice([-12,0,0,0,7,12]),'OSC2_TUNE':random.choice([-12,-7,0,0,7,12]),'OSC3_TUNE':random.choice([-12,0,0,12]),
   'OSC1_FINE':self._rand_tri(-12,12,0),'OSC2_FINE':self._rand_tri(-18,18,0),'OSC3_FINE':self._rand_tri(-18,18,0),
   'OSC1_LEVEL':self._rand_tri(85,127,118),'OSC2_LEVEL':self._rand_tri(0,112,55),'OSC3_LEVEL':self._rand_tri(0,100,35),'NOISE_LEVEL':self._rand_tri(0,45,5),
   'F1_CUTOFF':self._rand_tri(28,127,82),'F1_RES':self._rand_tri(0,95,22),'F1_ENV':self._rand_tri(-48,64,22),'F1_TRACK':self._rand_tri(-80,200,70),
   'F2_CUTOFF':self._rand_tri(35,127,90),'F2_RES':self._rand_tri(0,85,18),'F2_ENV':self._rand_tri(-42,64,18),'F2_TRACK':self._rand_tri(-60,200,60),'FILTER_SPACING':self._rand_tri(-40,40,0),
   'FENV_A':self._rand_tri(0,70,8),'FENV_D':self._rand_tri(5,100,35),'FENV_S':self._rand_tri(45,127,95),'FENV_R':self._rand_tri(3,105,28),
   'AENV_A':self._rand_tri(0,60,5),'AENV_D':self._rand_tri(5,100,28),'AENV_S':self._rand_tri(55,127,105),'AENV_R':self._rand_tri(3,100,25),
   'LFO1_WAVE':random.randint(0,127),'LFO2_WAVE':random.randint(0,127),'LFO1_RATE':self._rand_tri(5,110,42),'LFO2_RATE':self._rand_tri(5,110,48),
   'LFO1_FADE':self._rand_tri(0,90,12),'LFO2_FADE':self._rand_tri(0,90,12),'GLIDE':self._rand_tri(0,75,8),
   'DRIVE':self._rand_tri(0,80,12),'MOD_AMOUNT':self._rand_tri(0,90,25),'DELAY_AMOUNT':self._rand_tri(0,75,18),'REV_AMOUNT':self._rand_tri(0,80,24),
   'MOD_INTENSITY':self._rand_tri(5,105,45),'MOD_RATE':self._rand_tri(5,105,38),'DELAY_TIME':self._rand_tri(12,112,58),'DELAY_TIME_R':self._rand_tri(12,112,62),'DELAY_FEEDBACK':self._rand_tri(0,95,32),'DELAY_LPF':self._rand_tri(30,127,96),
   'REV_PRE':self._rand_tri(0,75,15),'REV_TIME':self._rand_tri(20,112,62),'REV_LOW':self._rand_tri(20,110,58),'REV_HIGH':self._rand_tri(20,110,52),'REV_SIZE':self._rand_tri(25,120,78),'REV_FILTER':self._rand_tri(25,127,90)
  }
  self.values.update(vals);self.choice['F1_MODE']=random.choices(range(5),weights=[5,3,2,1,0.3])[0];self.choice['F2_MODE']=random.choices(range(6),weights=[4,3,2,2,0.3,0.3])[0]
  self.choice['MOD_TYPE']=random.randrange(3);self.choice['MOD_SUB']=0;self.choice['DELAY_TYPE']=random.randrange(5);self.choice['REVERB_TYPE']=random.randrange(4)
  self.toggle['SYNC2']=random.random()<.18;self.toggle['SYNC3']=random.random()<.12;self.toggle['RING']=random.random()<.10;self.toggle['DELAY_SYNC']=random.random()<.35
  self.preset.sequence=keep_seq;self.preset.name='RANDOM';self.status='RANDOM — musical patch generated'
  # Send validated CCs without touching Matrix source/destination or sequencer.
  for key,val in vals.items():
   if key in CC:
    lo,hi=(0,127)
    if key in ('OSC1_TUNE','OSC2_TUNE','OSC3_TUNE'):lo,hi=-24,24
    elif key in ('F1_ENV','F2_ENV','FILTER_SPACING'):lo,hi=-63,64
    elif key in ('F1_TRACK','F2_TRACK'):lo,hi=-200,200
    try:self.midi.send_cc(CC[key],self._encode_cc_value(key,val,lo,hi))
    except Exception:pass
  for key,raws in (('F1_MODE',FILTER1_MODE_RAW),('F2_MODE',FILTER2_MODE_RAW),('MOD_TYPE',MOD_TYPE_RAW),('DELAY_TYPE',DELAY_TYPE_RAW),('REVERB_TYPE',REVERB_TYPE_RAW)):
   try:self.midi.send_cc(CC[key],raws[self.choice[key]])
   except Exception:pass
  for key in ('SYNC2','SYNC3','RING','DELAY_SYNC'):
   if key in CC:self.midi.send_cc(CC[key],127 if self.toggle[key] else 0)
  self.redraw()
 def seq_randomize(self):
  self.sequence_origin='SOFTWARE'
  # Scale-constrained random walk + density + humanized velocity/gate + smooth automation.
  seq=self.preset.sequence;ln=max(1,min(64,int(seq.length)));root=random.choice([36,48,48,60]);scale=random.choice(([0,2,3,5,7,8,10],[0,2,4,5,7,9,11],[0,3,5,7,10]))
  pool=sorted({root+12*octv+deg for octv in range(-1,3) for deg in scale if 24<=root+12*octv+deg<=84});idx=min(range(len(pool)),key=lambda i:abs(pool[i]-root)) if pool else 0;density=random.uniform(.52,.82)
  for i in range(64):
   st=seq.steps[i]
   if i>=ln:continue
   if random.random()>density:st.notes=[];st.velocity=random.randint(70,100);st.gate=random.randint(4,8);st.length=random.choice([.5,.75,1.0]);st.accent=0;st.tie=False;st.probability=random.randint(80,100);continue
   idx=max(0,min(len(pool)-1,idx+random.choices([-2,-1,0,1,2],weights=[1,4,6,4,1])[0]));note=pool[idx];st.notes=[note];st.velocity=max(1,min(127,int(random.gauss(98,13))));st.gate=random.randint(5,10);st.length=random.choice([.5,.75,1.0,1.0,1.25]);st.accent=random.randint(82,127) if random.random()<.18 else 0;st.tie=random.random()<.08;st.probability=random.randint(72,100)
  for lane in seq.automation:
   metadata=PARAMETERS.get(lane.get('parameter'))
   if lane.get('units')=='device-ui' and (metadata is None or metadata.minimum is None or metadata.status.startswith('PARTIAL')):continue
   vals=lane.setdefault('values',[64]*64);v=random.randint(38,90)
   for i in range(ln):v=max(8,min(119,v+random.randint(-14,14)));vals[i]=metadata.value(v/127) if lane.get('units')=='device-ui' else v
   lane['fine_values']=[[None]*4 for _ in range(64)]
  self.selected_seq_step=0;self.seq_hscroll=0;self.status='SEQUENCER RANDOM — notes + automation generated';self.redraw()
 def _preset_selector_label(self):
  if self.preset_source=='HARDWARE':
   n=self.preset.number or 1
   return f'[{n:03d}] ' + (self.hardware_names.get(n,'').strip() or str(self.preset.name or '').strip() or 'INIT')
  if self.lib_selected:
   try:
    p=Path(self.lib_selected); items=self._local_folder_presets(getattr(self,'preset_folder',p.parent)); num=items.index(p)+1 if p in items else 1
    return f'[{num:03d}] {p.stem}'
   except Exception:pass
  return str(self.preset.name or 'INIT')
 def _set_hardware_sequence_unavailable(self,reset=False):
  """Mark hardware preset data as 0x37 synth-state only; 64-step sequence is not read."""
  if reset:self.preset.sequence=Sequence()
  self.sequence_origin='HARDWARE_STATE_ONLY'
 def _autofit_sequence_note_view(self):
  # Reposition only after a sequence is loaded. Manual edits never call this helper.
  rows=22;lo_min=12;lo_max=96-rows+1
  notes=[int(n) for st in self.preset.sequence.steps for n in st.notes[:3] if 0 <= int(n) <= 127]
  if not notes:return
  mn,mx=min(notes),max(notes)
  # If the complete phrase fits, keep a small margin around it.
  if mx-mn+1 <= rows-6:
   low=mn-3
  else:
   # Widely separated notes: choose the 22-semitone window containing the most events.
   # Ties prefer a window closest to the note median, so one remote outlier cannot pull
   # the piano roll into a mostly empty octave range.
   ordered=sorted(notes);median=ordered[len(ordered)//2]
   candidates=[]
   for low in range(lo_min,lo_max+1):
    high=low+rows-1;count=sum(low <= n <= high for n in notes);center=low+(rows-1)/2
    candidates.append((count,-abs(center-median),low))
   low=max(candidates)[2]
  self.seq_note_low=max(lo_min,min(lo_max,int(round(low))))

 def _sequence_source_label(self):
  if self.sequence_origin=='LOCAL_BINARY_1081':return 'SEQUENCE SOURCE: LOCAL .unosyp — 64-STEP DATA DECODED'
  if self.sequence_origin=='LOCAL_JSON':return 'SEQUENCE SOURCE: LOCAL EDITOR PRESET'
  if self.sequence_origin=='LOCAL_STATE_ONLY':return 'SEQUENCE SOURCE: LOCAL .unosyp — SEQUENCE FORMAT NOT DECODED'
  if self.sequence_origin=='SOFTWARE':return 'SEQUENCE SOURCE: SOFTWARE EDITOR'
  if self.sequence_origin=='HARDWARE_0x29':return 'SEQUENCE SOURCE: HARDWARE 0x29 — 64-STEP DATA DECODED'
  return 'SEQUENCE SOURCE: HARDWARE 0x37 — 64 STEPS NOT READ'
 def _local_folder_presets(self,folder):
  try:
   folder=Path(folder);items=[]
   for p in folder.rglob('*.unosyp'):
    if not p.is_file():continue
    try:
     if p==storage.SONGS or storage.SONGS in p.parents:continue
    except Exception:pass
    items.append(p)
   return sorted(items,key=lambda p:(p.name.lower(),str(p).lower()))
  except Exception:
   logger.exception('Local preset recursive scan failed: %s',folder)
   return []
 def change_preset(self,d):
  if self.preset_source=='LOCAL' and self.preset_folder:
   items=self._local_folder_presets(self.preset_folder)
   if items:
    try:i=items.index(Path(self.lib_selected))
    except ValueError:i=0
    i=max(0,min(len(items)-1,i+d));self._select_local_from_tree(items[i]);return
  n=clamp((self.preset.number or 1)+d,1,256);changed=(self.preset_source!='HARDWARE' or self.hardware_selected!=n);self.preset.number=n;self.hardware_selected=n;self.preset_source='HARDWARE';self._set_hardware_sequence_unavailable(reset=changed)
  if self.settings.get('pr_change',True):self.midi.bank_program(n)
  self._schedule_hardware_refresh(n);self.redraw()
 def _dark_menu(self,parent=None):
  return tk.Menu(parent or self,tearoff=0,bg='#11171a',fg=TEXT,activebackground='#30363a',activeforeground=WHITE,selectcolor=ORANGE,bd=1,relief='solid',font=('Segoe UI',11))
 def open_preset_tree(self):
  m=self._dark_menu()
  hw=self._dark_menu(m)
  for a in range(1,257,32):
   sub=self._dark_menu(hw)
   for n in range(a,min(a+32,257)):sub.add_command(label=self._hardware_label(n),command=lambda n=n:self._select_hw_preset(n))
   hw.add_cascade(label=f'{a:03d}–{min(a+31,256):03d}',menu=sub)
  m.add_cascade(label='UnoSynth',menu=hw);m.add_separator()
  try:
   roots=storage.local_folders()
   for folder in roots:self._add_folder_menu(m,folder)
  except Exception:logger.exception('Preset tree build failed')
  try:m.tk_popup(self.winfo_pointerx(),self.winfo_pointery())
  finally:m.grab_release()
 def _add_folder_menu(self,parent,folder):
  folder=Path(folder);sub=self._dark_menu(parent);has=False
  # UI exposes only the first-level folder; presets from nested folders are flattened here.
  items=self._local_folder_presets(folder)
  for col,start in enumerate(range(0,len(items),20),1):
   target=sub if col==1 else self._dark_menu(parent)
   for num,fp in enumerate(items[start:start+20],start+1):
    target.add_command(label=f'[{num:03d}] {fp.stem}',command=lambda fp=fp:self._select_local_from_tree(fp));has=True
   if col>1: sub.add_cascade(label=f'{col}',menu=target)
  if has:parent.add_cascade(label=folder.name,menu=sub)
 def _select_hw_preset(self,n):
  n=max(1,min(256,int(n)));changed=(self.preset_source!='HARDWARE' or self.hardware_selected!=n);self.preset_source='HARDWARE';self.preset.number=n;self.hardware_selected=n;self._set_hardware_sequence_unavailable(reset=changed);self.midi.bank_program(n);self._schedule_hardware_refresh(n);self.status=f'HARDWARE {n:03d} → UNO — sequence not read';self.redraw()
 def _select_local_from_tree(self,path):
  path=Path(path);self.preset_source='LOCAL';self.lib_selected=path
  roots=storage.child_folders(storage.PRESETS);self.preset_folder=next((r for r in roots if r==path.parent or r in path.parents),path.parent)
  self.load_local_preset(path,preview=True);self.redraw()
 def read_state(self):self.midi.read_state();self.status='READ requested';self.redraw()
 def _ask_text(self,title,prompt,initial=''):
  result={'value':None};win=tk.Toplevel(self);win.title(title);win.configure(bg=ui_theme.color(BG));win.resizable(False,False);win.transient(self);win.grab_set();ww,hh=420,160;win.geometry(f'{ww}x{hh}+{self.winfo_rootx()+max(0,(self.winfo_width()-ww)//2)}+{self.winfo_rooty()+max(0,(self.winfo_height()-hh)//2)}')
  tk.Label(win,text=prompt,bg=BG,fg=TEXT,font=('Segoe UI',10)).place(x=22,y=20);ent=tk.Entry(win,bg='#0b0f11',fg=TEXT,insertbackground=ORANGE,relief='solid',bd=1,font=('Segoe UI',11));ent.place(x=22,y=50,width=376,height=32);ent.insert(0,str(initial));ent.selection_range(0,'end');ent.focus_set()
  def done(ok):result['value']=ent.get().strip() if ok else None;win.destroy()
  tk.Button(win,text='CANCEL',command=lambda:done(False),bg=PANEL2,fg=TEXT,activebackground='#273137',activeforeground=TEXT,relief='flat').place(x=218,y=105,width=84,height=32);tk.Button(win,text='OK',command=lambda:done(True),bg=ORANGE2,fg=TEXT,activebackground=ORANGE,activeforeground=BG,relief='flat').place(x=314,y=105,width=84,height=32);ent.bind('<Return>',lambda e:done(True));win.bind('<Escape>',lambda e:done(False));self.wait_window(win);return result['value']
 def _notify(self,title,message,error=False):
  win=tk.Toplevel(self);win.title(title);win.configure(bg=ui_theme.color(BG));win.resizable(False,False);win.transient(self);win.grab_set();ww,hh=480,170;win.geometry(f'{ww}x{hh}+{self.winfo_rootx()+max(0,(self.winfo_width()-ww)//2)}+{self.winfo_rooty()+max(0,(self.winfo_height()-hh)//2)}')
  tk.Label(win,text=str(message),bg=BG,fg=(RED if error else TEXT),justify='left',wraplength=430,font=('Segoe UI',10)).place(x=24,y=24,width=432,height=78);tk.Button(win,text='OK',command=win.destroy,bg=ORANGE2,fg=TEXT,activebackground=ORANGE,activeforeground=BG,relief='flat').place(x=370,y=116,width=84,height=32);win.bind('<Escape>',lambda e:win.destroy());self.wait_window(win)
 def _confirm(self,title,message):
  result={'ok':False};win=tk.Toplevel(self);win.title(title);win.configure(bg=ui_theme.color(BG));win.resizable(False,False);win.transient(self);win.grab_set();ww,hh=500,180;win.geometry(f'{ww}x{hh}+{self.winfo_rootx()+max(0,(self.winfo_width()-ww)//2)}+{self.winfo_rooty()+max(0,(self.winfo_height()-hh)//2)}')
  tk.Label(win,text=str(message),bg=BG,fg=TEXT,justify='left',wraplength=450,font=('Segoe UI',10)).place(x=24,y=22,width=452,height=86)
  def done(v):result['ok']=bool(v);win.destroy()
  tk.Button(win,text='CANCEL',command=lambda:done(False),bg=PANEL2,fg=TEXT,activebackground='#273137',activeforeground=TEXT,relief='flat').place(x=300,y=124,width=84,height=32);tk.Button(win,text='OK',command=lambda:done(True),bg=ORANGE2,fg=TEXT,activebackground=ORANGE,activeforeground=BG,relief='flat').place(x=392,y=124,width=84,height=32);win.bind('<Escape>',lambda e:done(False));self.wait_window(win);return result['ok']
 def save_local_preset(self):
  # Local SAVE always targets the default UNO Synth Pro preset folder.
  name=self._ask_text('Save preset','Preset name:',self.preset.name if self.preset.name not in ('INIT','RANDOM') else '')
  if not name:return
  p=copy.deepcopy(self.preset);p.name=name;p.params=self._collect_params()
  try:
   saved=storage.save_preset(p);self.preset.name=name;self.lib_selected=saved;self.status=f'SAVED LOCAL: {saved.name}';self.redraw()
  except Exception as e:self._notify('Save preset',str(e),True)
 def save_local_preset_as(self):
  # Standalone export: no project-folder binding or current working-file state.
  path=filedialog.asksaveasfilename(parent=self,title='Save preset as',initialdir=str(storage.PRESETS),initialfile=storage._safe(self.preset.name)+'.unosyp',defaultextension='.unosyp',filetypes=[('UNO editor preset','*.unosyp')],confirmoverwrite=False)
  if not path:return False
  path=Path(path)
  if path.exists() and not self._confirm('Overwrite file',f'Overwrite {path.name}?'):return False
  p=copy.deepcopy(self.preset);p.name=path.stem;p.params=self._collect_params()
  try:storage.save_working_preset(p,path)
  except Exception as e:self._notify('Save preset',str(e),True);return False
  self.status=f'SAVED AS: {path.name}';self.redraw();return True
 def store_locked(self):self._notify('STORE','Permanent preset write is intentionally locked until the 0x28 bulk-write format is fully validated on hardware.')
 def draw_synth(self):
  bottom=982
  # v1.31 SYNTH geometry refinement based on the v1.30 runtime layout preview.
  # Visual controls/behaviour come from the real v1.29 code. FX and MOD MATRIX below are retained verbatim.

  # ---- OSCILLATOR GROUP: OSC1/NOISE over OSC2/OSC3 ----
  lx,ly,lw=10,60,610;gap=8;cell_w=(lw-gap)/2;osc_bottom=525;row_gap=10
  cell_h=(osc_bottom-ly-row_gap)/2;inner_y=(cell_h-170)/2
  def osc_cell(x,y,w,h,n):
   self.rect(x,y,w,h);self.text(x+10,y+8,f'OSC {n}',12,TEXT,bold=True)
   gx,gy,gs=x+12,y+26+inner_y,112
   self.graph(gx,gy,gs,gs,'osc',f'OSC{n}_WAVE');self.hitbox(gx,gy,gs,gs,'osc_wave',f'OSC{n}_WAVE',(0,127))
   icon_path=Path(__file__).resolve().parent/'Assets'/'OSC_WAVE_MOUSE_ARROWS.png';self.asset_icon(icon_path,gx+38,gy+115,36,30)
   labs=[('TUNE',f'OSC{n}_TUNE',-24,24,True),('FINE',f'OSC{n}_FINE',-100,100,True)]
   if n>1:labs.append(('FM',f'FM1{n}',0,127,False))
   usable=w-145;step=usable/3
   # Keep identical horizontal fader spacing in OSC1/OSC2/OSC3.
   group_w=step*len(labs);start_x=x+143+(usable-group_w)/2
   for j,(lab,key,lo,hi,bip) in enumerate(labs):
    px=start_x+j*step+step*.48;fader_y=y+20;fader_h=h-40
    self.slider(px,fader_y,fader_h,lab,key,lo,hi,bip,vertical=True,show_label=False)
  def noise_cell(x,y,w,h):
   self.rect(x,y,w,h);self.text(x+10,y+8,'NOISE',12,TEXT,bold=True)
   fy=y+20;fh=h-40;btn_x=x+14;btn_w=62;btn_h=30;btn_gap=7;btn_y=y+42
   self.button(btn_x,btn_y,btn_w,btn_h,'RING',self.toggle['RING'],lambda:self.toggle_param('RING'),size=7)
   self.button(btn_x,btn_y+btn_h+btn_gap,btn_w,btn_h,'SYNC 2',self.toggle['SYNC2'],lambda:self.toggle_param('SYNC2'),size=7)
   self.button(btn_x,btn_y+2*(btn_h+btn_gap),btn_w,btn_h,'SYNC 3',self.toggle['SYNC3'],lambda:self.toggle_param('SYNC3'),size=7)
   specs=[('LEVEL 1','OSC1_LEVEL'),('LEVEL 2','OSC2_LEVEL'),('LEVEL 3','OSC3_LEVEL'),('NOISE','NOISE_LEVEL')]
   left=x+102;step=(w-112)/4
   for j,(lab,key) in enumerate(specs):
    px=left+j*step+step*.48;self.slider(px,fy,fh,lab,key,0,127,False,vertical=True,show_label=False)
  osc_cell(lx,ly,cell_w,cell_h,1)
  noise_cell(lx+cell_w+gap,ly,cell_w,cell_h)
  lower_y=ly+cell_h+row_gap
  osc_cell(lx,lower_y,cell_w,cell_h,2)
  osc_cell(lx+cell_w+gap,lower_y,cell_w,cell_h,3)

  # ---- FILTER: same full parameter set, new compact placement ----
  fx,fy,fw,fh=630,60,618,265
  self.rect(fx,fy,fw,fh);self.text(fx+fw/2,68,'FILTER',16,TEXT,'n',True)
  screen_x,screen_y,screen_w,screen_h=834,98,210,126
  self.graph(screen_x,screen_y,screen_w,screen_h,'filter')
  left_lines=(658,700,742,784);right_lines=(1092,1134,1176,1218)
  left_spec=[('CUT','F1_CUTOFF',0,127,False),('RES','F1_RES',0,127,False),('ENV','F1_ENV',-63,64,True),('KEY','F1_TRACK',-200,200,True)]
  right_spec=[('CUT','F2_CUTOFF',0,127,False),('RES','F2_RES',0,127,False),('ENV','F2_ENV',-63,64,True),('KEY','F2_TRACK',-200,200,True)]
  filter_fader_y=fy+34;filter_fader_h=168
  for line_x,(lab,key,lo,hi,bip) in zip(left_lines,left_spec):
   self.slider(line_x,filter_fader_y,filter_fader_h,lab,key,lo,hi,bip,vertical=True,show_label=False)
  for line_x,(lab,key,lo,hi,bip) in zip(right_lines,right_spec):
   self.slider(line_x,filter_fader_y,filter_fader_h,lab,key,lo,hi,bip,vertical=True,show_label=False)
  self.slider(screen_x,248,screen_w,'SPACING','FILTER_SPACING',-63,64,True)
  ctrl_y,ctrl_h=282,28;drop_w=174
  self.dropdown(left_lines[0]-6,ctrl_y,drop_w,ctrl_h,FILTER1_MODES[self.choice['F1_MODE']],'F1_MODE',FILTER1_MODES)
  self.dropdown(right_lines[-1]-drop_w+6,ctrl_y,drop_w,ctrl_h,FILTER2_MODES[self.choice['F2_MODE']],'F2_MODE',FILTER2_MODES)
  bgap=6;bw=(screen_w-bgap)/2
  self.button(screen_x,ctrl_y,bw,ctrl_h,'CUTOFF',self.filter_link==64,lambda:self.set_filter_link(64),size=9)
  self.button(screen_x+bw+bgap,ctrl_y,bw,ctrl_h,'CUT+RES',self.filter_link==127,lambda:self.set_filter_link(127),size=9)

  # ---- LFO 1 / LFO 2: two framed blocks side by side ----
  lfy=335;lfh=190;lfw=(618-gap)/2
  for n,x in ((1,630),(2,630+lfw+gap)):
   self.rect(x,lfy,lfw,lfh);self.text(x+10,lfy+8,f'LFO {n}',12,TEXT,'nw',True)
   gx,gy,gw,gh=x+10,lfy+36,142,86
   self.graph(gx,gy,gw,gh,'lfo',f'LFO{n}_WAVE');self.hitbox(gx,gy,gw,gh,'lfo_wave',f'LFO{n}_WAVE',(0,127))
   self.button(gx,lfy+152,66,28,'SYNC',self.toggle[f'LFO{n}_SYNC'],lambda n=n:self.toggle_param(f'LFO{n}_SYNC'),size=7)
   self.button(gx+72,lfy+152,70,28,'RETRIG',self.toggle[f'LFO{n}_RETRIG'],lambda n=n:self.toggle_param(f'LFO{n}_RETRIG'),size=7)
   rate_x=x+171;fade_x=x+205
   lfo_fader_y=lfy+34;lfo_fader_bottom=lfy+138;lfo_fader_h=lfo_fader_bottom-lfo_fader_y
   self.slider(rate_x,lfo_fader_y,lfo_fader_h,'RATE',f'LFO{n}_RATE',0,127,False,vertical=True,show_label=False)
   self.slider(fade_x,lfo_fader_y,lfo_fader_h,'FADE IN',f'LFO{n}_FADE',0,127,False,vertical=True,show_label=False)
   bx=x+238
   for j,lab in enumerate(('LIN','EXP','LOG')):self.button(bx,gy+j*38,54,30,lab,self.choice[f'LFO{n}_CURVE']==j,lambda n=n,j=j:self.set_choice(f'LFO{n}_CURVE',j),size=7)

  # ---- ENVELOPES + VOICE — v1.38 compact three-container row ----
  # The oscillator group ends at y=525, leaving an exact 10 px gap above this row.
  env_y=535;env_h=245;env_bottom=env_y+env_h
  env_gap=10
  f_x,f_w=10,500
  a_x,a_w=f_x+f_w+env_gap,500
  v_x,v_w=a_x+a_w+env_gap,218
  env_btn_y=env_bottom-10-28;env_btn_w=70;env_btn_h=28;env_btn_gap=8
  env_slider_y=env_y+28
  env_slider_bottom=env_btn_y-10;env_slider_h=env_slider_bottom-env_slider_y

  # FILTER ENV — same controls, compact horizontal placement.
  self.rect(f_x,env_y,f_w,env_h);self.text(f_x+f_w-10,env_y+10,'FILTER ENV',14,TEXT,'ne',True)
  f_slider_x=f_x+25;f_step=43
  f_graph_x,f_graph_y,f_graph_w,f_graph_h=f_x+205,572,275,135
  f_pair_w=env_btn_w*2+env_btn_gap;f_fader_center=((f_slider_x+6)+(f_slider_x+3*f_step+6))/2;f_btn_x=f_fader_center-f_pair_w/2
  for j,k in enumerate('ADSR'):self.slider(f_slider_x+j*f_step,env_slider_y,env_slider_h,k,'FENV_'+k,vertical=True)
  self.env_graph(f_graph_x,f_graph_y,f_graph_w,f_graph_h,'FENV');self.button(f_btn_x,env_btn_y,env_btn_w,env_btn_h,'LOOP',self.toggle['FENV_LOOP'],lambda:self.toggle_param('FENV_LOOP'),size=9);self.button(f_btn_x+env_btn_w+env_btn_gap,env_btn_y,env_btn_w,env_btn_h,'RETRIG',self.toggle['FENV_RETRIG'],lambda:self.toggle_param('FENV_RETRIG'),size=9)

  # AMP ENV — mirrored compact placement.
  self.rect(a_x,env_y,a_w,env_h);self.text(a_x+10,env_y+10,'AMP ENV',14,TEXT,'nw',True)
  a_graph_x,a_graph_y,a_graph_w,a_graph_h=a_x+20,572,275,135
  a_slider_x=a_x+320;a_step=43
  a_pair_w=env_btn_w*2+env_btn_gap;a_fader_center=((a_slider_x+6)+(a_slider_x+3*a_step+6))/2;a_btn_x=a_fader_center-a_pair_w/2
  self.env_graph(a_graph_x,a_graph_y,a_graph_w,a_graph_h,'AENV');self.button(a_btn_x,env_btn_y,env_btn_w,env_btn_h,'LOOP',self.toggle['AENV_LOOP'],lambda:self.toggle_param('AENV_LOOP'),size=9);self.button(a_btn_x+env_btn_w+env_btn_gap,env_btn_y,env_btn_w,env_btn_h,'RETRIG',self.toggle['AENV_RETRIG'],lambda:self.toggle_param('AENV_RETRIG'),size=9)
  for j,k in enumerate('ADSR'):self.slider(a_slider_x+j*a_step,env_slider_y,env_slider_h,k,'AENV_'+k,vertical=True)

  # VOICE — moved after FILTER ENV and AMP ENV. GLIDE is vertical; buttons compact.
  self.rect(v_x,env_y,v_w,env_h);self.text(v_x+10,env_y+10,'VOICE',14,TEXT,'nw',True)
  glide_x=v_x+24;glide_y=env_y+38;glide_h=env_h-58
  self.slider(glide_x,glide_y,glide_h,'GLIDE','GLIDE',vertical=True,show_label=False)
  voice_btn_w=100;voice_btn_h=36;voice_btn_x=v_x+v_w-20-voice_btn_w
  for j,lab in enumerate(['MONO','LEGATO','PARA']):self.button(voice_btn_x,env_y+52+j*48,voice_btn_w,voice_btn_h,lab,self.choice['VOICE']==j,lambda j=j:self.set_choice('VOICE',j),size=9)

  # ---- FX — v1.45 cumulative GUI + hardware-mode fixes ----
  fx_x,fx_w=1260,330;ix=1278;inner=294;col=137;gap=12;rx=ix+col+gap
  short_inner=inner*(2/3);short_inner_x=ix+(inner-short_inner)/2
  # DRIVE — unchanged controls; compact height retained.
  drive_y,drive_h=60,112
  self.rect(fx_x,drive_y,fx_w,drive_h);self.text(ix,drive_y+10,'DRIVE',11,bold=True)
  self.slider(short_inner_x,drive_y+48,short_inner,'DRIVE','DRIVE')
  self.text(ix,drive_y+84,'AUDIO IN',9,MUTED);self.button(1356,drive_y+72,94,28,'PRE FX',self.choice.get('AUDIO_IN',0)==0,lambda:self.set_choice('AUDIO_IN',0),size=9);self.button(1456,drive_y+72,116,28,'POST FX',self.choice.get('AUDIO_IN',0)==1,lambda:self.set_choice('AUDIO_IN',1),size=9)

  # MODULATION — top-level type is strictly 3 states; lower FX blocks can never be hidden by an invalid RX value.
  mod_y,mod_h=drive_y+drive_h+10,230
  self.rect(fx_x,mod_y,fx_w,mod_h);self.text(ix,mod_y+10,'MODULATION',11,bold=True)
  mod_btn_y=mod_y+28;mod_bw=90;mod_bg=12
  for j,lab in enumerate(['CHORUS','PHASER','FLANGER']):self.button(ix+j*(mod_bw+mod_bg),mod_btn_y,mod_bw,28,lab,self.choice['MOD_TYPE']==j,lambda j=j:self.set_fx_choice('MOD_TYPE',j,3),size=8)
  mt=max(0,min(2,int(self.choice.get('MOD_TYPE',0))))
  mod_sub={0:['SYNTH1','SYNTH2','STRINGS'],1:['COLOR1','COLOR2'],2:[]}[mt]
  if mod_sub:
   display_sub=max(0,min(self.choice.get('MOD_SUB',0),len(mod_sub)-1))
   sub_y=mod_y+64;sub_gap=10;sub_w=(inner-sub_gap*(len(mod_sub)-1))/len(mod_sub)
   for j,lab in enumerate(mod_sub):
    self.button(ix+j*(sub_w+sub_gap),sub_y,sub_w,28,lab,display_sub==j,lambda j=j:self.set_mod_sub(j),size=8)
  fy=mod_y+112
  if mt==0:
   self.slider(ix,fy,col,'INTENSITY','MOD_INTENSITY');self.slider(rx,fy,col,'RATE','MOD_RATE')
  elif mt==1:
   self.slider(short_inner_x,fy,short_inner,'RATE','MOD_RATE')
  else:
   self.slider(ix,fy,col,'DEPTH','MOD_DEPTH');self.slider(rx,fy,col,'FEEDBACK','MOD_FEEDBACK');self.slider(short_inner_x,fy+42,short_inner,'RATE','MOD_RATE')
  self.slider(short_inner_x,mod_y+204,short_inner,'AMOUNT','MOD_AMOUNT')

  # DELAY — two-row mode layout requested from hardware test.
  delay_y,delay_h=mod_y+mod_h+10,258
  self.rect(fx_x,delay_y,fx_w,delay_h);self.text(ix,delay_y+10,'DELAY',11,bold=True)
  dby=delay_y+28;dbw=90;dbg=12
  for j,lab in enumerate(['MONO','STEREO','DOUBLER']):self.button(ix+j*(dbw+dbg),dby,dbw,28,lab,self.choice['DELAY_TYPE']==j,lambda j=j:self.set_fx_choice('DELAY_TYPE',j,5),size=8)
  dby2=delay_y+64
  self.button(ix,dby2,dbw,28,'PING PONG',self.choice['DELAY_TYPE']==3,lambda:self.set_fx_choice('DELAY_TYPE',3,5),size=8)
  self.button(ix+dbw+dbg,dby2,dbw,28,'LCR',self.choice['DELAY_TYPE']==4,lambda:self.set_fx_choice('DELAY_TYPE',4,5),size=8)
  self.checkbox(ix+2*(dbw+dbg)+4,dby2+6,'SYNC','DELAY_SYNC')
  dy=delay_y+112;dt=max(0,min(4,int(self.choice.get('DELAY_TYPE',0))))
  if dt==0:
   self.slider(ix,dy,col,'TIME','DELAY_TIME');self.slider(rx,dy,col,'FEEDBACK','DELAY_FEEDBACK');self.slider(short_inner_x,dy+42,short_inner,'FILTER','DELAY_LPF')
  else:
   self.slider(ix,dy,col,'TIME L','DELAY_TIME');self.slider(rx,dy,col,'TIME R','DELAY_TIME_R');self.slider(ix,dy+42,col,'FEEDBACK','DELAY_FEEDBACK');self.slider(rx,dy+42,col,'FILTER','DELAY_LPF')
  # No reserved empty row: AMOUNT raised one row.
  self.slider(short_inner_x,delay_y+190,short_inner,'AMOUNT','DELAY_AMOUNT')

  # REVERB — four strict hardware types; no reserved empty row before AMOUNT.
  rev_y=delay_y+delay_h+10;rev_h=bottom-rev_y
  self.rect(fx_x,rev_y,fx_w,rev_h);self.text(ix,rev_y+10,'REVERB',11,bold=True)
  rev_labels=['HALL','PLATE','REVERSE','SPRING'];rbw=66;rbg=6;rby=rev_y+28
  for j,lab in enumerate(rev_labels):self.button(ix+j*(rbw+rbg),rby,rbw,28,lab,self.choice['REVERB_TYPE']==j,lambda j=j:self.set_fx_choice('REVERB_TYPE',j,4),size=8)
  ry=rev_y+92;rt=max(0,min(3,int(self.choice.get('REVERB_TYPE',0))))
  self.slider(ix,ry,col,'PRE-DELAY','REV_PRE');self.slider(rx,ry,col,'SIZE','REV_SIZE')
  self.slider(ix,ry+42,col,'TIME','REV_TIME');self.slider(rx,ry+42,col,'FILTER','REV_FILTER')
  if rt in (0,1):
   self.slider(ix,ry+84,col,'LOW TIME','REV_LOW');self.slider(rx,ry+84,col,'HIGH TIME','REV_HIGH')
  self.slider(short_inner_x,rev_y+rev_h-68,short_inner,'AMOUNT','REV_AMOUNT')

  # MOD MATRIX — v1.29, intentionally unchanged.
  my=790;mh=192;self.rect(10,my,1238,mh);self.text(24,my+10,'MOD MATRIX — 16 ROUTES',14,bold=True);self.text(90,my+38,'SOURCE',9,MUTED);self.text(420,my+38,'AMOUNT',9,MUTED);self.text(650,my+38,'DESTINATION',9,MUTED);self.text(1030,my+38,'FADE IN',9,MUTED)
  rowh=30;ctrlh=22;startrow=max(0,min(12,self.matrix_scroll))
  for vis,i in enumerate(range(startrow,startrow+4)):
   yy=my+56+vis*rowh;self.text(27,yy+ctrlh/2,f'{i+1:02}',8,MUTED,'w');self.dropdown(70,yy,250,ctrlh,self.values.get(f'MSRC{i}','SOURCE'),f'MSRC{i}',MATRIX_SOURCES);self.slider(350,yy+ctrlh/2-4,220,'',f'MAMT{i}',-64,64,True,show_label=False);self.dropdown(600,yy,315,ctrlh,self.values.get(f'MDST{i}','DESTINATION'),f'MDST{i}',MATRIX_DESTINATIONS);self.slider(945,yy+ctrlh/2-4,260,'',f'MFADE{i}',0,127,False,show_label=False)
  track_y=my+56;track_h=rowh*4;self.line(1228,track_y,1228,track_y+track_h,EDGE,3);thumb_h=track_h*4/16;thumb_y=track_y+(track_h-thumb_h)*(startrow/12 if 12 else 0);self.line(1228,thumb_y,1228,thumb_y+thumb_h,ORANGE,4)
 def draw_seq(self):
  # v1.26 — fixed-size step grid, synced horizontal scrolling, vertical note scroll,
  # polymetric STEPS 1..64, active/inactive shading, 12-note chromatic colors.
  bottom=982
  self.rect(10,60,295,bottom-60);self.text(28,78,'ARPEGGIATOR',15,bold=True)
  self.button(28,108,120,46,'ON',self.arp_on,self.toggle_arp_on);self.button(160,108,123,46,'HOLD',self.toggle['ARP_HOLD'],lambda:self.toggle_param('ARP_HOLD'))
  self.text(28,178,'MODE',9,MUTED);self.dropdown(112,166,171,38,ARP_MODES[self.choice['ARP_MODE']],'ARP_MODE',ARP_MODES)
  self.text(28,232,'RANGE',9,MUTED);self.dropdown(112,220,171,38,'1 OCT','ARP_RANGE',['1 OCT','2 OCT','3 OCT','4 OCT'])
  self.slider(72.5,390,170,'GATE','ARP_GATE',0,127);self.slider(72.5,450,170,'SWING','SWING',0,127)
  self.text(28,540,'PATTERN',10,bold=True)
  for i in range(16):
   r=i//8;c=i%8;self.button(28+c*32,562+r*46,27,38,str(i+1),self.arp_trig[i],lambda i=i:self.toggle_arp(i),size=8)
  # Small in-panel manual: informative, low contrast, no extra frame.
  self.text(157.5,676,'PATTERN QUICK GUIDE',8,MUTED,'center',True)
  self.text(157.5,700,'ON STEP  — note plays',8,MUTED,'center')
  self.text(157.5,720,'EMPTY STEP — MUTE',8,MUTED,'center')
  self.text(157.5,740,'Click 1–16 to toggle a step',8,MUTED,'center')

  sx,sy,sw=315,60,940;self.rect(sx,sy,sw,bottom-sy);self.text(333,78,'SEQUENCER',15,bold=True)
  # 16 fixed-width columns are visible. More steps never shrink the cells.
  kx,ky,kw,kh=324,118,74,398;grid_x=398;grid_w=830;visible=16;cw=grid_w/visible
  seq_len=max(1,min(64,int(self.preset.sequence.length)))
  self.seq_hscroll=max(0,min(self.seq_hscroll,max(0,64-visible)))
  first=self.seq_hscroll
  rows=22;rh=kh/rows
  # C0..C7 model, default lower visible note C2 (MIDI 36).
  self.seq_note_low=max(12,min(self.seq_note_low,96-rows+1));top_note=self.seq_note_low+rows-1
  self.rect(kx,ky,kw+grid_w,kh,'#10171a',EDGE)
  note_names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
  black_pc=(1,3,6,8,10)
  # Keyboard + row backgrounds. White-key rows are deliberately lighter.
  for r in range(rows):
   note=top_note-r;black=note%12 in black_pc;yy=ky+r*rh
   rowfill='#11181c' if black else '#1b2429'
   self.rect(grid_x,yy,grid_w,rh,rowfill,rowfill)
   self.rect(kx,yy,kw,rh,'#151a1d' if black else '#e7e9e9','#2b3236')
   if black:self.rect(kx,yy,kw*.55,rh,'#111517','#111517')
   self.text(kx+kw-7,yy+rh/2,f'{note_names[note%12]}{note//12-1}',7,'#222' if not black else TEXT,'e')
  # Active sequence steps are brighter; steps after STEPS remain visible but shaded.
  for col in range(visible):
   step=first+col;x=grid_x+col*cw
   if step>=seq_len:self.rect(x,ky,cw,kh,'#0a0e10','#0a0e10')
   elif col%2==0:self.rect(x,ky,cw,kh,'#202a2f','#263238')
  # PLAY indicator: highlight the current step column across Piano Roll.
  if self.seq_playing and first <= self.selected_seq_step < first+visible and self.selected_seq_step < seq_len:
   play_col=self.selected_seq_step-first;px=grid_x+play_col*cw
   self.play_indicator(px,ky,cw,kh)
  # Grid: every fourth step boundary is a little brighter.
  for col in range(visible+1):
   absolute=first+col
   major=(absolute%4==0)
   self.line(grid_x+col*cw,ky,grid_x+col*cw,ky+kh,'#56636a' if major else '#2d3a40',2 if major else 1)
  for r in range(rows+1):self.line(grid_x,ky+r*rh,grid_x+grid_w,ky+r*rh,'#344148' if r and (top_note-r+1)%12==0 else '#263238',1)
  # 12 chromatic note colors, repeating each octave; A is red.
  note_colors={9:'#e54848',10:'#ef7438',11:'#e6ad32',0:'#b9c93b',1:'#74bd4a',2:'#35b98b',3:'#35b9bd',4:'#4c8edb',5:'#6670d8',6:'#945dcc',7:'#c653bd',8:'#dc4f83'}
  for col in range(visible):
   sidx=first+col
   if sidx>=64:continue
   st=self.preset.sequence.steps[sidx]
   for n in st.notes[:3]:
    r=top_note-n
    if 0<=r<rows:
     x=grid_x+col*cw+1;ww=max(3,min(grid_x+grid_w-x,cw*max(1.0,float(st.length))-2));yy=ky+r*rh+2;clr=note_colors[n%12]
     selected=(self.selected_seq_note==(sidx,n));self.rect(x,yy,ww,rh-4,clr,WHITE if selected else clr,2 if selected else 1)
     if st.tie:self.line(x+ww,yy+(rh-4)/2,min(grid_x+grid_w,x+ww+cw*.35),yy+(rh-4)/2,clr,3)
  loaded_notes=[int(n) for st in self.preset.sequence.steps for n in st.notes[:3]]
  if loaded_notes and max(loaded_notes)>top_note:self.text(grid_x+grid_w-9,ky+7,'▲',8,MUTED,'ne',True)
  if loaded_notes and min(loaded_notes)<self.seq_note_low:self.text(grid_x+grid_w-9,ky+kh-7,'▼',8,MUTED,'se',True)
  self.hitbox(grid_x,ky,grid_w,kh,'pianoroll','SEQ',{'gx':grid_x,'gy':ky,'gw':grid_w,'gh':kh,'visible':visible,'first':first,'rows':rows,'top_note':top_note})
  # Visible vertical scrollbar for full C0..C7 range.
  vsx=1235;self.line(vsx,ky+4,vsx,ky+kh-4,EDGE,4);vrange=(96-rows+1)-12;thumbh=max(36,(kh-8)*rows/85);frac=(self.seq_note_low-12)/vrange if vrange else 0;vty=ky+4+((kh-8)-thumbh)*(1-frac);self.line(vsx,vty,vsx,vty+thumbh,ORANGE,5);self.hitbox(vsx-8,ky,16,kh,'seq_vscroll',None,{'y':ky,'h':kh,'thumb':thumbh,'range':vrange})
  for col in range(visible):self.text(grid_x+(col+.5)*cw,528,str(first+col+1),8,TEXT if first+col<seq_len else MUTED,'center')

  head_y=548;bx=grid_x
  for pnm in ('GATE','ACC','VELOCITY','LENGTH'):
   self.button(bx,head_y,98,42,pnm,self.seq_param==pnm,lambda pnm=pnm:self.set_seq_param(pnm),size=8);bx+=102
  self.button(1124,head_y,116,42,'TIE',False,self.toggle_selected_tie,size=8)
  py,ph=598,146;self.rect(grid_x,py,grid_w,ph,'#10171a',EDGE)
  for col in range(visible):
   sidx=first+col;x=grid_x+col*cw
   if sidx>=seq_len:self.rect(x,py,cw,ph,'#0a0e10','#0a0e10')
  # PLAY indicator: same current-step column in Step Parameter.
  if self.seq_playing and first <= self.selected_seq_step < first+visible and self.selected_seq_step < seq_len:
   play_col=self.selected_seq_step-first;px=grid_x+play_col*cw
   self.play_indicator(px,py,cw,ph)
  for col in range(visible+1):
   absolute=first+col;major=(absolute%4==0);self.line(grid_x+col*cw,py,grid_x+col*cw,py+ph,'#56636a' if major else '#263238',2 if major else 1)
  self.text(340,py+5,'100',8,TEXT);self.text(350,py+ph/2,'50',8,TEXT);self.text(358,py+ph-4,'0',8,TEXT,'sw')
  for col in range(visible):
   sidx=first+col;st=self.preset.sequence.steps[sidx]
   if self.seq_param=='GATE':t=clamp(st.gate/10,0,1)
   elif self.seq_param=='ACC':t=clamp(st.accent/127,0,1)
   elif self.seq_param=='VELOCITY':t=clamp(st.velocity/127,0,1)
   else:t=clamp((float(st.length)-0.5)/3.5,0,1)
   hh=max(3,t*(ph-8));self.rect(grid_x+col*cw+cw*.27,py+ph-4-hh,cw*.46,hh,ORANGE,ORANGE);self.hitbox(grid_x+col*cw,py,cw,ph,'seqbar',sidx,self.seq_param)
  for col in range(visible):self.text(grid_x+(col+.5)*cw,py+ph+14,str(first+col+1),8,TEXT if first+col<seq_len else MUTED,'center')

  my=770;bx=grid_x
  self.text(grid_x,my+21,'AUTOMATION',10,TEXT,'w')
  lane=self.automation_lane();target=lane['parameter'];metadata=PARAMETERS[target]
  self.dropdown(grid_x+140,my,240,42,target,'SEQ_TARGET',AUTOMATABLE)
  native=self.preset.sequence.native_automation
  if native.get('entry_count'):self.text(grid_x+395,my+21,f"Native: {native['entry_count']} entries — mapping PARTIAL",8,MUTED,'w')
  ay,ah=820,128;self.rect(grid_x,ay,grid_w,ah,'#10171a',EDGE);self.line(grid_x,ay+ah/2,grid_x+grid_w,ay+ah/2,'#435057',1)
  labels=metadata.scale_labels()
  for i,lab in enumerate(labels):self.text(grid_x-10,ay+i/max(1,len(labels)-1)*ah,lab,8,TEXT,'e')
  vals=lane.get('values',[None]*64);fine=lane.setdefault('fine_values',[[None]*4 for _ in range(64)])
  while len(fine)<64:fine.append([None]*4)
  for col in range(visible):
   sidx=first+col;x=grid_x+col*cw
   if sidx>=seq_len:self.rect(x,ay,cw,ah,'#0a0e10','#0a0e10')
  # PLAY indicator: same current-step column in the selected LINE automation lane.
  if self.seq_playing and first <= self.selected_seq_step < first+visible and self.selected_seq_step < seq_len:
   play_col=self.selected_seq_step-first;px=grid_x+play_col*cw
   self.play_indicator(px,ay,cw,ah)
  for col in range(visible+1):
   absolute=first+col;major=(absolute%4==0);self.line(grid_x+col*cw,ay,grid_x+col*cw,ay+ah,'#56636a' if major else '#263238',2 if major else 1)
  for col in range(visible):
   sidx=first+col;v=display_value(lane,vals[sidx] if sidx<len(vals) else None)
   if v is None or metadata.minimum is None:continue
   yy=ay+(1-clamp(metadata.fraction(v),0,1))*(ah-10)+5;self.rect(grid_x+col*cw+cw*.28,yy-3,cw*.44,6,ORANGE,ORANGE)
  self.hitbox(grid_x,ay,grid_w,ah,'modlane',self.seq_mod,{'gx':grid_x,'gy':ay,'gw':grid_w,'gh':ah,'visible':visible,'first':first})
  for col in range(visible):self.text(grid_x+(col+.5)*cw,ay+ah+13,str(first+col+1),8,TEXT if first+col<seq_len else MUTED,'center')
  # Shared horizontal scrollbar directly under Piano Roll; controls Piano Roll / Step Parameter / LINE automation together.
  hsy=538;self.line(grid_x,hsy,grid_x+grid_w,hsy,EDGE,4);thumbw=grid_w*visible/64;htx=grid_x+(grid_w-thumbw)*(first/(64-visible));self.line(htx,hsy,htx+thumbw,hsy,ORANGE,5);self.hitbox(grid_x,hsy-8,grid_w,16,'seq_hscroll',None,{'x':grid_x,'w':grid_w,'thumb':thumbw})

  rx=1265;rw=325;self.rect(rx,60,rw,bottom-60)
  self.button(rx+14,78,145,48,'PLAY ▶',self.seq_playing,self.toggle_seq_play);self.button(rx+166,78,145,48,'REC ●',self.seq_recording,self.toggle_seq_record)
  self.rect(rx+10,140,rw-20,118);self.button(rx+24,156,132,46,'Dupl',False,self.seq_duplicate if self.preset.sequence.can_duplicate else None,size=10);self.button(rx+168,156,132,46,'Fill',self._seq_fill_flash,self.seq_fill,size=10);self.text(rx+rw/2,222,'Fill all 64 steps with sequences.',8,MUTED,'center')
  self.rect(rx+10,270,rw-20,330);self.text(rx+24,286,'SEQUENCE SETTINGS',13,bold=True)
  self.text(rx+24,330,'OVERDUB',9,TEXT);self.dropdown(rx+130,314,170,38,self.seq_overdub,'SEQ_OVERDUB',['MONO','POLY'])
  self.text(rx+24,378,'TRANSPOSE',9,TEXT);self.dropdown(rx+130,362,170,38,str(self.preset.sequence.transpose),'SEQ_TRANS',list(range(-12,13)))
  self.text(rx+24,426,'SWING',9,TEXT);self.slider(rx+130,426,120,'','SEQ_SWING',0,100,show_label=False);self.text(rx+282,430,f'{int(self.values.get("SEQ_SWING",0))}%',8,TEXT,'e')
  # STEPS 1..64 uses the same thin-line language as numeric controls: drag + double-click entry.
  self.text(rx+24,474,'STEPS',9,TEXT);steps_x,steps_y,steps_w=rx+130,474,170;self.text(steps_x+steps_w/2,450,str(seq_len),9,MUTED,'center');st=(seq_len-1)/63
  self.line(steps_x,steps_y+4,steps_x+steps_w,steps_y+4,EDGE,3);self.line(steps_x,steps_y+4,steps_x+steps_w*st,steps_y+4,ORANGE,3)
  self.hitbox(steps_x,steps_y-8,steps_w,24,'seq_steps','SEQ_STEPS',(1,64,False,False))
  guide_cx=rx+rw/2;mouse_icon=Path(__file__).resolve().parent/'Assets'/'MOUSE_NO_ARROWS.png'
  self.text(guide_cx,632,'QUICK GUIDE',8,MUTED,'center',True)
  self.asset_icon(mouse_icon,guide_cx-70,646,22,22);self.text(guide_cx+6,656,'— edit step',8,MUTED,'center')
  self.text(guide_cx-62,676,'SHIFT +',8,MUTED,'center');self.asset_icon(mouse_icon,guide_cx-37,666,22,22);self.text(guide_cx+48,676,'— Pencil (4 points / step)',8,MUTED,'center')
  self.text(guide_cx,696,'Mouse wheel over Piano Roll — notes',8,MUTED,'center')
  self.text(guide_cx,716,'Horizontal bar — steps 1–64',8,MUTED,'center')
  self.text(guide_cx,736,'Double-click STEPS — type 1–64',8,MUTED,'center')

 def _song_tree_rows(self):
  rows=[]
  def walk(folder,depth):
   for child in storage.child_folders(folder):
    kids=bool(storage.child_folders(child));rows.append(('folder',child,child.name,depth,kids))
    if str(child) in self.song_tree_expanded:walk(child,depth+1)
   for fp in sorted(Path(folder).glob('*.unosyp'),key=lambda p:p.stem.lower()):rows.append(('preset',fp,fp.stem,depth,False))
  rows.append(('folder',storage.PRESETS,'ALL',0,True))
  if str(storage.PRESETS) in self.song_tree_expanded:walk(storage.PRESETS,1)
  return rows
 def _song_tree_toggle(self,path):
  path=Path(path);k=str(path)
  if path==Path(storage.PRESETS):self.song_tree_expanded.add(k)
  elif k in self.song_tree_expanded:self.song_tree_expanded.remove(k)
  else:self.song_tree_expanded.add(k)
  self.song_tree_selected=path;self.song_preset_folder=path;self.redraw()
 def draw_song(self):
  kbtop=982
  self.button(12,62,120,34,'SONG',self.song_mode=='SONG',lambda:self.set_song_mode('SONG'));self.button(138,62,120,34,'LIVE',self.song_mode=='LIVE',lambda:self.set_song_mode('LIVE'))
  left=12;top=105;lh=kbtop-top-8;self.rect(left,top,260,lh);self.text(26,118,'LOCAL PRESETS' if self.song_mode=='SONG' else 'SAVED SONGS',14,bold=True)
  if self.song_mode=='SONG':
   yy=152;all_rows=self._song_tree_rows();visible_rows=max(1,int((top+lh-20-yy)//25)+1);self.song_folder_scroll=clamp(self.song_folder_scroll,0,max(0,len(all_rows)-visible_rows))
   for kind,path,name,depth,has_kids in all_rows[self.song_folder_scroll:self.song_folder_scroll+visible_rows]:
    if yy>top+lh-20:break
    selected=(self.lib_selected==path if kind=='preset' else False)
    if selected:self.rect(20,yy-10,240,24,ORANGE2,ORANGE)
    ix=28+depth*14
    if kind=='folder':
     expanded=str(path) in self.song_tree_expanded;self.text(ix,yy,'▾' if expanded else '▸',11,MUTED,'w',True);self.text(ix+16,yy,'📁',11,ORANGE if selected else MUTED,'w');disp=name
     self.text(ix+34,yy,disp[:25] if len(disp)<=25 else disp[:22]+'…',10,ORANGE if selected else TEXT,'w');self.hitbox(20,yy-10,240,24,'songtreefolder',None,path)
    else:
     disp=name if len(name)<=27 else name[:24]+'…';self.text(ix+18,yy,disp,10,ORANGE if selected else TEXT,'w');self.hitbox(20,yy-10,240,24,'songlist',None,(path,name))
    yy+=25
  else:
   items=[(p.stem,'Song',[],p) for p in storage.list_songs()]
   for i,item in enumerate(items[:28]):
    y=160+i*27;name=item[0];path=item[3];sel=self.selected_song_file==path
    if sel:self.rect(20,y-3,240,25,ORANGE2,ORANGE)
    self.text(34,y,name,10,ORANGE if sel else TEXT);self.hitbox(20,y-3,240,25,'songlist',None,(path,name))
  # arrangement / live grid 4 columns x 16 rows horizontal
  cx=284;cw=1030;self.rect(cx,top,cw,lh);self.text(cx+14,118,'SONG ARRANGEMENT' if self.song_mode=='SONG' else 'LIVE SONGS',14,bold=True)
  gx=cx+14;gy=154;gap=10;cols=4;rows=16;cellw=(cw-28-gap*3)/4;cellh=(lh-70-gap*15)/16
  for idx in range(64):
   col=idx%4;row=idx//4;x=gx+col*(cellw+gap);y=gy+row*(cellh+gap)
   if self.song_mode=='SONG':name=self.song.slots[idx].preset_name
   else:name=Path(self.live_slots[idx]).stem if self.live_slots[idx] else 'EMPTY'
   active=(idx==self.selected_song_slot if self.song_mode=='SONG' else idx==self.selected_live_slot);fill=ORANGE2 if active else PANEL2;outline=ORANGE if active else EDGE
   self.rect(x,y,cellw,cellh,fill,outline);self.text(x+10,y+cellh/2,f'{idx+1:02}',9,ORANGE if active else TEXT,'w');self.text(x+58,y+cellh/2,name,10,TEXT if name!='EMPTY' else MUTED,'w');self.hitbox(x,y,cellw,cellh,'songcell',idx,None)
  # controls
  rx=1325;rw=265;self.rect(rx,top,rw,lh);self.text(rx+14,118,'SONG CONTROLS' if self.song_mode=='SONG' else 'LIVE CONTROLS',14,bold=True)
  if self.song_mode=='SONG':
   self.text(rx+16,158,'TEMPO',10);self.dropdown(rx+16,175,rw-32,32,str(self.song.tempo),'SONG_TEMPO',list(range(40,241)));self.text(rx+16,220,'LENGTH (1–64)',10);self.dropdown(rx+16,237,rw-32,32,str(self.song.length),'SONG_LENGTH',list(range(1,65)))
   self.button(rx+16,290,rw-32,42,'▶  PLAY',False,self.midi.start);self.button(rx+16,338,rw-32,42,'■  STOP',False,self.midi.stop);self.button(rx+16,395,110,34,'COPY',False,lambda:None);self.button(rx+135,395,114,34,'PASTE',False,lambda:None);self.button(rx+16,438,rw-32,38,'CLEAR SELECTION',False,self.clear_song_slot);self.button(rx+16,484,rw-32,38,'CLEAR SONG',False,self.clear_song);self.button(rx+16,545,rw-32,42,'SAVE SONG',True,self.save_song);self.button(rx+16,595,rw-32,38,'LOAD SONG',False,self.load_song_dialog);self.button(rx+16,641,rw-32,38,'DEPLOY TO UNO',False,self.deploy_locked);self.text(rx+16,692,'Bulk hardware write stays locked\nuntil 0x28 is fully validated.',8,MUTED)
  else:
   play_size=rw-32;play_label=(f'CANCEL {self.live_countdown_remaining}s' if self.live_countdown_remaining>0 else ('■ STOP' if self.live_playing else '▶ PLAY'));self.button(rx+16,150,play_size,play_size,play_label,self.live_playing or self.live_countdown_remaining>0,self.toggle_live_play,size=14)
   self.text(rx+16,400,'DELAYED START',10,TEXT);self.dropdown(rx+16,420,rw-32,36,('OFF' if self.live_delay==0 else ('1 min' if self.live_delay==60 else f'{self.live_delay} s')),'LIVE_DELAY',[0]+list(range(5,61,5)))
   self.text(rx+rw/2,476,'5–60 seconds',8,MUTED,'center');self.text(rx+rw/2,520,'The 4×16 grid is identical to SONG.\nEach cell holds a saved song.',9,MUTED,'center')
 def set_song_mode(self,m):self.song_mode=m;self.redraw()
 def draw_library(self):
  self.rect(12,62,1576,920)
  self.text(30,82,'PRESET LIBRARY',17,bold=True)
  # LEFT: permanent LOCAL library. RIGHT: UNO by default, or a LOCAL folder opened from the tree.
  # v1.63: three visible LOCAL preset columns, two visible right-panel columns, clear separation.
  left_x=24;left_w=900;gap=28;right_x=left_x+left_w+gap;right_w=612
  self._draw_local_panel(left_x,125,left_w,780)
  # Clean inter-panel gap also masks any partially scrolled LOCAL text.
  self.rect(left_x+left_w,125,gap,780,BG,BG)
  self._draw_right_panel(right_x,125,right_w,780)
  self.rect(right_x+right_w,125,max(0,BASE_W-(right_x+right_w)),780,BG,BG)
  if self._lib_tooltip:
   tx,ty,msg=self._lib_tooltip;tw=max(70,14+len(msg)*7)
   self.rect(tx,ty,tw,26,'#07090a',LIGHT_GREY);self.text(tx+8,ty+13,msg,8,TEXT,'w')

 def _tool_icon(self,x,y,label,tip,action,active=False,w=30):
  self.rect(x,y,w,30,ORANGE2 if active else PANEL2,ORANGE if active else EDGE)
  self.text(x+w/2,y+15,label,14,ORANGE if active else TEXT,'center',True)
  self.hitbox(x,y,w,30,'libtool',tip,action)

 def _draw_tag_tools(self,x,y):
  self.rect(x,y,30,30,ORANGE2 if self.lib_star_filter else PANEL2,ORANGE if self.lib_star_filter else EDGE)
  self.text(x+15,y+15,'★',14,'#ffd84a','center',True);self.hitbox(x,y,30,30,'libtool','Favorites',lambda:self._toggle_lib_star());x+=36
  cols=['#e34b4b','#ed8b32','#e2c744','#63b85b','#4d9fdf','#786bd6','#c05ac4']
  for i,c in enumerate(cols):
   active=i in self.lib_color_filters
   self._draw_aa_circle(x+15,y+15,14,c,WHITE if active else EDGE,2 if active else 1)
   self.hitbox(x,y,30,30,'libtool',f'Tag {i+1}',lambda i=i:self._toggle_lib_color(i));x+=30
  return x

 def _toggle_lib_star(self):self.lib_star_filter=not self.lib_star_filter;self.redraw()
 def _toggle_lib_color(self,i):
  if i in self.lib_color_filters:self.lib_color_filters.remove(i)
  else:self.lib_color_filters.add(i)
  self.redraw()
 def _meta_match(self,path):
  m=storage.get_preset_metadata(path)
  if self.lib_star_filter and not m.get('favorite',False):return False
  if self.lib_color_filters and not self.lib_color_filters.issubset(set(m.get('colors',[]))):return False
  return True

 def _draw_local_panel(self,x,y,w,h):
  # LOCAL label and Add Folder toolbar icon intentionally omitted; folder creation lives in the folder context menu.
  tag_tools_w=246
  self._draw_tag_tools(x+w-tag_tools_w,y)
  body_y=y+42;self.rect(x,body_y,w,h-42,'#111416',EDGE)
  tree_w=250;gap=10;view_x=x+tree_w+gap;view_w=w-tree_w-gap
  self.rect(x,body_y,tree_w,h-42,'#0e1214',EDGE);self.rect(view_x,body_y,view_w,h-42,'#111416',EDGE)
  folder=self.lib_panel_folder[0] or storage.PRESETS
  self._draw_preset_columns(view_x,body_y,view_w,h-42,folder,0,all_recursive=(Path(folder)==storage.PRESETS))
  # Draw the tree last: it acts as the left clip mask for partially visible columns.
  self.rect(x,body_y,tree_w,h-42,'#0e1214',EDGE);self._draw_folder_tree(x,body_y,tree_w,h-42)

 def _folder_rows(self):
  rows=[('all',storage.PRESETS,'ALL',0,True)]
  def walk(folder,depth):
   for d in storage.child_folders(folder):
    kids=storage.child_folders(d);expanded=str(d) in self.lib_expanded
    rows.append(('folder',d,d.name,depth,bool(kids)))
    if kids and expanded:walk(d,depth+1)
  walk(storage.PRESETS,0);return rows

 def _draw_folder_tree(self,x,y,w,h):
  rows=self._folder_rows();yy=y+18
  for kind,path,name,depth,has_kids in rows:
   if yy>y+h-34:break
   selected=Path(self.lib_panel_folder[0] or storage.PRESETS)==Path(path)
   if selected:self.rect(x+4,yy-12,w-8,27,'#292f33',EDGE)
   ix=x+10+depth*14
   if kind=='all':self.text(ix,yy,'▦',14,ORANGE if selected else MUTED,'w',True)
   else:
    if has_kids:self.text(ix,yy,'▾' if str(path) in self.lib_expanded else '▸',12,MUTED,'w',True)
    self.text(ix+16,yy,'📁',13,ORANGE if selected else MUTED,'w')
   tx=ix+(20 if kind=='all' else 38);avail=max(28,w-(tx-x)-10);max_chars=max(3,int(avail/7.2));disp=name if len(name)<=max_chars else name[:max(1,max_chars-1)]+'…'
   self.text(tx,yy,disp,11,ORANGE if selected else TEXT,'w')
   self.hitbox(x+4,yy-12,w-8,27,'libfoldertree',0,(path,name,kind))
   yy+=29
  self._restore_folder_entry_window()

 def _filtered_files(self,folder,all_recursive=False):
  try:
   base=Path(folder);files=list(base.rglob('*.unosyp')) if all_recursive else list(base.glob('*.unosyp'))
   files=[p for p in files if storage.SONGS not in p.parents];meta={p:storage.get_preset_metadata(p) for p in files}
   files.sort(key=lambda p:((meta[p].get('order') is None),meta[p].get('order') if meta[p].get('order') is not None else 0,p.stem.lower()))
   if self.lib_query:files=[p for p in files if self.lib_query.lower() in p.stem.lower()]
   if self.lib_star_filter:files=[p for p in files if meta[p].get('favorite',False)]
   if self.lib_color_filters:files=[p for p in files if self.lib_color_filters.issubset(set(meta[p].get('colors',[])))]
   self._lib_meta_cache=meta;return files
  except Exception:return []

 def _draw_preset_columns(self,x,y,w,h,folder,idx,all_recursive=False):
  files=self._filtered_files(folder,all_recursive);rows=max(1,int((h-42)//30));col_w=210 if idx==0 else 290;cols=max(1,(len(files)+rows-1)//rows);content_w=cols*col_w
  max_scroll=max(0,content_w-w+12);self.lib_hscroll[idx]=clamp(self.lib_hscroll[idx],0,max_scroll);off=self.lib_hscroll[idx]
  # Register the scrollable background first so individual preset hitboxes drawn
  # afterwards have priority in _hit_at() (which checks hitboxes in reverse order).
  self.hitbox(x,y,w,h,'libfilescroll',idx,max_scroll)
  for n,fp in enumerate(files):
   col=n//rows;row=n%rows;xx=x+10+col*col_w-off;yy=y+21+row*30
   if xx+col_w<x or xx>x+w:continue
   sel=self.lib_selected==fp
   if sel:self.rect(xx-4,yy-11,col_w-5,25,ORANGE2,ORANGE)
   num=files.index(fp)+1; name=fp.stem; disp=name if len(name)<=25 else name[:22]+'…'; disp=f'[{num:03d}] {disp}'
   # Reserve a measured gap for tags so punctuation never overlaps the name.
   self.text(xx,yy,disp,11,ORANGE if sel else TEXT,'w')
   meta=getattr(self,'_lib_meta_cache',{}).get(fp) or storage.get_preset_metadata(fp);tagx=xx+min(col_w-34,max(20,len(disp)*7.4+12))
   if meta.get('favorite'):self.text(tagx,yy,'★',10,ORANGE,'w');tagx+=13
   # Tag data/filtering remain; visual tag circles are intentionally omitted.
   self.hitbox(xx-4,yy-12,col_w-5,27,'libpreset',idx,(fp,fp.stem))
  if max_scroll>0:
   track_y=y+h-13;self.line(x+8,track_y,x+w-8,track_y,EDGE,3);thumb=max(32,(w-16)*w/content_w);pos=(w-16-thumb)*(self.lib_hscroll[idx]/max_scroll if max_scroll else 0)
   self.line(x+8+pos,track_y,x+8+pos+thumb,track_y,LIGHT_GREY,5);self.hitbox(x+8,track_y-8,w-16,16,'libxscroll',idx,{'max':max_scroll,'thumb':thumb,'w':w-16,'x':x+8})

 def _draw_right_panel(self,x,y,w,h):
  # Stable toolbar: Uno sits at the right, just before Receive/Send, with a small visual gap.
  enabled=self.lib_right_mode=='UNO'
  recv_x=x+w-84;send_x=x+w-38;uno_x=recv_x-66
  self._tool_icon(uno_x,y,'Uno','Uno',self._right_show_uno,self.lib_right_mode=='UNO',54)
  self._tool_icon(recv_x,y,'↓','Receive',self.to_lib if enabled else None,False,38)
  self._tool_icon(send_x,y,'↑','Send',self.to_hw if enabled else None,False,38)
  if not enabled:
   # Keep the buttons in place and visibly disabled so the layout never jumps.
   for bx in (recv_x,send_x):
    self.canvas.create_rectangle(self.X(bx),self.Y(y),self.X(bx+38),self.Y(y+30),fill='#111416',outline='',stipple='gray50')
  body_y=y+42;self.rect(x,body_y,w,h-42,'#111416',LIGHT_GREY,2);self.rect(x+5,body_y+5,w-10,h-52,'#111416',EDGE)
  if self.lib_right_mode=='UNO':
   self._draw_uno_slots(x,body_y,w,h-42)
  else:
   self._draw_preset_columns(x,body_y,w,h-42,self.lib_right_folder or storage.PRESETS,1,False)

 def _right_show_uno(self):self.lib_right_mode='UNO';self.redraw()
 def _right_open_folder(self,path):self.lib_right_mode='LOCAL';self.lib_right_folder=Path(path);self.lib_hscroll[1]=0;self.redraw()
 def _draw_uno_slots(self,x,y,w,h):
  rows=max(1,int((h-34)//30));col_w=290;cols=max(1,(256+rows-1)//rows);content_w=cols*col_w;max_scroll=max(0,content_w-w+12);self.lib_hscroll[1]=clamp(self.lib_hscroll[1],0,max_scroll);off=self.lib_hscroll[1]
  self.hitbox(x,y,w,h,'libhwscroll',1,max_scroll)
  for n in range(1,257):
   col=(n-1)//rows;row=(n-1)%rows;xx=x+10+col*col_w-off;yy=y+20+row*30
   if xx < x+6 or xx+col_w > x+w-6:continue
   sel=n==getattr(self,'lib_hw_selected',self.hardware_selected)
   if sel:self.rect(xx-4,yy-10,col_w-8,28,ORANGE2,ORANGE)
   self.text(xx+4,yy,f'{n:03d}',11,ORANGE if sel else TEXT,'w');name=self.hardware_names.get(n,'—') or '—';self.text(xx+54,yy,name[:24],10,TEXT if self.hardware_names.get(n) else MUTED,'w');self.hitbox(xx-4,yy-10,col_w-8,28,'hwslot',n)
  if max_scroll>0:
   track_y=y+h-13;self.line(x+8,track_y,x+w-8,track_y,EDGE,3);thumb=max(32,(w-16)*w/content_w);pos=(w-16-thumb)*(self.lib_hscroll[1]/max_scroll if max_scroll else 0)
   self.line(x+8+pos,track_y,x+8+pos+thumb,track_y,LIGHT_GREY,5);self.hitbox(x+8,track_y-8,w-16,16,'libxscroll',1,{'max':max_scroll,'thumb':thumb,'w':w-16,'x':x+8})
 def _begin_add_folder(self):
  parent=Path(self.lib_panel_folder[0] or storage.PRESETS)
  if parent==storage.PRESETS or parent.is_dir():pass
  try:
   base=parent/'New Folder';dst=base;i=2
   while dst.exists():dst=parent/f'New Folder {i}';i+=1
   dst.mkdir(parents=False);storage.invalidate_preset_cache();self.lib_expanded.add(str(parent));self.lib_panel_folder[0]=dst
   self._begin_folder_rename(dst)
  except Exception as e:self._notify('Folder',str(e),True)

 def _begin_folder_rename(self,path):
  self._finish_folder_entry(False);path=Path(path)
  ent=tk.Entry(self.canvas,bg='#090c0e',fg=TEXT,insertbackground=ORANGE,relief='solid',bd=1,font=('Segoe UI',11))
  ent.insert(0,path.name);ent.selection_range(0,'end');self._lib_folder_entry={'entry':ent,'path':path};ent.focus_set()
  ent.bind('<Return>',lambda ev:(self._finish_folder_entry(True),'break')[1]);ent.bind('<Escape>',lambda ev:(self._finish_folder_entry(False),'break')[1]);ent.bind('<FocusOut>',lambda ev:self._finish_folder_entry(True))
  self.redraw()
 def _restore_folder_entry_window(self):
  d=self._lib_folder_entry
  if not d:return
  rows=self._folder_rows();idx=next((i for i,r in enumerate(rows) if Path(r[1])==Path(d['path'])),None)
  if idx is None:return
  yy=125+42+18+idx*29;self._lib_folder_entry_window=self.canvas.create_window(self.X(24+45),self.Y(yy),window=d['entry'],width=max(90,self.S(145)),height=max(22,self.S(24)),anchor='w')
 def _finish_folder_entry(self,apply=True):
  d=self._lib_folder_entry
  if not d:return
  self._lib_folder_entry=None;src=Path(d['path'])
  if apply:
   name=d['entry'].get().strip()
   if name and name!=src.name:
    try:
     dst=src.with_name(storage._safe(name));src.rename(dst);self.lib_panel_folder[0]=dst
     if self.lib_right_folder==src:self.lib_right_folder=dst
    except Exception as e:self._notify('Rename folder',str(e),True)
  try:d['entry'].destroy()
  except Exception:pass
  storage.invalidate_preset_cache();self.redraw()

 def _load_library_preset(self,path):
  path=Path(path);self.lib_selected=path;self.preset_source='LOCAL';self.preset_folder=path.parent
  self.load_local_preset(path,preview=True);self.redraw()
 def _library_menu(self,parent=None):
  return self._dark_menu(parent)
 def _close_context_popup(self):
  p=getattr(self,'_context_popup',None)
  self._context_popup=None
  if p:
   try:p.destroy()
   except Exception:pass
 def _preset_context_menu(self,e,path):
  path=Path(path);self.lib_selected=path;self.redraw()
  m=self._library_menu();tags=self._library_menu(m)
  labels=[('★',None,'#ffd84a'),('●',0,'#e34b4b'),('●',1,'#ed8b32'),('●',2,'#e2c744'),('●',3,'#63b85b'),('●',4,'#4d9fdf'),('●',5,'#786bd6'),('●',6,'#c05ac4')]
  for lab,idx,col in labels:
   if idx is None:tags.add_command(label=lab,command=lambda:self._toggle_preset_favorite(path))
   else:tags.add_command(label=lab,command=lambda i=idx:self._toggle_preset_tag(path,i))
   try:tags.entryconfigure('end',foreground=col,activeforeground=col)
   except Exception:pass
  m.add_cascade(label='Tags >',menu=tags);m.add_separator()
  order_files=self._filtered_files(path.parent,False)
  try:order_idx=order_files.index(path)
  except ValueError:order_idx=-1
  m.add_command(label='↑ UP',state=('disabled' if order_idx<=0 else 'normal'),command=lambda:self._move_preset_order(path,-1))
  m.add_command(label='↓ DOWN',state=('disabled' if order_idx<0 or order_idx>=len(order_files)-1 else 'normal'),command=lambda:self._move_preset_order(path,1));m.add_separator()
  m.add_command(label='Rename',command=self.lib_rename);m.add_command(label='Copy',command=self.lib_copy);m.add_command(label='Cut',command=self.lib_cut);m.add_command(label='Paste',command=self.lib_paste)
  m.add_separator();m.add_command(label='Delete',command=self.lib_delete)
  try:m.tk_popup(e.x_root,e.y_root)
  finally:m.grab_release()
 def _move_preset_order(self,path,direction):
  path=Path(path);folder=path.parent;files=self._filtered_files(folder,False)
  if path not in files:return
  # Initialize persistent order from the currently visible order once, then swap neighbours.
  for i,p in enumerate(files):
   meta=storage.get_preset_metadata(p)
   if meta.get('order') is None:meta['order']=i;storage.set_preset_metadata(p,meta)
  files=self._filtered_files(folder,False);i=files.index(path);j=i+int(direction)
  if not 0<=j<len(files):return
  a,b=files[i],files[j];ma=storage.get_preset_metadata(a);mb=storage.get_preset_metadata(b)
  ma['order'],mb['order']=mb.get('order',j),ma.get('order',i);storage.set_preset_metadata(a,ma);storage.set_preset_metadata(b,mb);self.redraw()
 def _refresh_preset_context_tags(self,path,star,canv):
  meta=storage.get_preset_metadata(path);star.configure(fg='#ffd84a',bg=ORANGE2 if meta.get('favorite') else '#11171a')
  try:canv._draw_tags()
  except Exception:pass
 def _folder_context_menu(self,e,path):
  path=Path(path);m=self._library_menu()
  kids=storage.child_folders(path)
  if kids:
   expanded=str(path) in self.lib_expanded
   m.add_command(label='Collapse' if expanded else 'Expand',command=lambda:self._toggle_folder_expand(path))
  m.add_command(label='Open in right panel',command=lambda:self._right_open_folder(path));m.add_separator()
  m.add_command(label='New folder',command=lambda:self._begin_add_folder_in(path))
  m.add_command(label='Rename',command=lambda:self._begin_folder_rename(path))
  m.add_command(label='Copy',command=lambda:self._folder_clip('copy',path))
  m.add_command(label='Cut',command=lambda:self._folder_clip('cut',path))
  m.add_command(label='Paste',command=lambda:self._folder_paste(path))
  m.add_separator();m.add_command(label='Delete',command=lambda:self._delete_folder(path))
  try:m.tk_popup(e.x_root,e.y_root)
  finally:m.grab_release()

 def _toggle_folder_expand(self,path):
  path=str(Path(path))
  if path in self.lib_expanded:self.lib_expanded.remove(path)
  else:self.lib_expanded.add(path)
  self.redraw()

 def _begin_add_folder_in(self,parent):
  old=self.lib_panel_folder[0];self.lib_panel_folder[0]=Path(parent)
  try:self._begin_add_folder()
  except Exception:self.lib_panel_folder[0]=old;raise

 def _folder_clip(self,mode,path):
  path=Path(path)
  if path.exists():self._lib_folder_clipboard=(mode,path);self.status=f'Folder {mode}';self.redraw()

 def _folder_paste(self,target):
  if not self._lib_folder_clipboard:return
  mode,src=self._lib_folder_clipboard;target=Path(target)
  if not src.exists() or not target.is_dir():return
  try:
   dst=target/src.name;i=2
   while dst.exists():dst=target/f'{src.name} {i}';i+=1
   if mode=='copy':shutil.copytree(src,dst)
   else:shutil.move(str(src),str(dst));self._lib_folder_clipboard=None
   storage.invalidate_preset_cache();self.lib_expanded.add(str(target));self.redraw()
  except Exception as ex:self._notify('Paste folder',str(ex),True)

 def _toggle_preset_favorite(self,path):
  m=storage.get_preset_metadata(path);m['favorite']=not m.get('favorite',False);storage.set_preset_metadata(path,m);self.redraw()
 def _toggle_preset_tag(self,path,i):
  m=storage.get_preset_metadata(path);c=set(m.get('colors',[]));c.remove(i) if i in c else c.add(i);m['colors']=sorted(c);storage.set_preset_metadata(path,m);self.redraw()
 def draw_settings(self):
  self.rect(16,70,760,820);self.rect(790,70,794,820);self.text(42,95,'MIDI SETTINGS',18,bold=True);self.text(820,95,'ABOUT',18,bold=True)
  in_cur=self.settings.get('midi_in','UNO_RETURN');out_cur=self.settings.get('midi_out','UNO_TAP');ctrl_cur=self.settings.get('midi_controller','Off')
  ins=list(dict.fromkeys(([in_cur] if in_cur else [])+self._midi_inputs)) or ['UNO_RETURN'];outs=list(dict.fromkeys(([out_cur] if out_cur else [])+self._midi_outputs)) or ['UNO_TAP'];controllers=list(dict.fromkeys(['Off']+([ctrl_cur] if ctrl_cur and ctrl_cur!='Off' else [])+self._midi_inputs))
  rows=[('MIDI IN','midi_in',ins),('MIDI OUT','midi_out',outs),('MIDI CONTROLLER','midi_controller',controllers),('MIDI IN CHANNEL','midi_in_channel',['OMNI']+list(range(1,17))),('MIDI OUT CHANNEL','midi_out_channel',list(range(1,17))),('MIDI CLOCK','midi_clock',['Off','MIDI MASTER']),('SYNC','sync',['Internal','External','USB']),('MIDI INTERFACE','midi_interface',['Auto','Off','On'])]
  for i,(lab,key,opts) in enumerate(rows):
   y=145+i*82;self.text(55,y,lab,11,MUTED);self.settings_dropdown(320,y-10,410,40,self._display_setting(self.settings.get(key,opts[0])),key,opts)
  self.text(820,155,'UNO Pro Advanced',20,TEXT,bold=True);self.text(820,192,'Version 0.9.5-beta',11,MUTED)
  self.text(820,240,'Editor / librarian for IK Multimedia UNO Synth Pro',10,TEXT)
  self.text(820,270,'Hardware STORE remains locked until 0x28 is fully validated.',9,MUTED)
  self.button(530,820,202,44,'APPLY',self.settings_dirty,self.apply_settings if self.settings_dirty else None)

 def apply_midi(self):
  self._start_midi_connect(save=True,initial=False)
 def apply_settings(self):
  storage.save_settings(self.settings);self._applied_settings=copy.deepcopy(self.settings);self.settings_dirty=False
  self.preview=bool(self.settings.get('preview',True));self.live_delay=int(self.settings.get('live_delay',self.live_delay))
  self.status='Settings applied'
  self._start_midi_connect(save=False,initial=False);self.redraw()
 def save_settings(self):self.apply_settings()
 def _keyboard_key_shape(self,x,y,w,h,fill,outline,r=5):
  # Straight top corners; only the two bottom corners are rounded.
  import math
  r=max(1,min(float(r),w/4,h/5));pts=[(x,y),(x+w,y),(x+w,y+h-r)]
  for a in (0,22.5,45,67.5,90):
   rad=math.radians(a);pts.append((x+w-r+r*math.cos(rad),y+h-r+r*math.sin(rad)))
  for a in (90,112.5,135,157.5,180):
   rad=math.radians(a);pts.append((x+r+r*math.cos(rad),y+h-r+r*math.sin(rad)))
  pts.append((x,y))
  flat=[]
  for px,py in pts:flat.extend((self.X(px),self.Y(py)))
  self.canvas.create_polygon(*flat,fill=fill,outline=outline,width=max(1,int(self.S(1))),smooth=False)
 def draw_keyboard(self):
  # Borderless three-octave performance panel. It is drawn inside the 1600x1000 design area.
  y=1000;panel_h=162
  # Octave step control: two arrows stacked vertically.
  self.button(20,y+18,42,54,'▲',False,lambda:self._keyboard_octave(1),size=12);self.button(20,y+78,42,54,'▼',False,lambda:self._keyboard_octave(-1),size=12)
  self.text(72,y+75,f'{self.keyboard_octave_shift:+d}' if self.keyboard_octave_shift else '0',13,TEXT,'center',True)
  # Pitch and Mod are paired animated strips, deliberately without text labels.
  px=78;strip_w=48;strip_y=y+14;strip_h=132
  self.rect(px,strip_y,strip_w,strip_h,'#0b0e10',EDGE);cy=strip_y+strip_h/2;self.line(px+6,cy,px+strip_w-6,cy,MUTED,1);pv=clamp(self.pitch_visual,-8192,8191)/8192;py=cy-pv*(strip_h*.42);fy=min(cy,py);fh=max(2,abs(py-cy));self.rect(px+7,fy,strip_w-14,fh,ORANGE2,ORANGE);self.hitbox(px-4,strip_y-4,strip_w+8,strip_h+8,'pitchwheel')
  mx=140;self.rect(mx,strip_y,strip_w,strip_h,'#0b0e10',EDGE);mv=clamp(self.values.get('MOD_WHEEL',0),0,127)/127;fill_h=(strip_h-12)*mv;self.rect(mx+7,strip_y+strip_h-6-fill_h,strip_w-14,fill_h,ORANGE2,ORANGE);self.hitbox(mx-4,strip_y-4,strip_w+8,strip_h+8,'modwheel')
  # Pitch Bend Range selector / step control.
  ranges=[2,4,6,8,12,24];cur=int(self.settings.get('pitch_bend_range',2));cur=cur if cur in ranges else 2
  rx=202;self.text(rx+46,y+22,'PB RANGE',8,MUTED,'center');self.button(rx,y+42,30,42,'◀',False,lambda:self._step_pb_range(-1),size=9);self.text(rx+46,y+63,str(cur),13,TEXT,'center',True);self.button(rx+62,y+42,30,42,'▶',False,lambda:self._step_pb_range(1),size=9)
  # Three octaves, stretched to the full available panel height; width follows key proportions.
  kx=312;kh=panel_h-8;ky=y+4;octs=3;white_count=octs*7;kw=1260;ww=kw/white_count;start=max(0,min(91,36+self.keyboard_octave_shift*12));active=self.keys_down|self.hw_keys_down
  whites=[n for n in range(start,start+octs*12+1) if n%12 not in (1,3,6,8,10)]
  for i,n in enumerate(whites[:white_count]):
   pressed=n in active;off=3 if pressed else 0;x=kx+i*ww
   self._keyboard_key_shape(x,ky+off,ww,kh-off,ORANGE2 if pressed else WHITE,ORANGE if pressed else '#333',5);self.hitbox(x,ky,ww,kh,'key',n)
  wi=0
  for n in range(start,start+octs*12):
   if n%12 in (1,3,6,8,10):
    pressed=n in active;off=3 if pressed else 0;x=kx+(wi-.32)*ww;self._keyboard_key_shape(x,ky+off,ww*.62,kh*.61-off,ORANGE2 if pressed else '#101214',ORANGE if pressed else '#050505',4);self.hitbox(x,ky,ww*.62,kh*.65,'key',n)
   else:wi+=1
 def _keyboard_octave(self,d):
  self.keyboard_octave_shift=max(-3,min(4,int(self.keyboard_octave_shift)+int(d)));self.redraw()
 def _step_pb_range(self,d):
  vals=[2,4,6,8,12,24];cur=int(self.settings.get('pitch_bend_range',2));i=vals.index(cur) if cur in vals else 0;i=max(0,min(len(vals)-1,i+int(d)));self.settings['pitch_bend_range']=vals[i];storage.save_settings(self.settings);self.redraw()

 def click(self,e):
  x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale
  h0=self._hit_at(x,y)
  if self.open_dropdown and (h0 is None or h0[4] not in ('dropdown_item','choice')):
   self.open_dropdown=None;self.dropdown_hover=None
   if h0 is None:self.redraw();return
  for h in reversed(self.hit):
   hx,hy,hw,hh,kind,key,data=h
   if hx<=x<=hx+hw and hy<=y<=hy+hh:
    if kind=='envseg' and not self._near_env_segment(x,y,data):continue
    if kind=='action':
     if callable(data):data()
    elif kind=='modamount':
     under=next((q for q in reversed(self.hit) if q[4]=='slider' and q[0]<=x<=q[0]+q[2] and q[1]<=y<=q[1]+q[3]),None)
     if under:self.drag=under;self._set_slider(under,x,y);self._set_popup(under,x,y)
    elif kind=='slider':self.drag=h;self._set_slider(h,x,y);self._set_popup(h,x,y)
    elif kind=='seq_steps':self.drag=h;self._set_seq_steps(h,x)
    elif kind in ('lfo_wave','osc_wave'):self.drag=h;self._drag_origin=(y,float(self.values.get(key,0)))
    elif kind=='envpoint':self.drag=h;self._drag_origin=(x,y)
    elif kind=='envseg':
     idx,gx,gy,gw,gh,*_=data;self.drag=(hx,hy,hw,hh,'envpoint',key,(idx,gx,gy,gw,gh));self._drag_origin=(x,y);self._drag_env_point(self.drag,x,y)
    elif kind=='choice':self._open_dropdown(h,key,data)
    elif kind=='dropdown_item':self._select_dropdown_value(key,data)
    elif kind=='choice_dir':
     opts,d=data;self._cycle_choice(key,opts,d)
    elif kind=='pianoroll':self._piano_edit(data,x,y)
    elif kind=='seq_vscroll':self.drag=h;self._seq_vscroll(y,data)
    elif kind=='seq_hscroll':self.drag=h;self._seq_hscroll(x,data)
    elif kind=='libxscroll':self.drag=h;self._lib_xscroll(x,data)
    elif kind=='seqbar':self.drag=h;self._seqbar(key,data,y,hy,hh)
    elif kind=='modlane':
     if e.state & 0x0001:
      self.drag=(hx,hy,hw,hh,'modpencil',key,data);self._modpencil(x,y,data)
     else:
      self.drag=(hx,hy,hw,hh,'modlane',key,data);self._modlane_step(x,y,data)
    elif kind=='key':self.midi.note_on(key,100);self.keys_down.add(key);self._env_note_on();self.redraw()
    elif kind=='pitchwheel':self.drag=h;self._wheel_pitch(y,hy,hh)
    elif kind=='modwheel':self.drag=h;self._wheel_mod(y,hy,hh)
    elif kind=='songlist':
     path,name=data
     if self.song_mode=='SONG':
      self.lib_selected=path;self.drag=(hx,hy,hw,hh,'songdrag',None,{'path':Path(path),'name':name});self._lib_drag_origin=(x,y);self._lib_drag_started=False
     else:
      self.selected_song_file=path;self.drag=(hx,hy,hw,hh,'songdrag',None,{'path':Path(path),'name':name});self._lib_drag_origin=(x,y);self._lib_drag_started=False
     self.redraw();return 'break'
    elif kind=='songfolder':self.song_preset_folder=Path(data);self.redraw()
    elif kind=='songtreefolder':self._song_tree_toggle(data)
    elif kind=='songcell':self._song_cell(key)
    elif kind=='libcat':self.lib_category=key;self.redraw()
    elif kind=='libfolder':self.lib_panel_folder[key]=Path(data[0]);self.redraw()
    elif kind=='libfoldertree':
     path,name,fkind=data;path=Path(path);self.lib_panel_folder[0]=path;self.lib_hscroll[0]=0;self.redraw()
     if fkind=='folder':
      self.drag=(hx,hy,hw,hh,'libdrag',0,{'source':'folder','path':path});self._lib_drag_origin=(x,y);self._lib_drag_started=False
     return 'break'
    elif kind=='libtool':
     if callable(data):data()
    elif kind=='libpreset':
     self.lib_focus=int(key);path=Path(data[0]);self.lib_selected=path
     self.drag=(hx,hy,hw,hh,'libdrag',key,{'source':'local','path':path});self._lib_drag_origin=(x,y);self._lib_drag_started=False;self.redraw();return 'break'
    elif kind=='hwslot':
     self.lib_focus=1;self.lib_hw_selected=int(key);self.drag=(hx,hy,hw,hh,'libdrag',key,{'source':'uno','slot':int(key)});self._lib_drag_origin=(x,y);self._lib_drag_started=False;self.redraw();return 'break'
    return
 def right_click(self,e):
  if self.page!='LIBRARY':return
  x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;h=self._hit_at(x,y)
  if not h:return
  if h[4]=='libpreset':self._preset_context_menu(e,h[6][0]);return 'break'
  if h[4]=='libfoldertree':
   path,name,fkind=h[6]
   if fkind=='all':return 'break'
   self.lib_panel_folder[0]=Path(path);self.redraw();self._folder_context_menu(e,Path(path));return 'break'

 def _delete_folder(self,path):
  path=Path(path)
  if self._confirm('Delete folder',f'Delete folder "{path.name}" and its contents?'):
   try:
    shutil.rmtree(path);storage.invalidate_preset_cache()
    if Path(self.lib_panel_folder[0] or storage.PRESETS)==path:self.lib_panel_folder[0]=storage.PRESETS
    if self.lib_right_folder==path:self._right_show_uno()
    self.redraw()
   except Exception as e:self._notify('Delete folder',str(e),True)
 def _near_env_segment(self,x,y,data,tol=8.0):
  try:
   _,_,_,_,x1,y1,x2,y2=data;dx=x2-x1;dy=y2-y1
   if dx==0 and dy==0:return math.hypot(x-x1,y-y1)<=tol
   t=clamp(((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy),0.0,1.0);px=x1+t*dx;py=y1+t*dy
   return math.hypot(x-px,y-py)<=tol
  except Exception:return False
 def _hit_at(self,x,y):
  for h in reversed(self.hit):
   hx,hy,hw,hh,kind,key,data=h
   if hx<=x<=hx+hw and hy<=y<=hy+hh:
    if kind=='envseg' and not self._near_env_segment(x,y,data):continue
    return h
  return None
 def double_click(self,e):
  x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;h=self._hit_at(x,y)
  if h and h[4]=='pianoroll':self._piano_delete(h[6],x,y)
  elif h and h[4]=='slider':self._begin_numeric_entry(h)
  elif h and h[4]=='seq_steps':self._begin_numeric_entry((h[0],h[1],h[2],h[3],'slider','SEQ_STEPS',(1,64,False,False)))
  elif h and h[4] in ('lfo_wave','osc_wave'):self._begin_numeric_entry((h[0],h[1],h[2],h[3],'slider',h[5],(0,127,False,False)))
  return 'break'
 def _begin_numeric_entry(self,h):
  self._finish_numeric_entry(False)
  hx,hy,hw,hh,kind,key,data=h;lo,hi,vert,bip=data;v=(self.preset.sequence.length if key=='SEQ_STEPS' else self.values.get(key,lo))
  ent=tk.Entry(self.canvas,bg='#090c0e',fg=ORANGE,insertbackground=ORANGE,relief='solid',bd=1,justify='center',font=('Segoe UI',10,'bold'))
  ent.insert(0,str(int(v) if float(v).is_integer() else v));px=self.X(hx+hw/2);py=self.Y(hy-22);win=self.canvas.create_window(px,py,window=ent,width=max(64,self.S(72)),height=max(25,self.S(28)),anchor='center')
  self._numeric_entry={'entry':ent,'window':win,'key':key,'lo':lo,'hi':hi,'x':hx+hw/2,'y':hy-22,'width':72,'height':28};ent.focus_set();ent.selection_range(0,'end')
  ent.bind('<Return>',lambda ev:(self._finish_numeric_entry(True),'break')[1]);ent.bind('<Escape>',lambda ev:(self._finish_numeric_entry(False),'break')[1])
 def _restore_numeric_entry_window(self):
  d=self._numeric_entry
  if not d:return
  try:
   if not d['entry'].winfo_exists():return
   d['window']=self.canvas.create_window(self.X(d['x']),self.Y(d['y']),window=d['entry'],width=max(64,self.S(d['width'])),height=max(25,self.S(d['height'])),anchor='center')
   d['entry'].lift()
  except Exception:pass
 def _finish_numeric_entry(self,apply=True):
  d=self._numeric_entry
  if not d:return
  self._numeric_entry=None
  if apply:
   try:
    raw=d['entry'].get().strip().replace(',','.').replace('+','');val=float(raw);lo,hi=d['lo'],d['hi'];val=clamp(val,lo,hi);val=int(round(val)) if float(lo).is_integer() and float(hi).is_integer() else val
    if d['key']=='SEQ_STEPS':self.preset.sequence.length=int(val);self.status=f'STEPS = {int(val)}'
    else:self.set_value(d['key'],val,lo,hi)
   except Exception:self.status='Invalid numeric value'
  try:self.canvas.delete(d['window'])
  except Exception:pass
  try:d['entry'].destroy()
  except Exception:pass
  self.redraw()
 def hover_motion(self,e):
  if self.drag:return
  x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;hover=None;tool=None;modtip=None
  toolbar=next(((hx,hy+hh+4,key) for hx,hy,hw,hh,kind,key,data in self.hit if key in ('Settings','Theme') and hx<=x<=hx+hw and hy<=y<=hy+hh),None)
  if toolbar!=getattr(self,'_toolbar_tip',None):self._toolbar_tip=toolbar;self.redraw()
  for mh in reversed(self.hit):
   mx,my,mw,mhgt,mkind,mkey,mdata=mh
   if mkind=='modamount' and mx<=x<=mx+mw and my<=y<=my+mhgt:
    modtip=(mdata[1],mx,my+mhgt+7);break
  for h in reversed(self.hit):
   hx,hy,hw,hh,kind,key,data=h
   if hx<=x<=hx+hw and hy<=y<=hy+hh:
    if kind=='envpoint':hover=(key,data[0])
    if kind=='libtool':tool=(key,hx,hy+hh+4)
    if kind=='modamount':modtip=(data[1],hx,hy+hh+7)
    if kind=='dropdown_item':
     if data!=self.dropdown_hover:self.dropdown_hover=data;self.redraw()
     break
    break
  if self.open_dropdown and self.dropdown_hover is not None and self._hit_at(x,y) and self._hit_at(x,y)[4]!='dropdown_item':
   self.dropdown_hover=None;self.redraw()
  if hover!=self._env_hover:self._env_hover=hover;self.redraw()
  current=self._lib_tooltip[2] if self._lib_tooltip else None
  wanted=tool[0] if tool else None
  if wanted!=current:
   if self._lib_tooltip_job:
    try:self.after_cancel(self._lib_tooltip_job)
    except Exception:pass
    self._lib_tooltip_job=None
   if self._lib_tooltip:self._lib_tooltip=None;self.redraw()
   if tool:
    msg,tx,ty=tool;self._lib_tooltip_job=self.after(900,lambda m=msg,a=tx,b=ty:self._show_lib_tooltip(a,b,m))
  current_mod=self._mod_tooltip[2] if self._mod_tooltip else None
  wanted_mod='\n'.join(f'{src}  {amt:+d}' for src,amt in modtip[0]) if modtip else None
  if wanted_mod!=current_mod:
   if self._mod_tooltip_job:
    try:self.after_cancel(self._mod_tooltip_job)
    except Exception:pass
    self._mod_tooltip_job=None
   if self._mod_tooltip:self._mod_tooltip=None;self.redraw()
   if modtip:
    routes,tx,ty=modtip;self._mod_tooltip_job=self.after(400,lambda a=tx,b=ty,r=list(routes):self._show_mod_tooltip(a,b,r))

 def _show_lib_tooltip(self,x,y,msg):
  self._lib_tooltip_job=None;self._lib_tooltip=(x,y,msg);self.redraw()
 def motion(self,e):
  if not self.drag:return
  x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;kind=self.drag[4]
  if kind=='slider':self._set_slider(self.drag,x,y);self._set_popup(self.drag,x,y)
  elif kind=='seq_steps':self._set_seq_steps(self.drag,x)
  elif kind=='pitchwheel':self._wheel_pitch(y,self.drag[1],self.drag[3])
  elif kind=='modwheel':self._wheel_mod(y,self.drag[1],self.drag[3])
  elif kind in ('lfo_wave','osc_wave'):
   oy,ov=self._drag_origin;v=round(clamp(ov+(oy-y)*1.5,0,127));self.set_value(self.drag[5],v,0,127)
   if kind=='lfo_wave':shape=('SINE','TRIANGLE','UP SAW','DOWN SAW','SQUARE','RANDOM','S&H','NOISE')[min(7,int(v*8/128))]
   else:shape='TRIANGLE' if v<32 else ('SAW' if v<64 else ('SAW→SQUARE' if v<96 else 'PWM'))
   self.popup=(self.drag[0]+self.drag[2]/2,self.drag[1]-18,f'{v}  {shape}')
  elif kind=='envpoint':self._drag_env_point(self.drag,x,y)
  elif kind=='seqbar':self._seqbar(self.drag[5],self.drag[6],y,self.drag[1],self.drag[3])
  elif kind=='modlane':self._modlane_step(x,y,self.drag[6])
  elif kind=='modpencil':self._modpencil(x,y,self.drag[6])
  elif kind=='seq_vscroll':self._seq_vscroll(y,self.drag[6])
  elif kind=='seq_hscroll':self._seq_hscroll(x,self.drag[6])
  elif kind=='libxscroll':self._lib_xscroll(x,self.drag[6])
  elif kind in ('libdrag','songdrag'):
   if self._lib_drag_origin:
    ox,oy=self._lib_drag_origin
    if math.hypot(x-ox,y-oy)>=6:self._lib_drag_started=True;self._lib_drag_pos=(x,y);self.redraw()
 def _draw_library_drag_feedback(self):
  try:
   x,y=self._lib_drag_pos;payload=self.drag[6] if self.drag and self.drag[4] in ('libdrag','songdrag') else {}
   name=Path(payload.get('path','Preset')).name if payload.get('path') else (f"UNO {payload.get('slot',0):03d}" if payload.get('slot') else 'Preset')
   target=self._hit_at(x,y)
   if target and target[4] in ('libfoldertree','libfilescroll','libpreset','songcell'):
    hx,hy,hw,hh=target[:4];self.rect(hx,hy,hw,hh,'#1b2428',ORANGE)
   w=min(240,max(90,12+len(name)*7));self.rect(x+14,y+12,w,26,'#11171a',ORANGE);self.text(x+22,y+25,name,9,TEXT,'w')
  except Exception:pass
 def _lib_xscroll(self,x,d):
  usable=max(1,float(d['w'])-float(d['thumb']));frac=clamp((x-float(d['x'])-float(d['thumb'])/2)/usable,0,1)
  idx=int(self.drag[5]) if self.drag and self.drag[4]=='libxscroll' else 0;self.lib_hscroll[idx]=round(frac*float(d['max']));self.redraw()
 def _drag_env_point(self,h,x,y):
  _,_,_,_,_,key,data=h;idx,gx,gy,gw,gh=data;nx=clamp((x-gx-5)/(gw-10),.03,.96);ny=clamp((y-gy-5)/(gh-10),.08,.90)
  A=self._env_visual_norm(self.values.get(key+'_A',0));D=self._env_visual_norm(self.values.get(key+'_D',0));S=clamp(self.values.get(key+'_S',127)/127,0,1)
  xa=.03+.27*A;xd=xa+.27*D;sx=(.69 if S>=.03 else xd);updates=[]
  if idx==0:updates=[(key+'_A',self._env_visual_raw((nx-.03)/.27))]
  elif idx==1:updates=[(key+'_D',self._env_visual_raw((nx-xa)/.27)),(key+'_S',round(clamp(1-(ny-.10)/.78,0,1)*127))]
  elif idx==2:updates=[(key+'_S',round(clamp(1-(ny-.10)/.78,0,1)*127))]
  else:updates=[(key+'_R',self._env_visual_raw((nx-sx)/.27))]
  for k,v in updates:
   v=int(clamp(v,0,127));self.values[k]=v
   if k in CC:self._send_cc_ui(k,self._encode_cc_value(k,v,0,127))
  if updates:self.status=' / '.join(f'{k} = {v}' for k,v in updates);self._ensure_animation();self.redraw()
 def release(self,e):
  if self.drag and self.drag[4]=='songdrag':
   payload=self.drag[6];x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;target=self._hit_at(x,y);started=self._lib_drag_started
   self.drag=None;self._lib_drag_origin=None;self._lib_drag_started=False;self._lib_drag_pos=None
   if started and target and target[4]=='songcell' and self.song_mode=='LIVE':self._song_cell(int(target[5]))
   if started and target and target[4]=='songcell' and self.song_mode=='SONG':
    try:
     path=Path(payload['path']);idx=int(target[5]);name=str(payload.get('name') or path.stem)
     try:name=storage.load_preset(path).name or name
     except Exception:logger.exception('Preset metadata read failed during song drop; using drag label')
     self.song.slots[idx]=SongSlot(preset_path=str(path),preset_name=name);self.selected_song_slot=idx;self.status=f'{name} → SONG {idx+1:02d}'
    except Exception:logger.exception('Failed to drop preset into song slot')
   self.redraw();return 'break'
  if self.drag and self.drag[4]=='libdrag':
   payload=self.drag[6];x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;target=self._hit_at(x,y)
   started=self._lib_drag_started
   self.drag=None;self._lib_drag_origin=None;self._lib_drag_started=False;self._lib_drag_pos=None
   if started:self._handle_library_drop(payload,target)
   else:
    pass
   self.redraw();return 'break'
  if self.drag and self.drag[4]=='key':pass
  # release all mouse-played keys to avoid stuck notes
  had_keys=bool(self.keys_down)
  for n in list(self.keys_down):self.midi.note_off(n);self.keys_down.discard(n)
  if had_keys:self._env_note_off()
  if self.drag and self.drag[4]=='pitchwheel':self.midi.pitch_bend(0);self.pitch_visual=0
  self._flush_pending_cc()
  self.drag=None;self.popup=None;self.redraw()

 def _handle_library_drop(self,payload,target):
  if not target:return
  kind=target[4];key=target[5];data=target[6];src=payload.get('source')
  # Resolve a LOCAL destination folder from tree or a LOCAL panel background.
  dest=None
  if kind=='libfoldertree':
   p,_,fk=data;dest=Path(p)
  elif kind=='libfilescroll':
   if int(key)==0:dest=Path(self.lib_panel_folder[0] or storage.PRESETS)
   elif int(key)==1 and self.lib_right_mode=='LOCAL':dest=Path(self.lib_right_folder or storage.PRESETS)
  elif kind=='libpreset':dest=Path(data[0]).parent
  if src=='local':
   path=Path(payload['path'])
   if kind=='hwslot':
    self._select_hw_preset(key);self.status='Drop target selected — permanent Send remains locked';self.store_locked();return
   if dest and dest.is_dir() and path.parent.resolve()!=dest.resolve():
    try:
     dst=dest/path.name;i=2
     while dst.exists():dst=dest/f'{path.stem} {i}{path.suffix}';i+=1
     shutil.move(str(path),str(dst));storage.invalidate_preset_cache();self.lib_selected=dst;self.status=f'Moved to {dest.name}';self.redraw()
    except Exception as ex:self._notify('Move preset',str(ex),True)
  elif src=='folder':
   path=Path(payload['path'])
   if dest and dest.is_dir() and path!=dest and path not in dest.parents and path.parent.resolve()!=dest.resolve():
    try:
     dst=dest/path.name;i=2
     while dst.exists():dst=dest/f'{path.name} {i}';i+=1
     shutil.move(str(path),str(dst));storage.invalidate_preset_cache();self.lib_panel_folder[0]=dst;self.status=f'Moved folder to {dest.name}';self.redraw()
    except Exception as ex:self._notify('Move folder',str(ex),True)
  elif src=='uno':
   if not dest or not dest.is_dir():return
   slot=int(payload['slot']);self.status=f'Reading UNO {slot:03d}…';self.redraw()
   # Give the requested 0x37 refresh time to arrive before serializing the dropped slot.
   self.after(180,lambda s=slot,d=dest:self._save_uno_drop(s,d))

 def _save_uno_drop(self,slot,dest):
  try:
   p=copy.deepcopy(self.preset);p.number=int(slot);p.name=self.hardware_names.get(int(slot)) or f'UNO {int(slot):03d}';p.params=self._collect_params()
   out=Path(dest)/(storage._safe(p.name)+'.unosyp');i=2
   while out.exists():out=Path(dest)/f'{storage._safe(p.name)} {i}.unosyp';i+=1
   p.save(out);storage.invalidate_preset_cache();self.lib_selected=out;self.status=f'Received UNO {int(slot):03d} to {Path(dest).name}';self.redraw()
  except Exception as ex:self._notify('Receive preset',str(ex),True)

 def wheel(self,e):
  x=(e.x-self.ox)/self.scale;y=(e.y-self.oy)/self.scale;d=1 if e.delta>0 else -1
  if self.open_dropdown:
   if not self.open_dropdown.get('picker'):self._scroll_dropdown(-d)
   return 'break'
  if self.page=='SONG' and self.song_mode=='SONG' and 12<=x<=272 and 105<=y<=974:
   rows=self._song_tree_rows();visible=max(1,int((974-152)//25));self.song_folder_scroll=clamp(self.song_folder_scroll-d,0,max(0,len(rows)-visible));self.redraw();return 'break'
  if self.page=='ARP + SEQUENCER' and 315<=x<=1255:
   if 118<=y<=516 and not (e.state & 0x0001):
    self.seq_note_low=max(12,min(75,self.seq_note_low+d));self.redraw();return 'break'
   if 118<=y<=982:
    self.seq_hscroll=max(0,min(48,self.seq_hscroll-d));self.redraw();return 'break'
  if self.page=='SYNTH' and 10<=x<=1248 and 690<=y<=982:
   self.matrix_scroll=max(0,min(12,self.matrix_scroll-d));self.redraw();return 'break'
  if self.page=='LIBRARY':
   hw_scroll=next((h for h in reversed(self.hit) if h[4]=='libhwscroll' and h[0]<=x<=h[0]+h[2] and h[1]<=y<=h[1]+h[3]),None)
   if hw_scroll:
    _,_,_,_,_,key,max_scroll=hw_scroll;self.lib_hscroll[key]=clamp(self.lib_hscroll[key]-d*140,0,max_scroll or 0);self.redraw();return 'break'
  for h in reversed(self.hit):
   hx,hy,hw,hh,kind,key,data=h
   if hx<=x<=hx+hw and hy<=y<=hy+hh:
    if kind=='libhwscroll':self.lib_hscroll[key]=clamp(self.lib_hscroll[key]-d*140,0,data or 0);self.redraw();return 'break'
    if kind=='libfilescroll':self.lib_hscroll[key]=clamp(self.lib_hscroll[key]-d*140,0,data or 0);self.redraw();return 'break'
    if kind=='slider':
     lo,hi,vert,bip=data;self.set_value(key,clamp(self.values.get(key,lo)+d,lo,hi),lo,hi);self._set_popup(h);self.after(700,self._clear_popup)
    elif kind=='seq_steps':
     self.preset.sequence.length=clamp(int(self.preset.sequence.length)+d,1,64);self.popup=(hx+hw/2,hy-22,str(int(self.preset.sequence.length)));self.redraw();self.after(700,self._clear_popup)
    elif kind=='choice':
     if self.open_dropdown and self.open_dropdown['key']==key:self._scroll_dropdown(-d)
    elif kind=='dropdown_item':
     if self.open_dropdown:self._scroll_dropdown(-d)
    elif kind=='choice_dir':self._cycle_choice(key,data[0],d)
    return
 def _format_popup_value(self,key,v,bip=False):
  try:
   if key in ('LFO1_FADE','LFO2_FADE') and float(v)==0:return 'OFF'
   fv=float(v);iv=int(round(fv));txt=str(iv) if abs(fv-iv)<1e-9 else f'{fv:.2f}'.rstrip('0').rstrip('.')
   if bip and fv>0:txt='+'+txt
   return txt
  except Exception:return str(v)
 def _set_popup(self,h,x=None,y=None):
  hx,hy,hw,hh,kind,key,data=h
  v=self.values.get(key,0);bip=data[3] if data else False;txt=self._format_popup_value(key,v,bip)
  self.popup=((x if x is not None else hx+hw/2),(y-24 if y is not None else hy-22),txt)
  self.redraw()
 def _set_hw_popup(self,key):
  # Hardware-originated changes show their value by the visible control, never at a stale mouse position.
  for h in reversed(self.hit):
   hx,hy,hw,hh,kind,hkey,data=h
   if kind=='slider' and hkey==key:
    bip=data[3] if data else False;self.popup=(hx+hw/2,hy-22,self._format_popup_value(key,self.values.get(key,0),bip));break
  if self._popup_clear_job is not None:
   try:self.after_cancel(self._popup_clear_job)
   except Exception:pass
  self._popup_clear_job=self.after(700,self._clear_popup)
 def _clear_popup(self):
  if not self.drag:self.popup=None;self.redraw()
 def _draw_value_popup(self):
  x,y,txt=self.popup;tw=max(38,12+len(txt)*9)
  self.rect(x-tw/2,y-12,tw,24,'#252b2f',LIGHT_GREY,1);self.text(x,y,txt,10,LIGHT_GREY,'center',True)
 def _set_slider(self,h,x,y):
  hx,hy,hw,hh,kind,key,data=h;lo,hi,vert,bip=data;t=clamp(1-(y-hy)/hh,0,1) if vert else clamp((x-hx)/hw,0,1);v=lo+t*(hi-lo);self.set_value(key,round(v),lo,hi)
 def _encode_cc_value(self,key,v,lo=0,hi=127):
  if key in ('FILTER_SPACING','F1_ENV','F2_ENV'):return max(0,min(127,int(round(v+63))))
  if key in ('F1_TRACK','F2_TRACK'):
   v=float(v)
   return max(0,min(127,round((v+200)*63/200) if v<=0 else 63+round(v*64/200)))
  return norm(v,lo,hi)
 def _decode_cc_value(self,key,raw):
  raw=max(0,min(127,int(raw)))
  if key in ('FILTER_SPACING','F1_ENV','F2_ENV'):return raw-63
  if key in ('F1_TRACK','F2_TRACK'):
   return round(-200+raw*200/63) if raw<=63 else round((raw-63)*200/64)
  if key in ('OSC1_TUNE','OSC2_TUNE','OSC3_TUNE'):return round(denorm(raw,-24,24))
  if key.startswith('MAMT'):return round(denorm(raw,-64,64))
  return raw
 def _send_cc_ui(self,key,value):
  # Coalesce only high-frequency mouse drags. Clicks, wheel moves and numeric entry stay immediate.
  drag_kind=self.drag[4] if self.drag else None
  if drag_kind not in ('slider','lfo_wave','osc_wave','envpoint'):
   self._cc_pending.pop(key,None)
   job=self._cc_jobs.pop(key,None)
   if job is not None:
    try:self.after_cancel(job)
    except tk.TclError:pass
   self.midi.send_cc(CC[key],value);self._cc_last_sent[key]=(time.monotonic(),value);return
  now=time.monotonic();last_t,last_v=self._cc_last_sent.get(key,(0.0,None))
  if value==last_v and key not in self._cc_pending:return
  elapsed=now-last_t
  if elapsed>=self._cc_interval:
   self.midi.send_cc(CC[key],value);self._cc_last_sent[key]=(now,value);return
  self._cc_pending[key]=value
  if key not in self._cc_jobs:
   delay=max(1,int(round((self._cc_interval-elapsed)*1000)))
   self._cc_jobs[key]=self.after(delay,lambda k=key:self._flush_pending_cc(k))
 def _flush_pending_cc(self,key=None):
  keys=[key] if key is not None else list(self._cc_pending)
  for k in keys:
   job=self._cc_jobs.pop(k,None)
   if job is not None:
    try:self.after_cancel(job)
    except tk.TclError:pass
   if k not in self._cc_pending:continue
   value=self._cc_pending.pop(k)
   self.midi.send_cc(CC[k],value);self._cc_last_sent[k]=(time.monotonic(),value)
 def _apply_extended_preset_fields(self,ext):
  if not isinstance(ext,dict):return
  if 'voice_mode' in ext:self.choice['VOICE']=max(0,min(2,int(ext['voice_mode'])))
  if 'arp_direction' in ext:self.choice['ARP_MODE']=int(ext['arp_direction'])
  if 'arp_range' in ext:self.values['ARP_RANGE']=f"{int(ext['arp_range'])} OCT"
  if 'arp_pattern' in ext:
   mask=int(ext['arp_pattern']);self.arp_trig=[bool(mask&(1<<i)) for i in range(16)]
  for i,route in enumerate(ext.get('matrix',[])[:16]):
   src=route.get('source');dst=route.get('destination')
   if src is not None and 0<=int(src)<len(MATRIX_SOURCES):self.values[f'MSRC{i}']=MATRIX_SOURCES[int(src)]
   if dst is not None and 0<=int(dst)<len(MATRIX_DESTINATIONS):self.values[f'MDST{i}']=MATRIX_DESTINATIONS[int(dst)]

 def set_value(self,key,v,lo=0,hi=127,send=True):
  self.values[key]=v
  if key in CC and send:self._send_cc_ui(key,self._encode_cc_value(key,v,lo,hi))
  self.status=f'{key} = {v}';self.redraw()
  if key.startswith('MAMT') or key.startswith('LFO') or key.startswith('FENV_') or key.startswith('AENV_'):self._ensure_animation()
 def set_filter_link(self,state):
  self.filter_link=0 if self.filter_link==state else state
  self.midi.send_cc(CC['FILTER_LINK'],self.filter_link);self.status=f'FILTER LINK CC41 = {self.filter_link}';self.redraw()
 def toggle_param(self,key):
  self.toggle[key]=not self.toggle.get(key,False)
  if key in CC:self.midi.send_cc(CC[key],127 if self.toggle[key] else 0)
  self.redraw()
 def set_choice(self,key,j):self.choice[key]=j;self.redraw()
 def set_mod_sub(self,j):
  mt=max(0,min(2,int(self.choice.get('MOD_TYPE',0))));count=3 if mt==0 else (2 if mt==1 else 0)
  if count<=0:return
  self.choice['MOD_SUB']=max(0,min(count-1,int(j)))
  # Hardware-confirmed captures: CC98 Chorus Mode = 0/42/84; CC96 Phaser Color = 0/127.
  if mt==0:self.midi.send_cc(CC['CHORUS_MODE'],[0,42,84][self.choice['MOD_SUB']])
  elif mt==1:self.midi.send_cc(CC['MOD_INTENSITY'],[0,127][self.choice['MOD_SUB']])
  self.redraw()
 def set_fx_choice(self,key,j,count):
  limits={'MOD_TYPE':3,'DELAY_TYPE':5,'REVERB_TYPE':4};n=limits.get(key,count);j=max(0,min(n-1,int(j)));self.choice[key]=j
  if key=='MOD_TYPE':self.choice['MOD_SUB']=0
  if key in CC:
   raws={'MOD_TYPE':[0,42,84],'DELAY_TYPE':[0,25,50,75,100],'REVERB_TYPE':[0,32,64,96]}.get(key)
   self.midi.send_cc(CC[key],raws[j] if raws else round(j*127/max(1,n-1)))
  self.redraw()
 def _cycle_choice(self,key,opts,d):
  if key in self.settings:
   cur=self.settings.get(key);vals=list(opts);idx=vals.index(cur) if cur in vals else 0;self.settings[key]=vals[(idx+d)%len(vals)]
   if key=='pr_change':self.settings[key]=True
   self.settings_dirty=(self.settings!=self._applied_settings);self.status='Settings changed — APPLY';self.redraw();return
  if key=='preset':return
  if key=='SONG_TEMPO':self.song.tempo=int(opts[(opts.index(self.song.tempo)+d)%len(opts)]);self.redraw();return
  if key=='SONG_LENGTH':self.song.length=int(opts[(opts.index(self.song.length)+d)%len(opts)]);self.redraw();return
  if key=='LIVE_DELAY':self.live_delay=int(opts[(opts.index(self.live_delay)+d)%len(opts)]);self.redraw();return
  if key=='SEQ_LEN':
   vals=list(opts);cur=self.preset.sequence.length;idx=vals.index(cur) if cur in vals else 0;self.preset.sequence.length=vals[(idx+d)%len(vals)];self.redraw();return
  if key=='SEQ_TRANS':
   vals=list(opts);cur=self.preset.sequence.transpose;self.preset.sequence.transpose=vals[(vals.index(cur)+d)%len(vals)];self.redraw();return
  if key.startswith('MSRC') or key.startswith('MDST'):
   cur=self.values.get(key,opts[0]);idx=opts.index(cur) if cur in opts else 0;self.values[key]=opts[(idx+d)%len(opts)];self.redraw();return
  if key in self.choice:
   vals=list(opts);idx=self.choice[key];self.choice[key]=(idx+d)%len(vals)
   # confirmed mode CCs are sent as 0..127 distributed across documented mode count
   if key in ('F1_MODE','F2_MODE'):
    cckey=key;self.midi.send_cc(CC[cckey],([0,25,50,75,100] if key=='F1_MODE' else [0,20,40,60,80,100])[self.choice[key]])
   elif key in ('MOD_TYPE','DELAY_TYPE','REVERB_TYPE') and key in CC:
    raws={'MOD_TYPE':[0,42,84],'DELAY_TYPE':[0,25,50,75,100],'REVERB_TYPE':[0,32,64,96]}[key];idx=max(0,min(len(raws)-1,self.choice[key]));self.midi.send_cc(CC[key],raws[idx])
   elif key=='ARP_MODE':self.midi.sysex(ARP_SYSEX['direction_prefix']+bytes([self.choice[key]&127,0xF7]))
   elif key=='ARP_OCT':self.midi.sysex(ARP_SYSEX['octaves_prefix']+bytes([max(1,min(4,int(self.choice[key])))&127,0xF7]))
   self.redraw()
 def _dropdown_current(self,key,opts):
  vals=list(opts)
  if not vals:return None
  if key in self.settings:return self.settings.get(key,vals[0])
  if key.startswith('LIBSRC'):
   try:return self.lib_panel_source[int(key[-1])]
   except Exception:return vals[0]
  if key=='SONG_TEMPO':return self.song.tempo
  if key=='SONG_LENGTH':return self.song.length
  if key=='LIVE_DELAY':return self.live_delay
  if key=='SEQ_LEN':return self.preset.sequence.length
  if key=='SEQ_TRANS':return self.preset.sequence.transpose
  if key=='SEQ_OVERDUB':return self.seq_overdub
  if key=='SEQ_RES':return self.seq_resolution
  if key=='SEQ_TARGET':return self.automation_parameter
  if key=='ARP_RANGE':return self.values.get('ARP_RANGE','1 OCT')
  if key=='SEQ_KB_RANGE':return self.values.get('SEQ_KB_RANGE','C2')
  if key.startswith('MSRC') or key.startswith('MDST'):return self.values.get(key,vals[0])
  if key in self.choice:
   i=self.choice.get(key,0);return vals[i] if 0<=i<len(vals) else vals[0]
  return vals[0]
 def _open_dropdown(self,h,key,opts):
  vals=list(opts)
  if not vals:return
  hx,hy,hw,hh,_,_,_=h;cur=self._dropdown_current(key,vals);idx=vals.index(cur) if cur in vals else 0
  self.dropdown_hover=None
  if key.startswith('MSRC') or key.startswith('MDST') or key=='SEQ_TARGET':
   self.open_dropdown={'x':hx,'y':hy,'w':hw,'h':hh,'key':key,'opts':vals,'picker':True}
  else:
   self.dropdown_scroll=max(0,min(idx,max(0,len(vals)-10)));self.open_dropdown={'x':hx,'y':hy,'w':hw,'h':hh,'key':key,'opts':vals,'picker':False}
  self.redraw()
 def _draw_dropdown_overlay(self):
  d=self.open_dropdown;vals=d['opts'];cur=self._dropdown_current(d['key'],vals)
  if d.get('picker'):
   # Large multi-column parameter picker: maximum options visible at once, no scrolling when they fit.
   row=29;panel_top=95;panel_bottom=820;max_rows=12 if d['key']=='SEQ_TARGET' else max(1,int((panel_bottom-panel_top-20)//row));cols=max(1,(len(vals)+max_rows-1)//max_rows);rows=min(max_rows,(len(vals)+cols-1)//cols)
   cell_w=285 if d['key'].startswith('MDST') else 245;panel_w=cols*cell_w+20;panel_h=rows*row+20
   left=clamp(d['x'],18,BASE_W-panel_w-18);top=clamp(d['y']-panel_h/2,75,BASE_H-panel_h-120)
   self.rect(left,top,panel_w,panel_h,'#11171a',LIGHT_GREY,1)
   for i,opt in enumerate(vals):
    col=i//rows;r=i%rows;xx=left+10+col*cell_w;yy=top+10+r*row;sel=(opt==cur);hov=(opt==self.dropdown_hover)
    if hov:self.rect(xx,yy,cell_w-8,row-2,ORANGE2,ORANGE)
    elif sel:self.rect(xx,yy,cell_w-8,row-2,'#30363a',LIGHT_GREY)
    label=('✓  ' if sel else '   ')+self._display_setting(opt)
    self.text(xx+8,yy+row/2,label,10,ORANGE if hov else (LIGHT_GREY if sel else TEXT),'w')
    self.hitbox(xx,yy,cell_w-8,row-2,'dropdown_item',d['key'],opt)
   return
  n=min(10,len(vals));off=max(0,min(self.dropdown_scroll,max(0,len(vals)-n)));self.dropdown_scroll=off
  x,y,w,h=d['x'],d['y'],d['w'],d['h'];row=max(28,h);down_space=BASE_H-(y+h)-8;up_space=y-8
  below=down_space>=row*n or down_space>=up_space;top=(y+h if below else y-row*n)
  self.rect(x,top,w,row*n,'#11171a',LIGHT_GREY if vals else EDGE,1)
  for j,opt in enumerate(vals[off:off+n]):
   yy=top+j*row;sel=(opt==cur);hov=(opt==self.dropdown_hover)
   if hov:self.rect(x+1,yy+1,w-2,row-2,ORANGE2,ORANGE)
   elif sel:self.rect(x+1,yy+1,w-2,row-2,'#30363a',LIGHT_GREY)
   self.text(x+12,yy+row/2,self._display_setting(opt),10,ORANGE if hov else (LIGHT_GREY if sel else TEXT),'w')
   self.hitbox(x,yy,w,row,'dropdown_item',d['key'],opt)
  if len(vals)>n:
   self.text(x+w-8,top+5,'▲' if off>0 else '',8,MUTED,'ne');self.text(x+w-8,top+row*n-5,'▼' if off<len(vals)-n else '',8,MUTED,'se')
 def _scroll_dropdown(self,d):
  if not self.open_dropdown or self.open_dropdown.get('picker'):return
  vals=self.open_dropdown['opts'];self.dropdown_scroll=clamp(self.dropdown_scroll+d,0,max(0,len(vals)-10));self.redraw()
 def _select_dropdown_value(self,key,value):
  opts=self.open_dropdown['opts'] if self.open_dropdown and self.open_dropdown.get('key')==key else [value]
  self.open_dropdown=None;self.dropdown_hover=None
  if key in self.settings:
   self.settings[key]=value
   if key=='pr_change':self.settings[key]=True
   self.settings_dirty=(self.settings!=self._applied_settings);self.status='Settings changed — APPLY';self.redraw();return
  if key.startswith('LIBSRC'):
   try:self.lib_panel_source[int(key[-1])]=str(value);self.redraw()
   except Exception:pass
   return
  if key=='preset':
   try:self._select_hw_preset(int(value))
   except Exception:pass
   return
  if key=='SONG_TEMPO':self.song.tempo=int(value);self.redraw();return
  if key=='SONG_LENGTH':self.song.length=int(value);self.redraw();return
  if key=='LIVE_DELAY':self.live_delay=0 if int(value)<=0 else max(5,min(60,int(value)));self.settings['live_delay']=self.live_delay;storage.save_settings(self.settings);self.redraw();return
  if key=='SEQ_LEN':self.preset.sequence.length=int(value);self.redraw();return
  if key=='SEQ_TRANS':self.preset.sequence.transpose=int(value);self.redraw();return
  if key=='SEQ_OVERDUB':self.seq_overdub=str(value);self.redraw();return
  if key=='SEQ_RES':self.seq_resolution=str(value);self.redraw();return
  if key=='SEQ_TARGET':self.automation_parameter=str(value);self.redraw();return
  if key=='ARP_RANGE':
   self.values[key]=value
   try:
    n=max(1,min(4,int(str(value).split()[0])));self.midi.sysex(ARP_SYSEX['octaves_prefix']+bytes([n&127,0xF7]))
   except Exception:logger.exception('ARP range send failed')
   self.redraw();return
  if key=='SEQ_KB_RANGE':self.values[key]=value;self.redraw();return
  if key.startswith('MSRC') or key.startswith('MDST'):
   self.values[key]=value;self.redraw();self._ensure_animation();return
  if key in self.choice:
   vals=list(opts);self.choice[key]=vals.index(value) if value in vals else 0
   if key in ('F1_MODE','F2_MODE'):self.midi.send_cc(CC[key],([0,25,50,75,100] if key=='F1_MODE' else [0,20,40,60,80,100])[self.choice[key]])
   elif key in ('MOD_TYPE','DELAY_TYPE','REVERB_TYPE') and key in CC:
    raws={'MOD_TYPE':[0,42,84],'DELAY_TYPE':[0,25,50,75,100],'REVERB_TYPE':[0,32,64,96]}[key];idx=max(0,min(len(raws)-1,self.choice[key]));self.midi.send_cc(CC[key],raws[idx])
   elif key=='ARP_MODE':self.midi.sysex(ARP_SYSEX['direction_prefix']+bytes([self.choice[key]&127,0xF7]))
   elif key=='ARP_OCT':self.midi.sysex(ARP_SYSEX['octaves_prefix']+bytes([max(1,min(4,int(value)))&127,0xF7]))
   self.redraw()
 def _piano_cell(self,d,x,y):
  col=int((x-d['gx'])/(d['gw']/d['visible']));s=d.get('first',0)+col;r=int((y-d['gy'])/(d['gh']/d['rows']));note=d.get('top_note',57)-r
  return s,r,note
 def _piano_edit(self,d,x,y):
  s,r,note=self._piano_cell(d,x,y)
  if 0<=s<64 and 12<=note<=96 and 0<=r<d['rows']:
   st=self.preset.sequence.steps[s];self.selected_seq_step=s
   if note in st.notes:
    self.selected_seq_note=(s,note)
   elif len(st.notes)<(1 if self.seq_overdub=='MONO' else 3):
    st.notes.append(note);self.selected_seq_note=(s,note);self.sequence_origin='SOFTWARE'
   self.redraw()
 def _piano_delete(self,d,x,y):
  s,r,note=self._piano_cell(d,x,y)
  if 0<=s<64 and 0<=r<d['rows']:
   st=self.preset.sequence.steps[s]
   if note in st.notes:
    st.notes.remove(note);self.selected_seq_step=s;self.selected_seq_note=None;self.sequence_origin='SOFTWARE';self.redraw();return True
  return False
 def _seqbar(self,s,param,y,hy,hh):
  t=clamp(1-(y-hy)/hh,0,1);st=self.preset.sequence.steps[s]
  if param=='GATE':st.gate=round(t*10)
  elif param=='ACC':st.accent=round(t*127)
  elif param=='VELOCITY':st.velocity=round(t*127)
  else:st.length=round((0.5+t*3.5)*10)/10
  self.redraw()

 def _modlane_step(self,x,y,d):
  gx,gy,gw,gh,visible=d['gx'],d['gy'],d['gw'],d['gh'],d['visible'];col=int(clamp((x-gx)/(gw/visible),0,visible-1));s=d.get('first',0)+col;t=clamp(1-(y-gy)/gh,0,1)
  lane=self.automation_lane();metadata=PARAMETERS[lane['parameter']]
  if metadata.minimum is None or metadata.status.startswith('PARTIAL') or lane.get('units')!='device-ui':return
  vals=lane.setdefault('values',[None]*64)
  while len(vals)<64:vals.append(64)
  vals[s]=metadata.value(t)
  fine=lane.setdefault('fine_values',[[None]*4 for _ in range(64)])
  while len(fine)<64:fine.append([None]*4)
  fine[s]=[None]*4;self.popup=(x,y-18,str(vals[s]));self.redraw()
 def _modpencil(self,x,y,d):
  return self._modlane_step(x,y,d)
 def _seq_vscroll(self,y,d):
  top=d['y']+4;usable=d['h']-8-d['thumb'];frac=clamp((y-top-d['thumb']/2)/max(1,usable),0,1);self.seq_note_low=round(75-frac*63);self.redraw()
 def _seq_hscroll(self,x,d):
  usable=d['w']-d['thumb'];frac=clamp((x-d['x']-d['thumb']/2)/max(1,usable),0,1);self.seq_hscroll=round(frac*48);self.redraw()
 def _modbar(self,s,y,hy,hh):
  return self._modlane_step(0,y,{'gx':0,'gy':hy,'gw':1,'gh':hh,'visible':1,'first':s})
 def toggle_selected_tie(self):
  s=clamp(self.selected_seq_step,0,63);self.preset.sequence.steps[s].tie=not self.preset.sequence.steps[s].tie;self.redraw()
 def seq_copy(self):
  self.seq_clipboard=copy.deepcopy(self.preset.sequence);self.status='Sequence copied';self.redraw()
 def seq_paste(self):
  if self.seq_clipboard is not None:self.sequence_origin='SOFTWARE';self.preset.sequence=copy.deepcopy(self.seq_clipboard);self.status='Sequence pasted'
  self.redraw()
 def set_seq_timing(self,v):self.seq_timing=v;self.redraw()
 def set_seq_visible(self,n):self.seq_visible=n;self.redraw()
 def _set_seq_steps(self,h,x):
  hx,hy,hw,hh,kind,key,data=h;v=1+round(clamp((x-hx)/max(1,hw),0,1)*63)
  if int(self.preset.sequence.length)!=v:self.preset.sequence.length=v
  self.popup=(hx+hw/2,hy-22,str(v));self.redraw()
 def change_seq_steps(self,d):
  self.preset.sequence.length=max(1,min(64,int(self.preset.sequence.length)+int(d)));self.redraw()
 def set_seq_param(self,p):self.seq_param=p;self.redraw()
 def set_mod(self,i):self.seq_mod=i;self.redraw()
 def automation_lane(self):return parameter_line(self.preset.sequence,getattr(self,'automation_parameter','CUTOFF 1'))
 def seq_duplicate(self):
  try:self.preset.sequence.duplicate();self.sequence_origin='SOFTWARE';self.status='Sequence duplicated'
  except ValueError as error:self.status=str(error)
  self.redraw()
 def seq_fill(self):
  self.sequence_origin='SOFTWARE';self.preset.sequence.fill64(self.preset.sequence.length);self.status='Sequence repeated to 64 steps';self._seq_fill_flash=True;self.redraw();self.after(900,self._clear_seq_fill_flash)
 def _clear_seq_fill_flash(self):self._seq_fill_flash=False;self.redraw()
 def seq_clear_request(self):
  win=tk.Toplevel(self);win.title('INIT SEQUENCE');win.configure(bg=ui_theme.color(BG));win.resizable(False,False);win.transient(self);win.grab_set()
  ww,hh=360,150;win.geometry(f'{ww}x{hh}+{self.winfo_rootx()+max(0,(self.winfo_width()-ww)//2)}+{self.winfo_rooty()+max(0,(self.winfo_height()-hh)//2)}')
  tk.Label(win,text='Initialize sequence?',bg=BG,fg=TEXT,font=('Segoe UI',12,'bold')).pack(pady=(25,18))
  row=tk.Frame(win,bg=BG);row.pack()
  def yes():win.destroy();self.seq_clear()
  def no():win.destroy()
  for txt,cmd in [('YES',yes),('NO',no)]:tk.Button(row,text=txt,command=cmd,bg=PANEL2,fg=TEXT,activebackground=ORANGE2,activeforeground=WHITE,relief='solid',bd=1,width=10,font=('Segoe UI',10,'bold')).pack(side='left',padx=8)
  win.bind('<Escape>',lambda e:no());win.bind('<Return>',lambda e:yes())
 def seq_clear(self):
  self.sequence_origin='SOFTWARE';self.preset.sequence=Sequence();self.redraw()
 def toggle_arp(self,i):
  self.arp_trig[i]=not self.arp_trig[i]
  mask=sum((1<<j) for j,on in enumerate(self.arp_trig[:16]) if on)
  try:self.midi.sysex(bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x3C,0x00,0x02,mask&0x7F,(mask>>7)&0x7F,(mask>>14)&0x03,0xF7]))
  except Exception:logger.exception('ARP pattern send failed')
  self.redraw()
 def toggle_arp_on(self):
  self.arp_on=not self.arp_on
  # Confirmed in official-editor capture: editor -> UNO 35 00 <0|1> after hardware 34 06 <0|1>.
  msg=IK_HEADER+bytes([0x35,0x00,1 if self.arp_on else 0,0xF7])
  ok=self.midi.sysex(msg)
  self.status=('ARP ON' if self.arp_on else 'ARP OFF') + (' → UNO' if ok else ' — MIDI send failed')
  self.redraw()
 def _seq_all_notes_off(self):
  for job in list(self._seq_noteoff_jobs.values()):
   try:self.after_cancel(job)
   except Exception:pass
  self._seq_noteoff_jobs.clear()
  for n in list(self._seq_active_notes):self.midi.note_off(n)
  self._seq_active_notes.clear()
 def _seq_release_note(self,n):
  self._seq_noteoff_jobs.pop(n,None)
  if n in self._seq_active_notes:self.midi.note_off(n);self._seq_active_notes.discard(n)
 def _play_seq_step(self,idx):
  seq=self.preset.sequence;ln=max(1,min(64,int(seq.length)));idx=max(0,min(ln-1,int(idx)));st=seq.steps[idx]
  # Step automation is sent before notes. Only monitor-confirmed UNO CC targets are used.
  target_cc={'CUTOFF 1':28,'CUTOFF 2':35,'RESONANCE 1':29,'RESONANCE 2':36,'WAVE 1':12,'WAVE 2':13,'WAVE 3':14,'SPACING':40,'FM 1':25,'FM 2':26}
  for lane in seq.automation:
   cc=target_cc.get(str(lane.get('parameter','')).upper())
   # Device UI units are not MIDI bytes. Only legacy/captured raw CC values may use this existing mapping.
   vals=lane.get('cc_values',[]) if lane.get('units')=='device-ui' else lane.get('values',[])
   if cc is not None and idx<len(vals) and vals[idx] is not None:self.midi.send_cc(cc,max(0,min(127,int(vals[idx]))))
  # Probability is evaluated once per step. Empty steps remain silent.
  if st.notes and random.randint(1,100)<=max(0,min(100,int(st.probability))):
   notes={max(0,min(127,int(n)+int(seq.transpose))) for n in st.notes[:3]}
   # Notes not continued by a tie are released before the new step.
   if not st.tie:
    for n in list(self._seq_active_notes):
     if n not in notes:self._seq_release_note(n)
   vel=max(1,min(127,int(st.velocity)))
   for n in notes:
    if n not in self._seq_active_notes:self.midi.note_on(n,vel);self._seq_active_notes.add(n)
   if not st.tie:
    # Clock-derived 1/16 duration; gate 0..10. Fall back to 125 ms at 120 BPM.
    step_ms=max(20,int(self._seq_clock_interval*6*1000));gate=max(1,min(10,int(st.gate or round(float(st.length)*10))))
    off_ms=max(5,int(step_ms*gate/10))
    for n in notes:
     old=self._seq_noteoff_jobs.pop(n,None)
     if old:
      try:self.after_cancel(old)
      except Exception:pass
     self._seq_noteoff_jobs[n]=self.after(off_ms,lambda n=n:self._seq_release_note(n))
  elif not st.tie:self._seq_all_notes_off()
 def _clock_master_start(self):
  self._clock_master_stop()
  if self.settings.get('sync','USB')=='USB' and self.settings.get('midi_clock')=='MIDI MASTER':self._clock_master_tick()
 def _clock_master_stop(self):
  if self._clock_master_job is not None:
   try:self.after_cancel(self._clock_master_job)
   except Exception:pass
  self._clock_master_job=None
 def _clock_master_tick(self):
  if not self.seq_playing:return
  self.midi.clock();self._seq_clock()
  bpm=max(20,min(300,int(getattr(self.song,'tempo',120) or 120)));interval=max(1,round(60000/(bpm*24)));self._clock_master_job=self.after(interval,self._clock_master_tick)
 def toggle_seq_play(self):
  self.seq_playing=not self.seq_playing
  if self.seq_playing:
   self.seq_record_step=0;self.selected_seq_step=0;self._seq_clock_count=0;self._seq_last_clock_time=None;self.midi.start();self._play_seq_step(0);self._clock_master_start();self.status='PLAY — transport sent; MIDI Clock active' if self._clock_master_job is not None else 'PLAY — transport sent; internal/external clock'
  else:
   self._clock_master_stop();self._seq_all_notes_off();self.midi.stop();self.status='PLAY STOPPED'
  self.redraw()
 def toggle_seq_record(self):
  self.seq_recording=not self.seq_recording
  if self.seq_recording:
   self.seq_record_step=0;self._seq_clock_count=0;self.status='REC — notes + selected parameter automation'
  else:self.status='REC OFF'
  self.redraw()
 def _record_note(self,note,velocity):
  if not self.seq_recording:return
  idx=max(0,min(63,int(self.seq_record_step)));st=self.preset.sequence.steps[idx]
  if self.seq_overdub=='MONO':st.notes=[note]
  elif note not in st.notes and len(st.notes)<3:st.notes.append(note)
  st.velocity=max(1,min(127,int(velocity)));self.selected_seq_step=idx
 def _record_automation_cc(self,cc,value):
  if not self.seq_recording:return
  target_by_cc={28:'CUTOFF 1',35:'CUTOFF 2',29:'RESONANCE 1',36:'RESONANCE 2',12:'WAVE 1',13:'WAVE 2',14:'WAVE 3',40:'SPACING',25:'FM 1',26:'FM 2'}
  lane=self.automation_lane();target=lane.get('parameter','CUTOFF 1')
  if target_by_cc.get(cc)!=target:return
  idx=max(0,min(63,int(self.seq_record_step)));vals=lane.setdefault('cc_values' if lane.get('units')=='device-ui' else 'values',[None]*64)
  while len(vals)<64:vals.append(64)
  vals[idx]=max(0,min(127,int(value)))
 def _seq_clock(self):
  if not (self.seq_playing or self.seq_recording):return
  now=time.monotonic()
  if self._seq_last_clock_time is not None:
   dt=now-self._seq_last_clock_time
   if .002<dt<.25:self._seq_clock_interval=self._seq_clock_interval*.8+dt*.2
  self._seq_last_clock_time=now;self._seq_clock_count+=1
  # MIDI clock = 24 PPQN; 6 clocks per 1/16 step.
  if self._seq_clock_count>=6:
   self._seq_clock_count=0;ln=max(1,min(64,int(self.preset.sequence.length)));self.seq_record_step=(self.seq_record_step+1)%ln;self.selected_seq_step=self.seq_record_step;self.seq_hscroll=min(48,(self.selected_seq_step//16)*16)
   if self.seq_playing:self._play_seq_step(self.seq_record_step)
   self.redraw()
 def _song_cell(self,i):
  if self.song_mode=='SONG':
   self.selected_song_slot=i
   if self.lib_selected:
    try:p=storage.load_preset(self.lib_selected);self.song.slots[i]=SongSlot(str(self.lib_selected),p.name)
    except Exception:logger.exception('Failed to load preset into song slot')
  else:
   self.selected_live_slot=i
   if self.selected_song_file:self.live_slots[i]=str(self.selected_song_file);self.settings['live_slots']=list(self.live_slots);storage.save_settings(self.settings)
  self.redraw()
 def clear_song_slot(self):self.song.slots[self.selected_song_slot]=SongSlot();self.redraw()
 def clear_song(self):self.song=Song();self.redraw()
 def save_song(self):
  n=self._ask_text('Save Song','Song name:',self.song.name)
  if n:self.song.name=n;storage.save_song(self.song);self.status=f'Song saved: {n}';self.redraw()
 def load_song_dialog(self):
  fs=storage.list_songs()
  if not fs:self._notify('Load Song','No songs in '+str(storage.SONGS));return
  p=filedialog.askopenfilename(initialdir=str(storage.SONGS),filetypes=[('UNO Song','*.unosong')])
  if p:self.song=Song.load(p);self.status='Song loaded';self.redraw()
 def toggle_live_play(self):
  if self.live_countdown_remaining>0:
   self._cancel_live_countdown();self.status='LIVE START CANCELLED';self.redraw();return
  if self.live_playing:
   self.midi.stop();self.live_playing=False;self.status='LIVE STOPPED';self.redraw();return
  
  if int(self.live_delay)<=0:
   self.midi.start();self.live_playing=True;self.status='LIVE PLAY';self.redraw();return
  self.live_countdown_remaining=max(5,min(60,int(self.live_delay)));self.status=f'LIVE START IN {self.live_countdown_remaining}s';self.redraw();self._schedule_live_countdown()
 def _schedule_live_countdown(self):
  if self._live_countdown_job is not None:
   try:self.after_cancel(self._live_countdown_job)
   except Exception:pass
  self._live_countdown_job=self.after(1000,self._live_countdown_tick)
 def _live_countdown_tick(self):
  self._live_countdown_job=None
  if self.live_countdown_remaining<=0:return
  self.live_countdown_remaining-=1
  if self.live_countdown_remaining<=0:
   self.midi.start();self.live_playing=True;self.status='LIVE PLAY';self.redraw();return
  self.status=f'LIVE START IN {self.live_countdown_remaining}s';self.redraw();self._schedule_live_countdown()
 def _cancel_live_countdown(self):
  if self._live_countdown_job is not None:
   try:self.after_cancel(self._live_countdown_job)
   except Exception:pass
   self._live_countdown_job=None
  self.live_countdown_remaining=0
 def live_load(self):
  p=self.live_slots[self.selected_live_slot] or self.selected_song_file
  if p:
   try:self.song=Song.load(p);self.song_mode='SONG';self.status=f'Loaded {Path(p).stem}';self.redraw()
   except Exception as e:self._notify('LIVE',str(e),True)
 def deploy_locked(self):self._notify('DEPLOY TO UNO','Function is present by design, but permanent bulk write to the reserved hardware area is locked until command 0x28 is validated. No destructive SysEx is sent.')
 def _preview_if(self):
  # Compatibility entry point: LOCAL preview is current-buffer CC transmission, never Program Change.
  if not self.lib_selected:return
  try:self._send_local_preview()
  except Exception:logger.exception('Preset preview failed')
 def toggle_preview(self):self.preview=not self.preview;self.redraw()
 def _unique_preset_path(self,stem):
  base=storage.PRESETS/storage._safe(stem);p=base.with_suffix('.unosyp');i=2
  while p.exists():p=storage.PRESETS/f'{storage._safe(stem)} {i}.unosyp';i+=1
  return p
 def lib_add(self):
  src=filedialog.askopenfilename(title='Add preset',filetypes=[('UNO Synth Pro preset','*.unosyp')])
  if not src:return
  try:
   dst=self._unique_preset_path(Path(src).stem);shutil.copy2(src,dst);storage.invalidate_preset_cache();self.lib_selected=dst;self.status=f'Added {dst.name}';self.redraw()
  except Exception as e:self._notify('ADD',str(e),True)
 def lib_copy(self):
  if self.lib_selected and Path(self.lib_selected).exists():self._lib_clipboard=('copy',Path(self.lib_selected));self.status='Preset copied';self.redraw()
 def lib_cut(self):
  if self.lib_selected and Path(self.lib_selected).exists():self._lib_clipboard=('cut',Path(self.lib_selected));self.status='Preset cut';self.redraw()
 def lib_paste(self):
  if not self._lib_clipboard:return
  mode,src=self._lib_clipboard
  if not src.exists():self._lib_clipboard=None;return
  try:
   target_cat=self.lib_category if self.lib_category!='All' else 'My Presets'
   if mode=='cut' and src.parent.resolve()==storage.PRESETS.resolve():
    dst=src
    try:
     d=json.loads(src.read_text(encoding='utf-8'));d['category']=target_cat;src.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception:pass
    self._lib_clipboard=None
   else:
    dst=self._unique_preset_path(src.stem)
    try:
     d=json.loads(src.read_text(encoding='utf-8'));d['category']=target_cat;dst.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception:shutil.copy2(src,dst)
    if mode=='cut':src.unlink();self._lib_clipboard=None
   storage.invalidate_preset_cache();self.lib_selected=dst;self.status=f'Pasted to {target_cat}';self.redraw()
  except Exception as e:self._notify('Paste',str(e),True)
 def lib_rename(self):
  if not self.lib_selected or not Path(self.lib_selected).exists():return
  src=Path(self.lib_selected);cur=src.stem;n=self._ask_text('Rename preset','Preset name:',cur)
  if not n:return
  try:
   dst=self._unique_preset_path(n);shutil.move(str(src),str(dst))
   try:
    d=json.loads(dst.read_text(encoding='utf-8'));d['name']=n;dst.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
   except Exception:pass
   storage.invalidate_preset_cache();self.lib_selected=dst;self.redraw()
  except Exception as e:self._notify('Rename',str(e),True)
 def lib_delete(self):
  if self.lib_selected and Path(self.lib_selected).exists() and self._confirm('Delete','Delete selected local preset?'):
   Path(self.lib_selected).unlink();storage.invalidate_preset_cache();self.lib_selected=None;self.redraw()
 def to_hw(self):self.store_locked()
 def to_lib(self):
  p=copy.deepcopy(self.preset);p.number=self.hardware_selected;p.name=f'UNO {self.hardware_selected:03d}';self.lib_selected=storage.save_preset(p);self.redraw()
 def _env_note_on(self):
  self.env_gate=True;self.env_release=False;self.env_phase_start=time.monotonic();self.env_level_at_release=0.0;self.env_release_levels={'FENV':0.0,'AENV':0.0};self._ensure_animation()
 def _env_note_off(self):
  now=time.monotonic()
  self.env_release_levels={'FENV':self._env_level('FENV',now),'AENV':self._env_level('AENV',now)}
  self.env_level_at_release=self.env_release_levels['FENV'];self.env_gate=False;self.env_release=True;self.env_phase_start=now;self._ensure_animation()
 def _wheel_pitch(self,y,hy,hh):
  t=clamp(1-(y-hy)/hh,0,1);self.pitch_visual=round((t-.5)*16383);self.midi.pitch_bend(self.pitch_visual);self.status='PITCH BEND';self.redraw()
 def _wheel_mod(self,y,hy,hh):t=clamp(1-(y-hy)/hh,0,1);self.set_value('MOD_WHEEL',round(t*127),0,127)
 def _ensure_library_key_visible(self,focus,index,count):
  if focus==1:
   rows=max(1,int((780-42-34)//30));col_w=290;view_w=612;idx=1
  else:
   rows=max(1,int((780-42-42)//30));col_w=210;view_w=640;idx=0
  cols=max(1,(max(1,count)+rows-1)//rows);max_scroll=max(0,cols*col_w-view_w+12);col=max(0,int(index))//rows;left=col*col_w;right=left+col_w;cur=float(self.lib_hscroll[idx])
  if left<cur:cur=left
  elif right>cur+view_w:cur=right-view_w
  self.lib_hscroll[idx]=clamp(cur,0,max_scroll)
 def keypress(self,e):
  if self.page=='SONG' and self.live_editor is not None:return
  if e.keysym=='Escape' and self.open_dropdown:
   self.open_dropdown=None;self.dropdown_hover=None;self.redraw();return 'break'
  if e.keysym=='F8':self.open_dropdown=None;self.dropdown_hover=None;self.page='SONG';self.song_mode='LIVE';self.redraw();return
  if self.page=='LIBRARY' and e.keysym=='Return':
   if self.lib_focus==1:self._select_hw_preset(getattr(self,'lib_hw_selected',self.hardware_selected))
   elif self.lib_selected:self.preset_source='LOCAL';self.preset_folder=Path(self.lib_selected).parent;self.load_local_preset(Path(self.lib_selected),preview=True);self.redraw()
   return 'break'
  if e.keysym not in ('Up','Down','Left','Right'):return
  if self.page=='LIBRARY':
   if self.lib_focus==1:
    rows=max(1,int((780-42-34)//30));i=max(0,min(255,int(getattr(self,'lib_hw_selected',1))-1))
    if e.keysym=='Up':i=max(0,i-1)
    elif e.keysym=='Down':i=min(255,i+1)
    elif e.keysym=='Left':i=max(0,i-rows)
    else:i=min(255,i+rows)
    self.lib_hw_selected=i+1;self._ensure_library_key_visible(1,i,256);self.redraw();return 'break'
   files=self._filtered_files(self.lib_panel_folder[0] or storage.PRESETS,Path(self.lib_panel_folder[0] or storage.PRESETS)==storage.PRESETS)
   if files:
    try:i=files.index(Path(self.lib_selected))
    except Exception:i=0
    rows=max(1,int((780-42-42)//30))
    if e.keysym=='Up':i=max(0,i-1)
    elif e.keysym=='Down':i=min(len(files)-1,i+1)
    elif e.keysym=='Left':i=max(0,i-rows)
    else:i=min(len(files)-1,i+rows)
    self.lib_selected=files[i];self._ensure_library_key_visible(0,i,len(files));self.redraw();return 'break'
  if self.page=='SONG' and self.song_mode=='SONG':
   rows=self._song_tree_rows()
   if not rows:return 'break'
   current=self.lib_selected if self.lib_selected else self.song_tree_selected
   try:i=next(j for j,r in enumerate(rows) if Path(r[1])==Path(current))
   except Exception:i=0
   kind,path,_,_,_=rows[i]
   if e.keysym=='Up':i=max(0,i-1)
   elif e.keysym=='Down':i=min(len(rows)-1,i+1)
   elif e.keysym=='Right' and kind=='folder':self.song_tree_expanded.add(str(path));self.song_tree_selected=path;self.redraw();return 'break'
   elif e.keysym=='Left' and kind=='folder':
    if Path(path)!=Path(storage.PRESETS):self.song_tree_expanded.discard(str(path))
    self.song_tree_selected=path;self.redraw();return 'break'
   kind,path,name,_,_=rows[i]
   if kind=='preset':self.lib_selected=path
   else:self.song_tree_selected=path
   self.redraw();return 'break'
 def _apply_state_cc(self,cc,decoded):
  """Apply one exact-observed 0x37 field to the GUI without sending MIDI back."""
  key=CC_TO_KEY.get(int(cc))
  if not key:return False
  ordinal=int(decoded.get('ordinal',0));raw=int(decoded.get('cc_min',0));unique=int(decoded.get('unique_states',128))
  # Enum fields: use the hardware-observed ordinal. Unknown extra enum states are
  # deliberately not guessed into a GUI label that does not exist yet.
  if key=='F1_MODE':
   if 0<=ordinal<len(FILTER1_MODES):self.choice['F1_MODE']=ordinal;return True
   return False
  if key=='F2_MODE':
   if 0<=ordinal<len(FILTER2_MODES):self.choice['F2_MODE']=ordinal;return True
   return False
  if key=='FILTER_LINK':
   if 0<=ordinal<3:self.filter_link=(0,64,127)[ordinal];return True
   return False
  if key=='MOD_TYPE':
   if 0<=ordinal<3:self.choice['MOD_TYPE']=ordinal;self.choice['MOD_SUB']=0;return True
   return False
  if key=='DELAY_TYPE':
   if 0<=ordinal<5:self.choice['DELAY_TYPE']=ordinal;return True
   return False
  if key=='REVERB_TYPE':
   if 0<=ordinal<4:self.choice['REVERB_TYPE']=ordinal;return True
   return False
  if key=='CHORUS_MODE':
   # CC98 has three hardware-observed states. It is only visible as MOD_SUB in
   # CHORUS mode; retain the ordinal there when applicable.
   self.values['CHORUS_MODE']=ordinal
   if self.choice.get('MOD_TYPE',0)==0 and 0<=ordinal<3:self.choice['MOD_SUB']=ordinal
   return True
  # Toggle semantics come from the observed 0x37 state itself, not a generic
  # MIDI >=64 rule (e.g. Delay Sync switches state at CC1 in the sweep).
  if key in self.toggle:
   self.toggle[key]=bool(ordinal)
   return True
  # 101-state hardware fields are native 0..100 values.  For other quantized
  # fields keep a CC-space representative; 128-state fields are exact CC values.
  value=ordinal if unique==101 else raw
  if key=='DELAY_TIME_R':self.values[key]=value
  else:self.values[key]=self._decode_cc_value(key,value)
  return True

 def _midi_rx(self,data,is_sysex):
  if self._closing:return
  try:self._midi_rx_queue.put_nowait((bytes(data),bool(is_sysex)))
  except Exception:pass
 def _drain_midi_rx(self):
  self._midi_rx_job=None
  if self._closing:return
  events=[]
  try:
   while True:events.append(self._midi_rx_queue.get_nowait())
  except queue.Empty:pass
  if events:
   # Keep only the newest value for each CC in this 10 ms slice; preserve all clocks/notes/SysEx.
   last_cc={};ordered=[]
   for data,is_sysex in events:
    if (not is_sysex) and len(data)>=3 and (data[0]&0xF0)==0xB0 and (data[1]&127)!=0:last_cc[(data[0]&0x0F,data[1]&127)]=(data,is_sysex)
    else:ordered.append((data,is_sysex))
   ordered.extend(last_cc.values())
   for data,is_sysex in ordered:self._midi_rx_ui(data,is_sysex)
  if not self._closing:self._midi_rx_job=self.after(10,self._drain_midi_rx)
 def _midi_rx_ui(self,data,is_sysex):
  if is_sysex:
   # Live hardware UI notifications confirmed by controlled 2026-09-11 captures.
   # Receive-only: update GUI state without echoing anything back to the UNO.
   if len(data)==10 and data[:6]==IK_HEADER and data[6]==0x34 and data[-1]==0xF7:
    subtype,value=data[7],data[8]&0x7F
    if subtype==0x04 and value<=2:
     self.choice['VOICE']=value;self.status=f'RX Voice {['MONO','LEGATO','PARA'][value]}';self.redraw();return
    if subtype==0x06 and value<=1:
     self.arp_on=bool(value);self.status='RX ARP ON' if value else 'RX ARP OFF';self.redraw();return
   if data[:7]==IK_HEADER+bytes([0x3E]) and len(data)>=11:
    addr=tuple(data[7:9]);payload=bytes(data[9:-1])
    if addr==(0,0) and len(payload)==1 and payload[0]<=9:
     self.choice['ARP_MODE']=payload[0];self.status=f'RX ARP Direction {ARP_MODES[payload[0]]}';self.redraw();return
    if addr==(0,1) and len(payload)==1 and 1<=payload[0]<=4:
     self.values['ARP_RANGE']=f'{payload[0]} OCT';self.status=f'RX ARP Range {payload[0]} OCT';self.redraw();return
    if addr==(0,2) and len(payload)==3:
     mask=(payload[0]&0x7F)|((payload[1]&0x7F)<<7)|((payload[2]&0x03)<<14)
     self.arp_trig=[bool(mask & (1<<i)) for i in range(16)];self.status='RX ARP Pattern';self.redraw();return
   if data[:6]==IK_HEADER and len(data)>=12 and data[7]==0x29:
    if self._accept_hardware_sequence_page(data):return
   if data[:6]==IK_HEADER and len(data)>=12 and data[6]==0x32:
    self._schedule_hardware_refresh(self.hardware_selected);self.redraw();return
   if len(data)>=43 and data[:6]==IK_HEADER and data[7]==0x24:
    try:
     decoded=decode_preset_name_response(data)
     if decoded is None:raise ValueError('invalid 0x24 response')
     slot,name=decoded
     self.hardware_names[slot]=name
     if self._catalog_active and slot==self._catalog_slot:
      if self._catalog_timeout_job is not None:
       try:self.after_cancel(self._catalog_timeout_job)
       except Exception:pass
       self._catalog_timeout_job=None
      self._catalog_retry=0;self._catalog_slot+=1;self._catalog_job=self.after(5,self._request_catalog_slot)
     if slot==self.hardware_selected and name:self.preset.name=name
     self.status=f'HARDWARE {slot:03d}' + (f' — {name}' if name else '')
    except Exception:logger.exception('Failed to decode 0x24 preset name response')
    if self.page=='LIBRARY' or slot==self.hardware_selected or slot%16==0:self.redraw()
    return
   if len(data)==309 and data[:6]==IK_HEADER and data[7]==0x37:
    try:
     self._last_state_dump=bytes(data)
     if self.preset_source=='HARDWARE' and self.sequence_origin!='HARDWARE_0x29':self._set_hardware_sequence_unavailable(reset=False)
     resolved,unresolved=decode_state_0x37(data);applied=0;semantic_skips=0
     # Apply enums/types first so context-sensitive visible controls (CHORUS MODE,
     # DELAY/REVERB layouts) see the preset's type before subordinate fields.
     priority=(30,37,41,95,100,107)
     ordered=[cc for cc in priority if cc in resolved]+[cc for cc in resolved if cc not in priority]
     for cc in ordered:
      if self._apply_state_cc(cc,resolved[cc]):applied+=1
      else:semantic_skips+=1
     # Non-CC ARP preset fields, mapped by controlled 3E/0x37 differentials.
     self._apply_extended_preset_fields(decode_extended_preset_fields(decode_0x37_raw(data)))
     # Preserve the previously confirmed sequencer Direction field.
     off=SEQ_STATE['direction_offset'];raw=data[off]&SEQ_STATE['direction_mask'];name=SEQ_STATE['direction_values'].get(raw)
     if name:self.choice['SEQ_DIR']=SEQ_DIRECTIONS.index(name)
     self.status=f'0x37 state: {applied} GUI fields applied' + (' / hardware sequence read via 0x29' if self.sequence_origin=='HARDWARE_0x29' else ' / hardware sequence pending')
     if unresolved or semantic_skips:self.status+=f' / {len(unresolved)} unseen / {semantic_skips} unlabeled'
    except Exception:
     logger.exception('Failed to decode 0x37 state');self.status=f'0x37 state received ({len(data)} bytes) — decode failed'
   self.redraw();return
  if not data:return
  st=data[0]
  if st==0xFA:
   self.seq_playing=True;self.seq_record_step=0;self.selected_seq_step=0;self._seq_clock_count=0;self._seq_last_clock_time=None;self._play_seq_step(0);self.status='RX PLAY';self.redraw();return
  if st==0xFC:
   self.seq_playing=False;self._seq_all_notes_off();self.status='RX STOP';self.redraw();return
  if st==0xF8:
   self._seq_clock();return
  typ=st&0xF0;ch=st&0x0F
  inch=self.settings.get('midi_in_channel',1);channel_ok=(str(inch).upper()=='OMNI') or ch==max(0,int(inch)-1)
  if typ==0x90 and len(data)>=3 and channel_ok and (data[2]&127)>0:
   note=data[1]&127;self.hw_keys_down.add(note);self._env_note_on();self._record_note(note,data[2]&127);self.status=f'RX Note {note}';self.redraw()
  elif (typ==0x80 or (typ==0x90 and len(data)>=3 and (data[2]&127)==0)) and len(data)>=2 and channel_ok:
   note=data[1]&127;self.hw_keys_down.discard(note);self._env_note_off();self.status=f'RX Note Off {note}';self.redraw()
  elif typ==0xB0 and len(data)>=3 and channel_ok:
   cc,v=data[1]&127,data[2]&127
   if cc==0:self._rx_bank=v
   self._record_automation_cc(cc,v);key=CC_TO_KEY.get(cc)
   if key:
    if key=='F1_MODE':
     vals=[0,25,50,75,100];self.choice['F1_MODE']=min(range(len(vals)),key=lambda i:abs(vals[i]-v))
    elif key=='F2_MODE':
     vals=[0,20,40,60,80,100];self.choice['F2_MODE']=min(range(len(vals)),key=lambda i:abs(vals[i]-v))
    elif key=='FILTER_LINK':self.filter_link=min((0,64,127),key=lambda q:abs(q-v))
    elif key in ('MOD_TYPE','DELAY_TYPE','REVERB_TYPE'):
     raws={'MOD_TYPE':[0,42,84],'DELAY_TYPE':[0,25,50,75,100],'REVERB_TYPE':[0,32,64,96]}[key]
     # Hardware-captured enum values: MOD 0/42/84, REVERB 0/32/64/96; DELAY retained from validated v1.43/v1.45.
     self.choice[key]=min(range(len(raws)),key=lambda i:abs(raws[i]-v))
     if key=='MOD_TYPE':self.choice['MOD_TYPE']=max(0,min(2,self.choice['MOD_TYPE']));self.choice['MOD_SUB']=0
    elif key=='DELAY_TIME_R':self.values['DELAY_TIME_R']=v
    else:self.values[key]=self._decode_cc_value(key,v)
    if key in self.toggle:self.toggle[key]=v>=64
    self.status=f'RX CC{cc}={v}';self._set_hw_popup(key);self.redraw()
  elif typ==0xC0 and len(data)>=2:
   new_n=max(1,min(256,int(self._rx_bank)*128+(data[1]&127)+1));changed=(self.preset_source!='HARDWARE' or self.hardware_selected!=new_n);self.preset.number=new_n;self.hardware_selected=new_n;self.preset_source='HARDWARE';self._set_hardware_sequence_unavailable(reset=changed);self._schedule_hardware_refresh(self.preset.number);self.status=f'RX Program {self.preset.number:03d} — reading state / sequence unavailable';self.redraw()

if __name__=='__main__':App().mainloop()

