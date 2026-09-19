import unittest

from ProtocolLab import protocol_lab as lab


class ProtocolLabParserTests(unittest.TestCase):
    def test_request_shape_0x37(self):
        raw = bytes.fromhex("F0 00 21 1A 02 03 37 00 00 F7")
        p = lab.parse_ik_sysex(raw)
        self.assertTrue(p.valid_ik)
        self.assertEqual(p.command, 0x37)
        self.assertEqual(p.command_offset, 6)
        self.assertEqual(p.direction_shape, "REQUEST/NOTIFY-LIKE")

    def test_response_shape_0x37(self):
        raw = bytes.fromhex("F0 00 21 1A 02 03 00 37 00 00 01 02 F7")
        p = lab.parse_ik_sysex(raw)
        self.assertTrue(p.valid_ik)
        self.assertEqual(p.command, 0x37)
        self.assertEqual(p.command_offset, 7)
        self.assertEqual(p.payload, bytes.fromhex("00 00 01 02"))

    def test_unknown_stays_unknown(self):
        raw = bytes.fromhex("F0 00 21 1A 02 03 55 01 F7")
        p = lab.parse_ik_sysex(raw)
        self.assertEqual(p.command, 0x55)
        self.assertEqual(p.role, "UNKNOWN")

    def test_non_ik_rejected(self):
        p = lab.parse_ik_sysex(bytes.fromhex("F0 7D 01 F7"))
        self.assertFalse(p.valid_ik)

    def test_label_diff(self):
        m = lab.CaptureModel()
        m.mark("A")
        m.add_bytes(bytes.fromhex("F0 00 21 1A 02 03 37 00 00 F7"))
        m.mark("B")
        m.add_bytes(bytes.fromhex("F0 00 21 1A 02 03 37 00 00 F7"))
        m.add_bytes(bytes.fromhex("F0 00 21 1A 02 03 3E 00 00 01 F7"))
        self.assertEqual(m.diff_labels("A", "B"), [("0x37", 1, 1, 0), ("0x3E", 0, 1, 1)])


if __name__ == "__main__":
    unittest.main()
