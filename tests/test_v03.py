import unittest,tempfile,zipfile
from pathlib import Path
from live_creator.core.arrangement import Arrangement
from live_creator.devices.uno.library import PresetLibrary
from live_creator.devices.uno import song

class V03Tests(unittest.TestCase):
    def model(self):
        a=Arrangement();a.insert(0,'A',3);a.insert(1,'B',2);a.insert(2,'C',1);return a
    def test_start_and_selection_independent(self):
        a=self.model();a.select(4);a.start();a.select(1)
        self.assertEqual(a.playhead,4);a.advance();self.assertEqual(a.playhead,5)
        a.stop();self.assertFalse(a.playing)
    def test_default_start_and_end(self):
        a=self.model();a.start();self.assertEqual(a.playhead,1)
        for _ in range(6):a.advance()
        self.assertFalse(a.playing);self.assertEqual(a.playhead,6)
    def test_multiple_selection_loop(self):
        a=self.model();a.select(1);a.select(4,True);a.toggle_loop()
        self.assertEqual(len(a.selection),2);self.assertEqual(a.loop_range,(1,5))
        a.start();a.select(6);a.advance();a.advance();self.assertEqual(a.playhead,1)
        self.assertEqual(a.loop_range,(1,5))
    def test_toggle_loop(self):
        a=self.model();a.select(4);a.toggle_loop();a.toggle_loop();self.assertIsNone(a.loop_range)
    def test_rejected_edit_preserves_transport(self):
        a=self.model();a.select(1);a.toggle_loop();a.start()
        with self.assertRaises(ValueError):a.resize(a.blocks[0].id,64)
        self.assertTrue(a.playing);self.assertEqual(a.loop_range,(1,3))
    def test_song_self_contained(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            root=Path(d);p=root/'Bass.unosyp';raw=bytes(range(256))*5;p.write_bytes(raw)
            library=PresetLibrary();id=library.capture(p);a=Arrangement();a.insert(0,id,3);a.insert(1,None,2);a.insert(2,id);a.set_tempo(137)
            path=root/'Song.unosong';song.save(path,a,library);p.unlink();b,assets=song.load(path)
            self.assertEqual(assets.assets[id],raw);self.assertEqual(b.tempo,137);self.assertEqual([(x.preset,x.length) for x in b.blocks],[(id,3),(None,2),(id,1)])
            with zipfile.ZipFile(path) as z:self.assertEqual(len(z.namelist()),2)
    def test_bad_song(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            path=Path(d)/'bad.unosong'
            with zipfile.ZipFile(path,'w') as z:z.writestr('manifest.json','{"format":"other","version":1}')
            with self.assertRaises(ValueError):song.load(path)

if __name__=='__main__':unittest.main()
