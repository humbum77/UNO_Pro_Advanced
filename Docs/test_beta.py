"""Offline release checks. Run: python Docs/test_beta.py"""
import ast, copy, importlib, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import Mock, patch
from types import SimpleNamespace
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import app, storage
from app import App
from data_model import Preset, Sequence
from protocol_map import preset_page_read, COMMANDS
from hardware_seq_0x29 import parse_0x29_response, apply_to_sequence, RESPONSE_PREFIX

class BetaTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
  self.patches=[]
  def use(p):self.patches.append(p);return p.start()
  use(patch.object(app.tk.Tk,'__init__',return_value=None))
  def missing(self,name):raise AttributeError(name)
  use(patch.object(App,'__getattr__',missing))
  use(patch.object(App,'winfo_exists',return_value=True))
  for name in ('title','configure','geometry','resizable','bind','protocol','after','after_idle','after_cancel','winfo_rootx','winfo_rooty'):
   use(patch.object(App,name,return_value=None))
  for name,val in [('winfo_screenwidth',1920),('winfo_screenheight',1080),('winfo_width',1440),('winfo_height',900)]:use(patch.object(App,name,return_value=val))
  canvas=Mock();canvas.winfo_width.return_value=1600;canvas.winfo_height.return_value=1000
  use(patch.object(app.tk,'Canvas',return_value=canvas));use(patch.object(app,'PIL_OK',False))
  use(patch.object(app,'MidiEngine',return_value=Mock()))
  use(patch.object(storage,'load_settings',return_value=copy.deepcopy(storage.DEFAULT)))
  use(patch.object(storage,'save_settings'))
  use(patch.object(storage,'PRESETS',self.folder));use(patch.object(storage,'SONGS',self.folder/'songs'))
  self.a=App();self.a._notify=Mock();self.a._confirm=Mock(return_value=True)
  self.a._confirm_discard=Mock(return_value=True)
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.tmp.cleanup()
 def test_save_as_current_and_roundtrip(self):
  a=self.a;a.preset.sequence.steps[0].notes=[48,55,60];a.preset.sequence.length_confirmed=False
  a.preset.sequence.binary_page_metadata=['test'];a.values['F1_CUTOFF']=53
  self.assertTrue(a.dirty)
  first=self.folder/'Куплет.unosyp';second=self.folder/'Припев.unosyp'
  with patch.object(app.filedialog,'asksaveasfilename',return_value=str(first)):
   self.assertTrue(a.save_local_preset())
  self.assertFalse(a.dirty);original=first.read_bytes()
  a.preset.sequence.steps[0].notes=[62]
  with patch.object(app.filedialog,'asksaveasfilename',return_value=str(second)) as dialog:
   self.assertTrue(a.save_local_preset_as());self.assertEqual(dialog.call_args.kwargs['initialdir'],str(self.folder))
  self.assertEqual(a.working_file,second);self.assertEqual(first.read_bytes(),original)
  a.values['F1_CUTOFF']=71;self.assertTrue(a.save_local_preset())
  loaded=storage.load_preset(second)
  self.assertEqual(asdict(loaded.sequence),asdict(a.preset.sequence));self.assertEqual(loaded.params,a._collect_params())
  a.values['F1_CUTOFF']=20;self.assertTrue(a.load_local_preset(second));self.assertFalse(a.dirty)
  self.assertEqual(a.values['F1_CUTOFF'],71)
 def test_cancel_and_atomic_failure(self):
  a=self.a;path=self.folder/'Part.unosyp';self.assertTrue(a._save_working_file(path));before=path.read_bytes()
  a.values['F1_CUTOFF']=4;a._confirm.return_value=False
  self.assertFalse(a.save_local_preset());self.assertEqual(path.read_bytes(),before);self.assertTrue(a.dirty)
  with patch.object(app.filedialog,'asksaveasfilename',return_value=''):self.assertFalse(a.save_local_preset_as())
  a._confirm.return_value=True
  with patch.object(storage.os,'replace',side_effect=OSError('disk failure')):self.assertFalse(a.save_local_preset())
  self.assertEqual(path.read_bytes(),before);self.assertEqual(list(self.folder.glob('*.tmp')),[]);self.assertTrue(a.dirty)
 def test_binary_never_overwritten(self):
  p=self.folder/'official.unosyp';raw=b'\x25\x01\x00\x00\xff';p.write_bytes(raw)
  self.assertFalse(self.a._save_working_file(p));self.assertEqual(p.read_bytes(),raw);self.assertIsNone(self.a.working_file)
 def test_cancel_switches_before_mutation(self):
  a=self.a;a.values['F1_CUTOFF']=1;a._confirm_discard.return_value=False
  before=a._working_snapshot();slot=a.hardware_selected
  a._select_hw_preset(8);a.change_preset(1);a.init_patch();a.close()
  self.assertEqual(slot,a.hardware_selected);self.assertEqual(before,a._working_snapshot());self.assertFalse(a._closing)
  a.midi.bank_program.assert_not_called()
  p=self.folder/'load.unosyp';storage.save_working_preset(Preset(),p)
  self.assertFalse(a.load_local_preset(p));self.assertEqual(before,a._working_snapshot())
 def test_three_way_prompt(self):
  a=self.a;a.values['F1_CUTOFF']=4
  for selection,save_ok,expected in [('Save',True,True),('Save',False,False),("Don't Save",False,True),('Cancel',True,False)]:
   commands={}
   def button(*args,**kw):commands[kw['text']]=kw['command'];return Mock()
   with patch.object(app.tk,'Toplevel',return_value=Mock()),patch.object(app.tk,'Label',return_value=Mock()),patch.object(app.tk,'Frame',return_value=Mock()),patch.object(app.tk,'Button',side_effect=button),patch.object(App,'wait_window',side_effect=lambda win:commands[selection]()),patch.object(a,'save_local_preset',return_value=save_ok):
    self.assertEqual(App._confirm_discard(a),expected)
 def test_dirty_all_sequence_fields_and_revert(self):
  a=self.a;base=copy.deepcopy(a.preset.sequence)
  mutations=[lambda s:setattr(s,'transpose',3),lambda s:setattr(s,'length',32),lambda s:setattr(s.steps[0],'tie',True),lambda s:setattr(s.steps[0],'velocity',2),lambda s:s.automation[0]['values'].__setitem__(0,9)]
  for mutate in mutations:
   mutate(a.preset.sequence);self.assertTrue(a.dirty);a.preset.sequence=copy.deepcopy(base);self.assertFalse(a.dirty)
 def test_pages_and_geometry(self):
  a=self.a
  for page in ('SYNTH','ARP + SEQUENCER','SONG','LIBRARY','SETTINGS'):
   a.page=page;a.redraw();self.assertTrue(a.hit)
  a.page='SYNTH';a.redraw()
  sliders={h[5]:h for h in a.hit if h[4]=='slider' and h[6][2]}
  for prefix in ('F1','F2'):
   endpoints={(sliders[prefix+'_'+k][1],sliders[prefix+'_'+k][3]) for k in ('CUTOFF','RES','ENV','TRACK')};self.assertEqual(len(endpoints),1)
  for n in (1,2):
   rate=sliders[f'LFO{n}_RATE'];fade=sliders[f'LFO{n}_FADE'];self.assertEqual((rate[1],rate[3]),(fade[1],fade[3]))
  self.assertEqual(App._vertical_fader_geometry(100,20,80)['label_y'],60)
  a.page='ARP + SEQUENCER';a.redraw()
  buttons=[h for h in a.hit if h[4]=='action'];self.assertTrue(any(h[6]==a.save_local_preset_as for h in buttons))
 def test_live_drag_assignment(self):
  a=self.a;a.page='SONG';a.song_mode='LIVE';song=self.folder/'Set.unosong';song.write_text('{}');a.selected_song_file=song;a.redraw()
  target=next(h for h in a.hit if h[4]=='songcell' and h[5]==3)
  x=target[0]+4;y=target[1]+4
  a.drag=(0,0,1,1,'songdrag',None,{'path':song,'name':'Set'});a._lib_drag_started=True;a._lib_drag_pos=(x,y)
  a._draw_library_drag_feedback();a.release(SimpleNamespace(x=a.X(x),y=a.Y(y)))
  self.assertEqual(a.live_slots[3],str(song));self.assertIsNone(a.drag)
 def test_late_hardware_does_not_replace_edits(self):
  a=self.a;a.values['F1_CUTOFF']=8;a._hw_seq_slot=1;a._hw_seq_expected_page=4;a._hw_seq_pages={i:bytes(192) for i in (1,2,3)}
  before=a._working_snapshot();data=RESPONSE_PREFIX+bytes([0,0,4])+bytes(192)+b'\xf7'
  a._accept_hardware_sequence_page(data);self.assertEqual(before,a._working_snapshot())
 def test_protocol_and_static(self):
  for slot in (1,2,128,129,256):
   for page in range(5):
    bank,program=divmod(slot-1,128)
    self.assertEqual(preset_page_read(slot,page),bytes([0xf0,0,0x21,0x1a,2,3,0x29,bank,program,page,0xf7]))
    size=293 if page==0 else 192;data=RESPONSE_PREFIX+bytes([bank,program,page])+bytes(size)+b'\xf7'
    self.assertEqual(parse_0x29_response(data,slot),(page,bytes(size)));self.assertIsNone(parse_0x29_response(data,1 if slot!=1 else 2))
  self.assertIn('LOCKED',COMMANDS[0x28]);seq=Sequence();apply_to_sequence(seq,{i:bytes(192) for i in range(1,5)});self.assertEqual(len(seq.steps),64);self.assertFalse(seq.length_confirmed)
  for path in ROOT.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'));importlib.import_module(path.stem)
  src=(ROOT/'app.py').read_text(encoding='utf-8');self.assertNotIn('_apply_ui_scale',src);self.assertNotIn('⛶',src);self.assertNotIn('ui_scale',storage.DEFAULT)
  self.assertIn("self.resizable(True,True)",src)
  self.assertIn("['Off','MIDI MASTER']",src)
 def test_protocol_note_payload(self):
  raw=bytearray([255]*160)
  for i in range(16):raw[i*10:i*10+4]=bytes([0,48+i,90+i,0])
  bits=[(byte>>bit)&1 for byte in raw[1:] for bit in range(8)]
  packed=bytes(sum(bit<<j for j,bit in enumerate(bits[i:i+7])) for i in range(0,len(bits),7))
  payload=packed+bytes(192-len(packed));seq=Sequence();apply_to_sequence(seq,{i:payload for i in range(1,5)})
  self.assertEqual([step.notes for step in seq.steps],[[48+i%16] for i in range(64)])
  self.assertEqual([step.velocity for step in seq.steps],[90+i%16 for i in range(64)])
  self.assertTrue(all(seq.steps[i].control_raw is None for i in (0,16,32,48)))
 def test_redraw_does_not_dirty_loaded_fx(self):
  a=self.a;a.choice.update(MOD_TYPE=1,MOD_SUB=2,DELAY_TYPE=8,REVERB_TYPE=5);a._mark_clean()
  before=a._working_snapshot();a.redraw()
  self.assertEqual(a._working_snapshot(),before);self.assertFalse(a.dirty)
 def test_bank_and_performance_wheel_are_not_edits(self):
  a=self.a
  for cc,value in [(0,1),(1,80),(0,0)]:a._midi_rx_ui(bytes([0xb0,cc,value]),False)
  self.assertFalse(a.dirty)
 def test_browsing_sync_has_no_prompt(self):
  a=self.a;a._confirm_discard=lambda:App._confirm_discard(a)
  with patch.object(app.tk,'Toplevel',side_effect=AssertionError('Unexpected warning')):
   for slot in range(2,8):
    a._select_hw_preset(slot)
    a._midi_rx_ui(bytes([0xb0,0,0]),False)
    a._midi_rx_ui(bytes([0xb0,28,slot]),False)
    a._midi_rx_ui(app.IK_HEADER+bytes([0x34,4,slot%3,0xf7]),True)
    self.assertFalse(a.dirty)
 def test_sync_keeps_local_edits_and_recorded_notes_dirty(self):
  a=self.a;a._schedule_hardware_refresh(1);a.values['F1_RES']=3
  a.seq_recording=True;a._midi_rx_ui(bytes([0x90,60,100]),False)
  a._midi_rx_ui(bytes([0xb0,28,40]),False)
  self.assertTrue(a.dirty);self.assertNotEqual(a._clean_snapshot['params']['values']['F1_RES'],3)
  self.assertEqual(a.preset.sequence.steps[0].notes,[60])
  a._mark_clean();a._preset_sync_until=0;a._midi_rx_ui(bytes([0xb0,28,41]),False)
  self.assertTrue(a.dirty)

if __name__=='__main__':unittest.main(verbosity=2)
