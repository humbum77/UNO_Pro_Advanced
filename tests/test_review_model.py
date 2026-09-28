import unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
from live_creator.core.session import Session,Loop,Transport
from live_creator.core.clipboard import Clipboard
from live_creator.core import state,paths
from live_creator.devices.uno.timing import sequence_beats,decode_sequence_length

class ReviewTests(unittest.TestCase):
    def test_confirmed_binary_length_all_captures(self):
        for length in (1,2,4,8,9,10,16,17,32,33,48,64):
            raw=bytearray(1081);value=length*8-1;raw[207]=value&127;raw[208]=value>>7
            self.assertEqual(decode_sequence_length(raw),length)
        self.assertIsNone(decode_sequence_length(b'short'))
    def test_marker_collision_atomic_known_issue(self):
        s,a=self.make();a.set_marker(1,'INTRO');a.set_marker(3,'VERSE');a.select(1);before=a.blocks
        with self.assertRaisesRegex(ValueError,'Marker conflict'):a.delete_selected()
        self.assertEqual(a.blocks,before);self.assertEqual(a.markers,{1:'INTRO',3:'VERSE'})
    def make(self):
        s=Session(resolver=lambda ref:4);a=s.song.timeline
        for ref in ('intro','chorus','outro'):a.insert(len(a.blocks),ref,2)
        return s,a
    def test_assigned_no_jump_active_exit(self):
        s,a=self.make();s.toggle(0);s.update(1);a.select(3);s.assign_loop()
        self.assertEqual(s.position,1);self.assertEqual(s.loop_state,Loop.ASSIGNED)
        s.update(4);self.assertEqual(s.current_step,3);self.assertEqual(s.loop_state,Loop.ACTIVE)
        s.update(9);self.assertEqual(s.position,5);s.toggle(9)
        self.assertEqual(s.loop_state,Loop.NONE);self.assertTrue(s.active);self.assertEqual(s.position,5)
        s.update(13);self.assertEqual(s.current_step,5);s.update(16);self.assertFalse(s.active)
    def test_assigned_before_start_does_not_jump(self):
        s,a=self.make();a.select(3);s.assign_loop();a.select(1);s.toggle(0)
        self.assertEqual(s.position,0);self.assertEqual(s.loop_state,Loop.ASSIGNED)
    def test_duration_excludes_loops(self):
        s,a=self.make();duration=s.duration(s.song);a.select(3);s.assign_loop()
        self.assertEqual(s.duration(s.song),duration);self.assertEqual(duration,12)
    def test_snapshot_isolated_from_edit_delete_and_pad(self):
        s,a=self.make();s.toggle(0);id=s.playing_block_id
        a.select(1);a.delete_selected();s.select_pad(1);s.update(1)
        self.assertEqual(s.playing_block_id,id);self.assertEqual(s.playing_pad,0)
    def test_marker_section_and_delete(self):
        s,a=self.make();a.set_marker(1,'INTRO');a.set_marker(5,'OUTRO')
        self.assertEqual(a.sections(),[(1,4,'INTRO'),(5,6,'OUTRO')])
        a.select(1);a.delete_selected();self.assertEqual(a.markers,{1:'INTRO',3:'OUTRO'})
        a.select(3);a.delete_selected();self.assertEqual(a.markers,{1:'INTRO'})
    def test_clipboard_no_marker_and_independent_color(self):
        s,a=self.make();a.set_marker(1,'INTRO');a.select(1);a.set_color(a.selection,'#345678')
        clip=Clipboard();clip.copy_blocks(s.song);s.select_pad(1);clip.paste_blocks(s.song,0)
        self.assertFalse(s.song.timeline.markers);self.assertEqual(s.song.timeline.blocks[0].color,'#345678')
        self.assertEqual(s.song.timeline.blocks[0].preset,'intro')
    def test_song_clipboard_markers_no_alias(self):
        s,a=self.make();a.set_marker(1,'INTRO');clip=Clipboard();clip.copy_song(s.song);song=clip.paste_song()
        song.timeline.set_marker(1,'CHANGED');self.assertEqual(a.markers[1],'INTRO')
        self.assertNotEqual(a.blocks[0].id,song.timeline.blocks[0].id)
    def test_left_resize_anchored_end(self):
        s,a=self.make();id=a.blocks[1].id;a.resize_left(id,1)
        b,start,end=next(x for x in a.ranges() if x[0].id==id);self.assertEqual((start,end),(4,4))
        a.resize_left(id,-1);self.assertEqual(a.length,6);self.assertEqual(a.blocks[1].length,2)
    def test_state_v2_markers_and_color(self):
        s,a=self.make();a.set_marker(3,'CHORUS');a.set_color({a.blocks[0].id},'#234567')
        loaded=state.decode(state.encode(s));self.assertEqual(loaded.song.timeline.markers,{3:'CHORUS'})
        self.assertEqual(loaded.song.timeline.blocks[0].color,'#234567')
    def test_storage_root(self):
        with patch.dict(os.environ,{'LOCALAPPDATA':str(Path(__file__).parent.resolve())}):
            self.assertEqual(paths.state_path(),Path(__file__).parent.resolve()/'UnoLive'/'state'/'live_creator_state.json')
    def test_metadata_timing_no_guess_or_writes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            p=Path(folder)/'preset.unosyp';p.write_bytes(b'binary unknown')
            self.assertIsNone(sequence_beats(str(p)))
            data={'sequence':{'length':32,'length_confirmed':True,'resolution':'1/16'}}
            p.write_text(json.dumps(data));self.assertEqual(sequence_beats(str(p)),8)
            del data['sequence']['resolution'];p.write_text(json.dumps(data));self.assertIsNone(sequence_beats(str(p)))
            self.assertEqual(len(list(Path(folder).iterdir())),1)
    def test_confirmed_binary_duration(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            p=Path(folder)/'confirmed.unosyp';raw=bytearray(1081);value=33*8-1;raw[207]=value&127;raw[208]=value>>7;p.write_bytes(raw)
            self.assertEqual(sequence_beats(str(p)),8.25)
            s=Session(resolver=sequence_beats);s.song.timeline.insert(0,str(p),3)
            self.assertEqual(s.duration(s.song),12.375)

if __name__=='__main__':unittest.main()
