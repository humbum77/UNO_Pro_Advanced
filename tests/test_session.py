import unittest,tempfile
from pathlib import Path
from live_creator.core.session import Session
from live_creator.core import state

class SessionTests(unittest.TestCase):
    def make(self):
        s=Session(resolver=lambda ref:1);s.song.timeline.insert(0,'preset',3);s.song.timeline.insert(1,'other',2);return s
    def test_64_independent(self):
        s=self.make();s.select_pad(63);self.assertEqual(s.song.timeline.length,0)
        s.song.name='Last';s.song.timeline.insert(0,'last');self.assertEqual(s.pads[0].timeline.length,5)
    def test_play_start_block(self):
        s=self.make();s.song.timeline.select(5);s.toggle(0);self.assertEqual(s.current_step,4)
    def test_pad_change_preserves_playback(self):
        s=self.make();s.toggle(0);s.select_pad(1);s.update(.5)
        self.assertEqual(s.playing_pad,0);self.assertEqual(s.current_step,2);self.assertEqual(s.song.timeline.length,0)
    def test_cancel_all_delays(self):
        for delay in [5,10,15,30,45,60]:
            s=self.make();s.song.delay=delay;s.toggle(100);self.assertEqual(s.pending_pad,0)
            s.select_pad(2);s.toggle(101);s.update(200);self.assertFalse(s.active)
    def test_delay_captures_song(self):
        s=self.make();s.song.delay=5;s.toggle(0);s.select_pad(3);s.update(5)
        self.assertEqual(s.playing_pad,0);self.assertEqual(s.current_step,1)
    def test_loop_and_selection(self):
        s=self.make();a=s.song.timeline;a.select(1);a.select(4,True);a.toggle_loop();s.toggle(0)
        a.select(3);s.select_pad(8);s.update(1.0);self.assertEqual(s.current_step,1);self.assertTrue(s.active)
    def test_end(self):
        s=self.make();s.toggle(0);s.update(3);self.assertFalse(s.active)
        self.assertEqual(s.position,2.5)
    def test_deselected_block_starts_at_beginning(self):
        s=self.make();s.song.timeline.select(4);s.song.timeline.select(4,True);s.toggle(0)
        self.assertEqual(s.current_step,1)
    def test_each_song_has_atomic_limit(self):
        s=Session()
        for index in range(64):
            s.select_pad(index);s.song.timeline.insert(0,'preset',64)
            before=s.song.timeline.blocks
            with self.assertRaisesRegex(ValueError,'64-step limit reached'):s.song.timeline.insert(1,'overflow')
            self.assertEqual(s.song.timeline.blocks,before)
    def test_state_roundtrip(self):
        s=self.make();s.song.timeline.select(1);s.song.timeline.toggle_loop();s.song.delay=15;s.song.name='Имя';s.song.colors={'preset':'#112233'}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            p=Path(folder)/'state.json';state.save(p,s);loaded=state.load(p)
            self.assertEqual(state.encode(s),state.encode(loaded));self.assertEqual(len(list(Path(folder).iterdir())),1)
            self.assertFalse(loaded.active)
    def test_invalid_state(self):
        d=state.encode(self.make());d['pads'][0]['blocks'][0]['length']=65
        with self.assertRaises(ValueError):state.decode(d)

if __name__=='__main__':unittest.main()
