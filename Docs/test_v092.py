import unittest, tempfile, json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_beta import BetaTests
from app import App
import app,storage

class RollbackTests(unittest.TestCase):
 setUp=BetaTests.setUp
 tearDown=BetaTests.tearDown
 test_protocol_note_payload=BetaTests.test_protocol_note_payload
 test_live_drag_assignment=BetaTests.test_live_drag_assignment
 def test_scales(self):
  a=self.a
  self.assertEqual(a.settings['ui_scale'],'100%')
  for scale,size in [('100%','1200x750'),('125%','1440x900'),('150%','1600x1000')]:
   a._apply_ui_scale(scale);self.assertTrue(a.geometry.call_args.args[0].startswith(size));a.resizable.assert_called_with(False,False)
 def test_buttons_and_fill(self):
  a=self.a;a.page='ARP + SEQUENCER'
  with patch.object(a,'button',wraps=a.button) as button,patch.object(a,'text',wraps=a.text) as text:
   a.redraw();calls=[c.args for c in button.call_args_list]
   for label in ('SAVE','SAVE AS','⛶'):
    matches=[c for c in calls if c[4]==label];self.assertEqual(len(matches),1);self.assertEqual(matches[0][1],8)
   fill=next(c for c in calls if c[4]=='FILL');self.assertEqual(fill[2:4],(241,46))
   self.assertTrue(any(c.args[1]==222 and 'Fill all 64' in str(c.args[2]) for c in text.call_args_list))
 def test_browsing_never_prompts(self):
  a=self.a;a.values['F1_CUTOFF']=3
  with patch.object(app.tk,'Toplevel',side_effect=AssertionError('Unexpected warning')):
   a._select_hw_preset(2);a.change_preset(1)
  a._confirm_discard.assert_not_called()
 def test_legacy_save_and_standalone_save_as(self):
  a=self.a;a._ask_text=lambda *args:'Part';a.save_local_preset();a.save_local_preset()
  self.assertTrue((self.folder/'Part.unosyp').exists());self.assertTrue((self.folder/'Part 2.unosyp').exists())
  target=self.folder/'Export.unosyp'
  with patch.object(app.filedialog,'asksaveasfilename',return_value=str(target)):self.assertTrue(a.save_local_preset_as())
  self.assertEqual(storage.load_preset(target).params,a._collect_params());self.assertFalse(hasattr(a,'working_file'))
  before=target.read_bytes();a._confirm.return_value=False
  with patch.object(app.filedialog,'asksaveasfilename',return_value=str(target)):self.assertFalse(a.save_local_preset_as())
  self.assertEqual(target.read_bytes(),before)
 def test_scale_migration(self):
  config=self.folder/'settings.json';config.write_text(json.dumps({'ui_scale':'125%'}))
  # setUp mocks load_settings, so exercise the real module function separately.
  import importlib.util
  spec=importlib.util.spec_from_file_location('settings_test',Path(storage.__file__));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.SETTINGS=config
  self.assertEqual(mod.load_settings()['ui_scale'],'100%')
  config.write_text(json.dumps({'ui_scale':'150%','scale_restored_v092':True}))
  self.assertEqual(mod.load_settings()['ui_scale'],'150%')

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RollbackTests))
 sys.exit(0 if result.wasSuccessful() else 1)
