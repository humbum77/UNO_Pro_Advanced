"""Real Tk integration smoke, isolated storage, mocked MIDI; no hardware sends."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main(preview=False):
 with tempfile.TemporaryDirectory(prefix='uno-integration-') as folder:
  os.environ['LOCALAPPDATA']=folder
  import app,storage,ui_theme
  from live_creator.core import state
  errors=[]
  with patch.object(app,'MidiEngine',return_value=Mock()),patch.object(app.App,'_start_port_refresh'),patch.object(app.App,'_restore_session_preset'):
   a=app.App();a.report_callback_exception=lambda *args:errors.append(args)
   try:
    a.update();a.set_page('SONG');a.update();live=a.live_editor
    live.session.resolver=lambda p:4
    live.model.insert(0,'synthetic-a',30);live.model.insert(1,'synthetic-b',10)
    live.model.set_marker(1,'INTRO');live.model.set_marker(31,'CHORUS');live.session.song.set_length(35);live.sync_editor();live.render();a.update()
    assert len(live.pad_boxes)==64 and len(live.timeline.find_withtag('slot-number'))==64
    assert len(live.timeline.find_withtag('inactive'))==29
    assert len(live.timeline.find_withtag(live.model.blocks[1].id))==2
    assert all(live.timeline.type(i)=='polygon' for i in live.timeline.find_withtag('block'))
    live.select(1);live.toggle_play();live.select_pad(1);assert live.session.playing_pad==0
    a.set_page('SYNTH');a.update();assert not live.winfo_ismapped() and live.session.active
    a.set_page('SONG');live.select_pad(0);a.update();live.toggle_play()
    for name in ('dark','light'):
     if ui_theme.current!=name:a.toggle_theme()
     for page in ('SYNTH','ARP + SEQUENCER','LIBRARY','SONG','SETTINGS'):
      a.set_page(page);a.update()
     assert storage.load_settings().get('theme','dark')==name
     a.set_page('SONG');a.update()
     assert live.grid_canvas.itemcget(live.grid_canvas.find_withtag('pad-63')[0],'fill')=='#1b2024'
    a.set_page('ARP + SEQUENCER');a.update();a.preset.sequence.length=12;a.seq_duplicate();assert a.preset.sequence.length==24
    a._select_dropdown_value('SEQ_TARGET','SPACING');a.update()
    a._open_dropdown((520,770,240,42,'choice','SEQ_TARGET',None),'SEQ_TARGET',app.AUTOMATABLE);a.update()
    assert a.open_dropdown['picker'] and len([h for h in a.hit if h[4]=='dropdown_item'])==22
    a.open_dropdown=None;a.redraw()
    assert not errors,errors
    assert not a.midi.sysex.called and not a.midi.send_cc.called
    assert (Path(folder)/'UnoLive'/'settings.json').exists()
    print('INTEGRATION GUI PASS: embedded LIVE, 64 pads, LENGTH, radius, snapshots, all pages/themes, picker, Dupl, no sends',flush=True)
    if preview:
     a.set_page('SONG');a.update();a.mainloop()
   finally:
    if a.winfo_exists():
     if a.live_editor is not None:a.live_editor.close();a.live_editor=None
     a.destroy()

if __name__=='__main__':main('--preview' in sys.argv)
