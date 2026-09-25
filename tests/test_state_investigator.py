import unittest
from ProtocolLab.state_investigator import changed_bytes, changed_bits, stable_bit_changes, unsolicited_signature

class InvestigatorTests(unittest.TestCase):
    def test_byte_and_bit_diff(self):
        self.assertEqual(changed_bytes(b"\x00\x10",b"\x00\x14"),[(1,0x10,0x14,0x04)])
        self.assertEqual(changed_bits(b"\x00\x10",b"\x00\x14"),[(1,0x04,False,True)])
    def test_stable_correlation(self):
        pairs=[(b"\x00\x10",b"\x00\x14"),(b"\x20\x10",b"\x20\x14")]
        self.assertEqual(stable_bit_changes(pairs),[(1,0x04,False,True)])
    def test_clock_is_removed(self):
        c=unsolicited_signature([b"\xF8",b"\xFA",b"\xFA"])
        self.assertNotIn(b"\xF8",c); self.assertEqual(c[b"\xFA"],2)
if __name__=="__main__": unittest.main()
