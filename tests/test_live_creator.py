import unittest
from live_creator.core.arrangement import Arrangement

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.a=Arrangement(); self.first=self.a.insert(0,'Bass01',3); self.second=self.a.insert(1,'Bass02',2)
    def test_numbering(self):
        self.assertEqual([(s,e) for b,s,e in self.a.ranges()],[(1,3),(4,5)])
    def test_resize_ripple(self):
        self.a.resize(self.first,4)
        self.assertEqual([(s,e) for b,s,e in self.a.ranges()],[(1,4),(5,6)])
    def test_gap_and_reverse(self):
        self.a.move(self.second,2)
        self.assertEqual([(b.preset,s,e) for b,s,e in self.a.ranges()],[('Bass01',1,3),(None,4,5),('Bass02',6,7)])
        self.a.move(self.second,-1); self.assertEqual(self.a.blocks[1].length,1)
        self.a.move(self.second,-1); self.assertEqual(len(self.a.blocks),2)
    def test_replace_preserves_length(self):
        self.a.replace(self.first,'Lead'); self.assertEqual(self.a.blocks[0].length,3)
        self.assertEqual(self.a.steps()[2].preset,'Lead')
    def test_insert_ripple(self):
        self.a.insert(1,'Sub'); self.assertEqual(self.a.steps()[4].block_id,self.second)
    def test_limit_is_atomic(self):
        self.a.resize(self.second,61); before=self.a.blocks
        for fn in [lambda:self.a.insert(0,'X'),lambda:self.a.resize(self.first,4),lambda:self.a.move(self.first,1)]:
            with self.assertRaisesRegex(ValueError,'64-step limit reached'):fn()
            self.assertEqual(self.a.blocks,before)
    def test_selection_follows_block(self):
        self.a.select(5); self.a.resize(self.first,5); self.assertEqual(self.a.selected_step,7)
        self.a.resize(self.second,1); self.assertEqual(self.a.selected_step,6)
    def test_unused_and_invalid(self):
        for n in [0,6,64]:
            with self.assertRaises(ValueError):self.a.select(n)
        before=self.a.blocks
        for fn in [lambda:self.a.resize(self.first,0),lambda:self.a.move(self.second,-1),lambda:self.a.insert(-1,'X')]:
            with self.assertRaises(ValueError):fn()
            self.assertEqual(self.a.blocks,before)
    def test_leading_empty(self):
        self.a.move(self.first,2); self.assertIsNone(self.a.steps()[0].preset)
        self.a.move(self.first,-2); self.assertEqual(self.a.steps()[0].preset,'Bass01')

if __name__=='__main__':unittest.main()
