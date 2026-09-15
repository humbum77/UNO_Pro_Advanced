import unittest
from live_creator.core.arrangement import Arrangement
from live_creator.core.session import Session
from live_creator.ui.layout import Slots,pulse

class NextIterationTests(unittest.TestCase):
    def test_boundary_segments(self):
        g=Slots(1176);segments=list(g.segments(30,35))
        self.assertEqual([(s,e) for x,y,x2,y2,s,e in segments],[(30,32),(33,35)])
        self.assertAlmostEqual(segments[0][2]-segments[0][0],3*g.pitch)
        self.assertAlmostEqual(segments[1][2]-segments[1][0],3*g.pitch)
    def test_slots_fit(self):
        for width in (936,1176,1416):
            g=Slots(width)
            for step in range(1,65):
                x,y=g.point(step);self.assertLessEqual(x+g.pitch,width-9)
                self.assertEqual(int(g.position(x+g.pitch/2,y+10)),step)
    def test_delete_multiple(self):
        a=Arrangement();a.insert(0,'A',3);a.insert(1,'B',4);a.insert(2,'C',2)
        a.select(1);a.select(4,True);a.delete_selected()
        self.assertEqual([(s,e) for b,s,e in a.ranges()],[(1,2)])
        self.assertFalse(a.selection);self.assertIsNone(a.selected_step)
    def test_drop_gap_atomic(self):
        a=Arrangement();a.insert_at_slot(0,'A',64);self.assertEqual(a.length,64)
        before=a.blocks
        with self.assertRaises(ValueError):a.insert_at_slot(2,'B',65)
        self.assertEqual(a.blocks,before)
    def test_one_step_uses_sequence_duration(self):
        s=Session(resolver=lambda ref:16);s.song.timeline.insert(0,'A');s.toggle(0)
        for now in (.01,.5,1,7.9):s.update(now);self.assertTrue(s.active)
        s.select_pad(1);self.assertEqual(s.playing_pad,0);s.update(8);self.assertFalse(s.active)
    def test_pulse_soft(self):
        self.assertNotEqual(pulse('#496879',0),pulse('#496879',.75))
        for now in (0,.75,1.5,2.25):
            p=pulse('#496879',now)
            for i in (1,3,5):self.assertGreater(int(p[i:i+2],16),int('#496879'[i:i+2],16))
    def test_unknown_duration_does_not_start(self):
        s=Session();s.song.timeline.insert(0,'A',3)
        with self.assertRaisesRegex(ValueError,'duration unknown'):s.toggle(0)
        self.assertFalse(s.active)

if __name__=='__main__':unittest.main()
