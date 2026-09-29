"""The TUNE scale grammar confirmed by the operator on 2026-09-29.

The device reads the first hundred cents in cents and the rest in semitones:
0, 1c..99c, 1st, 1st1c..1st99c, 2st, 2st1c..2st99c, ... up to 24st, mirrored on
the negative side. This pins the display grammar only; the native automation
byte encoding is still undetermined and is not asserted here.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import automation_metadata
from automation_metadata import tune_label


class TuneScale(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(tune_label(0), "0")
        self.assertEqual(tune_label(0.0), "0")

    def test_first_hundred_cents_are_read_in_cents(self):
        for c in range(1, 100):
            self.assertEqual(tune_label(c / 100), f"{c}c")

    def test_whole_semitones_have_no_cent_part(self):
        for st in range(1, 25):
            self.assertEqual(tune_label(st), f"{st}st")

    def test_semitone_plus_cents(self):
        for st in range(1, 25):
            for c in range(1, 100):
                self.assertEqual(tune_label(st + c / 100), f"{st}st{c}c")

    def test_negative_side_mirrors(self):
        self.assertEqual(tune_label(-0.01), "-1c")
        self.assertEqual(tune_label(-0.99), "-99c")
        self.assertEqual(tune_label(-1), "-1st")
        self.assertEqual(tune_label(-1.5), "-1st50c")
        self.assertEqual(tune_label(-24), "-24st")
        self.assertEqual(tune_label(-12.34), "-12st34c")
        self.assertEqual(tune_label(-24 / 100), "-24c")

    def test_the_ladder_the_operator_listed(self):
        # 0; 1c-99c; 1st; 1st1c-1st99c; 2st; 2st1c-2st99c; ... up to 24 st.
        # 24st is the top of the two-octave range, so the ladder stops there.
        expected = ["0"]
        expected += [f"{c}c" for c in range(1, 100)]
        for st in range(1, 24):
            expected.append(f"{st}st")
            expected += [f"{st}st{c}c" for c in range(1, 100)]
        expected.append("24st")
        got = [tune_label(i / 100) for i in range(0, 2401)]
        self.assertEqual(got, expected)
        self.assertEqual(len(got), 2401)

    def test_parameter_uses_the_device_grammar(self):
        meta = automation_metadata.PARAMETERS["TUNE 1"]
        self.assertIs(meta.formatter, tune_label)
        self.assertEqual(meta.format(1.5), "1st50c")
        self.assertEqual(meta.format(-0.5), "-50c")
        self.assertEqual(meta.format(0), "0")
        self.assertEqual(meta.format(24), "24st")
        self.assertIsNone(meta.format(None))
        self.assertEqual(meta.scale_labels(), ("24st", "0", "-24st"))

    def test_status_no_longer_claims_the_interpolation_is_unknown(self):
        status = automation_metadata.PARAMETERS["TUNE 1"].status
        self.assertIn("CONFIRMED hybrid cents/semitone scale", status)
        self.assertNotIn("PARTIAL", status)
        self.assertIn("native byte encoding of this scale is NOT yet determined",
                      status)

    def test_range_is_two_octaves_in_semitones(self):
        meta = automation_metadata.PARAMETERS["TUNE 1"]
        self.assertEqual((meta.minimum, meta.maximum), (-24, 24))
        self.assertEqual(meta.polarity, "bipolar")

    def test_other_parameters_keep_the_plain_formatting(self):
        self.assertEqual(automation_metadata.PARAMETERS["CUTOFF 1"].format(256), "256")
        self.assertEqual(
            automation_metadata.PARAMETERS["CUTOFF 1"].scale_labels(),
            ("512", "256", "0"))
        self.assertEqual(
            automation_metadata.PARAMETERS["SPACING"].scale_labels(),
            ("64", "0", "-64"))


class TuneNativeCodec(unittest.TestCase):
    """The native TUNE automation codec the project already carries."""

    def test_it_round_trips_the_whole_ladder(self):
        import uno_step_automation_decoder as decoder
        for cents in (0, 1, 50, 99, 100, 101, 150, 199, 200, 1200, 2400,
                      -1, -100, -150, -1250):
            semitones = cents / 100
            raw = decoder.encode_native_value("TUNE1", semitones)
            self.assertEqual(len(raw), 2, f"{cents}c encoded to {raw.hex()}")
            back = decoder.decode_native_value("TUNE1", raw)
            self.assertAlmostEqual(back, semitones, places=9,
                                   msg=f"{cents}c -> {raw.hex()} -> {back}")

    def test_the_one_cent_band_is_expressible(self):
        import uno_step_automation_decoder as decoder
        # 1st1c .. 1st99c, the band the operator asked about
        for cents in range(101, 200):
            raw = decoder.encode_native_value("TUNE1", cents / 100)
            self.assertAlmostEqual(
                decoder.decode_native_value("TUNE1", raw), cents / 100, places=9)
        self.assertEqual(decoder.encode_native_value("TUNE1", 1.0).hex(), "0064")
        self.assertEqual(decoder.encode_native_value("TUNE1", 1.01).hex(), "0065")
        self.assertEqual(decoder.encode_native_value("TUNE1", 1.99).hex(), "00c7")
        self.assertEqual(decoder.encode_native_value("TUNE1", 2.0).hex(), "00c8")

    def test_known_capture_reading_locates_the_labelled_value(self):
        # The captures store the value 7-bit packed at file offset 0x01F1, so
        # pair/16 is cents. Controls below use captures whose value is known.
        import struct
        import uno_step_automation_decoder as decoder
        ladder = Path(r"D:\UNO\unosyp")
        if not ladder.is_dir():
            self.skipTest("instrument capture corpus not present")
        for name, cents in (("TUN1S1_99C", 99), ("TUN1S1_1ST", 100),
                            ("TUN1S1_2ST", 200)):
            path = ladder / f"{name}.unosyp"
            if not path.exists():
                self.skipTest(f"controlled fixture missing: {path}")
            body = path.read_bytes()
            lo = struct.unpack_from("<I", body, 297)[0]
            page1 = body[301:301 + lo]
            pair = ((page1[196] & 0x7F) | ((page1[197] & 0x7F) << 7))
            self.assertEqual(pair / 16.0, float(cents),
                             f"{name}: page1[196:198] -> {pair/16.0} not {cents}")

    def test_dhk_y_carries_a_value_inside_the_one_cent_band(self):
        # DHK_Y is the operator's data-knob capture. The same reading that
        # reproduces 99c, 1st and 2st in the controls gives 146c here, which is
        # 1st46c and lies strictly between 1st and 2st.
        import struct
        from automation_metadata import tune_label
        path = Path(r"D:\Documents\IK Multimedia\UNO Synth Pro Editor\1test\DHK_Y.unosyp")
        if not path.exists():
            self.skipTest("instrument capture not present")
        body = path.read_bytes()
        lo = struct.unpack_from("<I", body, 297)[0]
        page1 = body[301:301 + lo]
        pair = ((page1[196] & 0x7F) | ((page1[197] & 0x7F) << 7))
        cents = pair / 16.0
        self.assertEqual(cents, 146.0)
        self.assertTrue(101 <= cents <= 199)
        self.assertEqual(tune_label(cents / 100), "1st46c")


if __name__ == "__main__":
    unittest.main()
