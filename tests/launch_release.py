"""Launch packaged main entry point with isolated service paths and mocked MIDI."""
import os,sys,tempfile,runpy
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory(prefix='uno-launch-') as folder:
 os.environ['LOCALAPPDATA']=folder
 import app
 original=app.App.mainloop
 errors=[]
 def loop(self,*args,**kwargs):
  self.report_callback_exception=lambda *e:errors.append(e)
  def verify():
   try:
    self.set_page('SONG');self.update_idletasks();assert self.live_editor.winfo_ismapped()
    self.live_editor.close();self.live_editor=None
   except Exception as exc:errors.append(exc)
   finally:self.destroy()
  self.after(400,verify);original(self,*args,**kwargs)
 with patch.object(app,'MidiEngine',return_value=Mock()),patch.object(app.App,'_start_port_refresh'),patch.object(app.App,'_restore_session_preset'),patch.object(app.App,'mainloop',loop):
  runpy.run_path(str(ROOT/'main.py'),run_name='__main__')
 assert not errors,errors
 import logging
 logging.shutdown()
 print('PACKAGED MAIN LAUNCH PASS (MIDI mocked, isolated storage)')
