import ast,copy,json,subprocess,tempfile,unittest
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch
import storage,ui_theme
from data_model import Sequence,Preset
from native_automation import read_automation,sequence_length,encode_sequence_length
from automation_metadata import PARAMETERS,AUTOMATABLE,parameter_line
from live_creator.core.session import Session,Transport
from live_creator.core.state import encode,decode

ROOT=Path(__file__).resolve().parents[1]
class IntegrationTests(unittest.TestCase):
 def test_duplicate(self):
  for n in (8,12,16,32):
   seq=Sequence(length=n)
   for i in range(n):seq.steps[i].notes=[i];seq.steps[i].control_raw=i
   lane=seq.automation[0];lane['values']=list(range(64));lane['fine_values']=[[i,None] for i in range(64)];lane['cc_values']=list(range(64))
   seq.duplicate();self.assertEqual(seq.length,n*2)
   self.assertEqual(seq.steps[:n],seq.steps[n:2*n]);seq.steps[n].notes.append(99);self.assertNotIn(99,seq.steps[0].notes)
   for key in ('values','fine_values','cc_values'):self.assertEqual(lane[key][:n],lane[key][n:2*n])
 def test_dupl_limit_atomic(self):
  for n in (33,48,64):
   seq=Sequence(length=n);before=asdict(seq)
   with self.assertRaises(ValueError):seq.duplicate()
   self.assertEqual(asdict(seq),before)
 def test_native_dupl_partial(self):
  seq=Sequence();seq.native_automation={'entry_count':1,'payload_hex':'2901'};before=asdict(seq)
  self.assertFalse(seq.can_duplicate)
  with self.assertRaises(ValueError):seq.duplicate()
  self.assertEqual(asdict(seq),before)
 def test_no_guessed_automation_sends(self):
  from app import App
  from types import SimpleNamespace
  from unittest.mock import Mock
  seq=Sequence();seq.automation[0]['values'][0]=512
  a=SimpleNamespace(preset=Preset(sequence=seq),midi=Mock(),_seq_all_notes_off=Mock())
  App._play_seq_step(a,0);a.midi.send_cc.assert_not_called()
  seq.automation[0]['cc_values']=[73]*64;App._play_seq_step(a,0);a.midi.send_cc.assert_called_once_with(28,73)
  seq.length=8;seq.automation[0]['cc_values']=list(range(64));seq.fill64();self.assertEqual(seq.automation[0]['cc_values'][8:16],list(range(8)))
 def test_length_packing(self):
  original=bytes(range(256))*5
  for n in range(1,65):
   result=encode_sequence_length(original,n);self.assertEqual(sequence_length(result),n)
   self.assertEqual(result[:207],original[:207]);self.assertEqual(result[209:],original[209:])
 def test_native_container(self):
  for n in (0,1,2,14,17,18,32):
   data=bytearray(600);data[494]=n*2;data[495]=7;data[496:496+n*2]=bytes(range(n*2))
   before=bytes(data);info=read_automation(data)
   self.assertEqual(info['entry_count'],n);self.assertEqual(bytes(data),before)
   self.assertIsNone(info['maximum_entries']);self.assertEqual(info['unknown_byte_495'],7)
   self.assertTrue(all(e['parameter'] is None and e['step'] is None for e in info['entries']))
  data[494]=3
  with self.assertRaises(ValueError):read_automation(data)
  with self.assertRaises(ValueError):read_automation(bytes(495))
 def test_native_pairs_opaque(self):
  data=bytearray(600);data[494]=6;data[496:502]=bytes.fromhex('29 01 58 0e 08 c3')
  self.assertEqual([e['raw_hex'] for e in read_automation(data)['entries']],['2901','580e','08c3'])
 def test_song_length(self):
  s=Session(lambda p:4);s.song.timeline.insert(0,'a',40);s.song.timeline.insert(1,'b',24);s.song.set_length(33)
  self.assertEqual(len(s.timing(s.song)),33);self.assertEqual(s.duration(s.song),66)
  s.song.timeline.select(40);s.toggle(0);s.update(66);self.assertEqual(s.transport,Transport.STOPPED)
  self.assertEqual(s.song.timeline.length,64);self.assertEqual(decode(encode(s)).song.length,33)
 def test_length_loop_and_snapshot(self):
  s=Session(lambda p:1);s.song.timeline.insert(0,'a',64);s.song.set_length(10);s.song.timeline.loop_range=(8,20)
  s.toggle(0);self.assertEqual(s.loop_range,(8,10));s.song.set_length(2);self.assertEqual(len(s.durations),10)
  s.update(20);self.assertLessEqual(s.current_step,10)
  s.toggle(20);s.update(30);self.assertFalse(s.active)
 def test_metadata(self):
  self.assertEqual(len(AUTOMATABLE),22);self.assertNotIn('FM 1',AUTOMATABLE);self.assertNotIn('KEYTRACKING',AUTOMATABLE)
  self.assertEqual(PARAMETERS['SPACING'].scale_labels(),('64','0','-64'))
  self.assertEqual(PARAMETERS['CUTOFF 1'].scale_labels(),('512','256','0'))
  seq=Sequence();self.assertIs(parameter_line(seq,'LEVEL 3'),parameter_line(seq,'LEVEL 3'))
  self.assertTrue(all(v is None for v in seq.automation[0]['values']))
 def test_theme(self):
  ui_theme.set_theme('light');self.assertEqual(ui_theme.color('#ff8c18'),'#4db8ff');self.assertEqual(ui_theme.color('#4db8ff'),'#ff8c18')
  for key in ('play','rec'):self.assertEqual(ui_theme.TOKENS['dark'][key],ui_theme.TOKENS['light'][key])
  ui_theme.set_theme('dark')
 def test_storage_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'test.unosyp';seq=Sequence();seq.automation[0]['values'][3]=512;seq.native_raw_hex='ff01';seq.native_automation={'payload_hex':'2901'}
   storage.save_working_preset(Preset(sequence=seq),p);loaded=storage.load_preset(p);self.assertEqual(asdict(loaded.sequence),asdict(seq))
   raw=root/'binary.unosyp';raw.write_bytes(b'\xff\x00')
   with self.assertRaises(ValueError):storage.save_working_preset(Preset(),raw)
   self.assertEqual(raw.read_bytes(),b'\xff\x00')
 def test_safety_unchanged(self):
  for name in ('midi_engine.py','midi_interface.py','protocol_map.py','hardware_seq_0x29.py'):
   base=subprocess.check_output(['git','show','51906bc:'+name],cwd=ROOT).decode('utf-8-sig').replace('\r\n','\n')
   self.assertEqual((ROOT/name).read_text(encoding='utf-8-sig'),base)
  base=ast.parse(subprocess.check_output(['git','show','51906bc:app.py'],cwd=ROOT).decode('utf-8-sig'));current=ast.parse((ROOT/'app.py').read_text(encoding='utf-8-sig'))
  for name in ('store_locked','seq_fill'):
   extract=lambda tree:ast.dump(next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name))
   self.assertEqual(extract(base),extract(current))

if __name__=='__main__':unittest.main()
