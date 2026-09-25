import unittest
from ProtocolLab import unosyp_probe as p


class UnosypProbeTests(unittest.TestCase):
    def test_non_binary_is_not_promoted(self):
        r = p.probe_bytes(b'{"name":"x"}')
        self.assertFalse(r.binary_pro_format)
        self.assertIsNone(r.automation_byte_count)

    def test_zero_automation(self):
        data = bytearray(600)
        data[:4] = p.BINARY_MAGIC
        data[494] = 0
        data[495] = 0
        r = p.probe_bytes(bytes(data))
        self.assertEqual(r.automation_byte_count, 0)
        self.assertEqual(r.automation_entries_hex, ())

    def test_two_byte_entries_preserved_raw(self):
        data = bytearray(600)
        data[:4] = p.BINARY_MAGIC
        data[494] = 4
        data[495] = 0x12
        data[496:500] = bytes.fromhex("58 0E 08 C3")
        r = p.probe_bytes(bytes(data))
        self.assertEqual(r.automation_byte_count, 4)
        self.assertEqual(r.automation_reserved_byte, 0x12)
        self.assertEqual(r.automation_entries_hex, ("58 0E", "08 C3"))
        self.assertEqual(r.trailing_offset, 500)


if __name__ == "__main__":
    unittest.main()
