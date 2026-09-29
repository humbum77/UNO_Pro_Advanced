"""Regression tests for the preset read/write wiring.

Each test corresponds to a defect found on 2026-09-29 where the editor read a
preset correctly but lost it, mislabelled it, or could not write it back.
"""
import copy
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import data_model
import matrix_codec as mc
import native_automation as na
import storage
import unosyp_state_decoder as usd

CORPUS = pathlib.Path(r"E:\unosyp_to_hex")
REQUIRED_CORPUS = CORPUS.exists()


def load_corpus_preset(name):
    for path in CORPUS.rglob(f"{name}.hex.plain.txt"):
        tokens = path.read_text(encoding="utf-8", errors="replace").split()
        data = bytes(int(t, 16) for t in tokens if re.fullmatch(r"[0-9a-fA-F]{1,2}", t))
        if len(data) >= 1000:
            return data
    raise FileNotFoundError(name)


def _write_temp(data, tmp, name):
    path = pathlib.Path(tmp) / name
    path.write_bytes(data)
    return path


class MatrixWriteTests(unittest.TestCase):
    """The matrix was decoded but never written back."""

    def setUp(self):
        if not REQUIRED_CORPUS:
            self.skipTest('corpus not present')
        self.data = load_corpus_preset("3RD OF MARCH")
        self.routes = mc.decode_matrix(mc.decode_file_state(self.data))
        self.base = [{'source': r['source_file_id'], 'destination': r['destination_file_id'],
                      'amount': r['amount'], 'fade': r['fade']} for r in self.routes]

    def test_writing_the_unchanged_matrix_is_a_no_op(self):
        self.assertEqual(na.apply_matrix_to_file(self.data, self.base), self.data)

    def test_a_edited_route_survives_a_write_and_reload(self):
        edited = [dict(r) for r in self.base]
        edited[0]['amount'] = 33
        out = na.apply_matrix_to_file(self.data, edited)
        back = mc.decode_matrix(mc.decode_file_state(out))
        self.assertEqual(back[0]['amount'], 33)
        self.assertNotEqual(back[0]['amount'], self.routes[0]['amount'])

    def test_the_file_tail_is_preserved(self):
        edited = [dict(r) for r in self.base]
        edited[0]['amount'] = 21
        out = na.apply_matrix_to_file(self.data, edited)
        self.assertEqual(len(out), len(self.data))
        self.assertEqual(out[mc.FILE_STATE_SIZE:], self.data[mc.FILE_STATE_SIZE:])

    def test_other_routes_are_not_disturbed(self):
        edited = [dict(r) for r in self.base]
        edited[0]['amount'] = 12
        back = mc.decode_matrix(mc.decode_file_state(na.apply_matrix_to_file(self.data, edited)))
        for i in range(1, 16):
            if i + 1 in mc.SEQUENCER_OVERLAP_SLOTS:
                continue
            with self.subTest(route=i + 1):
                self.assertEqual(back[i]['source_file_id'], self.routes[i]['source_file_id'])
                self.assertEqual(back[i]['destination_file_id'], self.routes[i]['destination_file_id'])

    def test_sequencer_fields_survive_a_matrix_write(self):
        # The sequence fields live in the unpacked 260-byte state, not in the
        # packed file stream, so compare those.
        edited = [dict(r) for r in self.base]
        edited[0]['amount'] = 44
        out = na.apply_matrix_to_file(self.data, edited)
        before = mc.decode_file_state(self.data)
        after = mc.decode_file_state(out)
        for index in (207, 208, 209, 210, 212):
            with self.subTest(byte=index):
                self.assertEqual(after[index], before[index],
                                 'a matrix write must not disturb the sequencer bytes')

    def test_sequencer_overlapping_routes_are_refused(self):
        # SEQUENCER_OVERLAP_SLOTS holds 1-based route numbers.
        for label in mc.SEQUENCER_OVERLAP_SLOTS:
            slot = label - 1
            edited = [dict(r) for r in self.base]
            edited[slot]['amount'] = (edited[slot]['amount'] or 0) + 7
            with self.subTest(route=label):
                with self.assertRaises(ValueError):
                    na.apply_matrix_to_file(self.data, edited)

    def test_codec_itself_refuses_overlapping_writes(self):
        with self.assertRaises(ValueError):
            mc.write_matrix_to_file(self.data, {5: {'amount': 12}}, allow_overlapping=False)

    def test_preset_model_carries_the_matrix(self):
        preset = data_model.Preset()
        self.assertEqual(preset.matrix, [])
        preset.matrix = self.base
        self.assertEqual(len(preset.matrix), 16)

    def test_the_save_path_actually_passes_the_matrix_to_the_writer(self):
        """The writer existed but the save path never called it with a matrix."""
        if not REQUIRED_CORPUS:
            self.skipTest('corpus not present')
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "saved.unosyp"
            preset = data_model.Preset(name="rt", source="local")
            preset.sequence = storage.load_binary_unosyp_sequence(
                _write_temp(self.data, tmp, "src.unosyp"))
            edited = [dict(r) for r in self.base]
            edited[0]['amount'] = 27
            preset.matrix = edited
            storage.save_working_preset(preset, path)
            back = mc.decode_matrix(mc.decode_file_state(path.read_bytes()))
        self.assertEqual(back[0]['amount'], 27,
                         'the matrix never reached the saved file')

    def test_the_overlap_guard_is_reachable_from_the_save_path(self):
        """Guard must fire on a real save, not only when called directly."""
        if not REQUIRED_CORPUS:
            self.skipTest('corpus not present')
        slot = mc.SEQUENCER_OVERLAP_SLOTS[0] - 1
        with tempfile.TemporaryDirectory() as tmp:
            preset = data_model.Preset(name="rt", source="local")
            preset.sequence = storage.load_binary_unosyp_sequence(
                _write_temp(self.data, tmp, "src.unosyp"))
            edited = [dict(r) for r in self.base]
            edited[slot]['amount'] = (edited[slot]['amount'] or 0) + 9
            preset.matrix = edited
            with self.assertRaises(ValueError):
                storage.save_working_preset(preset, pathlib.Path(tmp) / "bad.unosyp")

    def test_destination_labels_come_from_the_registry_not_a_list_index(self):
        """app.py used to index the visible selector with a native FILE id."""
        source = (pathlib.Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("decode_destination_file_id", source)
        self.assertNotIn("MATRIX_DESTINATIONS[di]", source,
                         "a native FILE id must not index the UI selector")


class MatrixLabelTests(unittest.TestCase):
    """Destination labels were looked up by UI index instead of native FILE id."""

    def test_every_registry_id_resolves_to_its_own_name(self):
        for item in mc.DESTINATIONS:
            with self.subTest(file_id=item.file_id):
                self.assertEqual(mc.decode_destination_file_id(item.file_id), item.name)

    def test_ids_above_the_visible_selector_still_resolve(self):
        visible = set(mc.MATRIX_DESTINATION_FILE_NAMES)
        above = [i for i in mc.DEST_BY_FILE if mc.DEST_BY_FILE[i].name not in visible]
        self.assertTrue(above, 'expected ids outside the visible selector')
        for file_id in above:
            with self.subTest(file_id=file_id):
                resolved = mc.decode_destination_file_id(file_id)
                self.assertNotEqual(resolved, f'FILE 0x{file_id:02X}')

    def test_source_ids_resolve(self):
        for item in mc.SOURCES:
            with self.subTest(file_id=item.file_id):
                self.assertEqual(mc.decode_source_file_id(item.file_id), item.name)

    def test_the_cross_mod_family_is_anchored_not_sequential(self):
        """Mod 13 must live at FILE 0x32, not at UI index 13."""
        self.assertEqual(mc.decode_destination_file_id(0x32), 'Mod 13 Amount')
        self.assertEqual(mc.DEST_BY_NAME['Mod 1 Amount'].file_id, 0x26)


class MatrixAmountRangeTests(unittest.TestCase):
    def test_native_amount_range_is_minus_63_to_plus_64(self):
        self.assertEqual((mc.AMOUNT_MIN, mc.AMOUNT_MAX), (-63, 64))

    def test_out_of_range_amount_is_refused(self):
        for bad in (-64, 65, 200):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    mc.encode_amount(bad)

    def test_editor_range_matches_the_codec(self):
        import app as appmod
        self.assertEqual(appmod.MATRIX_AMOUNT_RANGE, (mc.AMOUNT_MIN, mc.AMOUNT_MAX))


class AutomationDecoderGateTests(unittest.TestCase):
    """The canonical decoder was gated behind a recognised profile."""

    def test_container_metadata_is_kept_for_every_preset(self):
        if not REQUIRED_CORPUS:
            self.skipTest('corpus not present')
        data = load_corpus_preset("BASS")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "p.unosyp"
            path.write_bytes(data)
            seq = storage.load_binary_unosyp_sequence(path)
        self.assertIsNotNone(seq)
        native = seq.native_automation or {}
        self.assertIn('container_entry_count', native)
        self.assertIn('lanes_populated', native)
        self.assertGreater(native.get('entry_count', 0), 0,
                           'BASS is known to carry native automation events')
        # The status must say the targets are unresolved rather than hiding them.
        self.assertIsNone(native.get('profile'))
        self.assertEqual(native.get('lanes_populated'), 0)

    def test_a_preset_with_named_targets_reaches_the_lanes(self):
        if not REQUIRED_CORPUS:
            self.skipTest('corpus not present')
        data = load_corpus_preset("FAKE 808")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "p.unosyp"
            path.write_bytes(data)
            seq = storage.load_binary_unosyp_sequence(path)
        filled = sum(1 for lane in seq.automation for v in lane.get('values', []) if v is not None)
        self.assertGreater(filled, 0, 'a resolved profile must populate editor lanes')


if __name__ == '__main__':
    unittest.main()
