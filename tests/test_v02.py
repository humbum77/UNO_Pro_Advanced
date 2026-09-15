import unittest
from pathlib import Path
import tempfile
from live_creator.devices.uno.library import PresetLibrary,children
from live_creator.core.arrangement import Arrangement

class V02Tests(unittest.TestCase):
    def test_reference_only(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            p=Path(folder)/'Bass.unosyp';raw=bytes(range(256))*5;p.write_bytes(raw)
            lib=PresetLibrary();id=lib.capture(p);p.unlink()
            self.assertEqual(lib.label(id),'PRESET NOT FOUND')
            self.assertFalse(hasattr(lib,'assets'))
            p.write_bytes(raw);self.assertEqual(lib.capture(p),id)
    def test_browser(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root=Path(folder);(root/'songs').mkdir();(root/'Bass').mkdir();(root/'z.unosyp').touch();(root/'x.txt').touch()
            self.assertEqual([p.name for p in children(root)],['Bass','z.unosyp'])
    def test_playhead_independent(self):
        a=Arrangement();a.insert(0,'id',3);a.select(1);a.set_playhead(3);a.select(2)
        self.assertEqual(a.playhead,3);a.resize(a.blocks[0].id,1);self.assertIsNone(a.playhead)
        with self.assertRaises(ValueError):a.set_playhead(2)

if __name__=='__main__':unittest.main()
