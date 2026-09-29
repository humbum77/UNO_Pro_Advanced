"""Modulation-matrix codec checked against the unified evidence database.

These tests replace hand-written expectations with real device captures. When
the codec regresses, they fail on the actual bytes rather than on an
assumption about them.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matrix_codec as mc
from tests import evidence_db


class MatrixCodecRegistryTests(unittest.TestCase):
    def test_registry_is_the_canonical_one(self):
        self.assertEqual(len(mc.SOURCES), 38)
        self.assertEqual(len(mc.DESTINATIONS), 54)
        self.assertEqual(len(mc.DESTINATIONS_VISIBLE), 49)
        self.assertEqual(len(mc.DESTINATION_HIDDEN), 5)

    def test_file_ids_and_ui_order_are_independent(self):
        """The defect this codec existed to remove: index used as a FILE id."""
        for name in (f'Mod {i} Amount' for i in range(1, 17)):
            item = mc.DEST_BY_NAME[name]
            ui = mc.MATRIX_DESTINATION_FILE_NAMES.index(name)
            self.assertEqual(ui, item.ui_index, f'{name}: UI order drifted')
            self.assertNotEqual(item.file_id, ui,
                                f'{name}: FILE id and UI position must not coincide')

    def test_destination_ui_lookup_writes_the_right_file_id(self):
        for name in mc.MATRIX_DESTINATION_FILE_NAMES:
            change = mc.ui_route_to_file_change('LFO 1', name, 10, 0)
            self.assertEqual(change['destination_file_id'], mc.DEST_BY_NAME[name].file_id)
            self.assertEqual(mc.decode_destination_file_id(change['destination_file_id']), name)

    def test_ui_names_cannot_override_the_file_id(self):
        """Passing the UI name list must not reintroduce index-as-FILE-id.

        A caller that hands the editor's ordered list in must still get FILE
        ids, because the UI order is a different namespace.
        """
        names = mc.MATRIX_DESTINATION_FILE_NAMES
        for name in names:
            change = mc.ui_route_to_file_change('LFO 1', name, 10, 0,
                                                 destination_names=names)
            self.assertEqual(change['destination_file_id'], mc.DEST_BY_NAME[name].file_id,
                             f'{name}: a UI index leaked into the FILE id')

    def test_hidden_destinations_remain_readable(self):
        for item in mc.DESTINATION_HIDDEN:
            self.assertEqual(mc.decode_destination_file_id(item.file_id), item.name)
            self.assertNotIn(item.name, mc.MATRIX_DESTINATION_FILE_NAMES)

    def test_amount_scale_round_trips(self):
        for value in (-63, -32, -1, 0, 1, 32, 63, 64):
            self.assertEqual(mc.decode_amount(mc.encode_amount(value)), value)
        for bad in (-64, 65, 1000):
            with self.assertRaises(ValueError):
                mc.encode_amount(bad)


class MatrixCodecBitGeometryTests(unittest.TestCase):
    def test_route_is_32_bits_at_the_documented_offsets(self):
        raw = bytearray(mc.RAW_STATE_SIZE)
        for slot, (source, destination, amount, fade) in enumerate([
            (0, 0, 0, 0), (21, 15, 64, 255), (63, 63, -63, 1), (37, 53, 32, 7),
            (7, 3, -32, 200), (14, 41, 10, 3), (22, 49, -10, 4), (9, 45, 40, 9),
            (19, 46, -40, 8), (2, 47, 20, 5), (30, 48, -20, 6), (31, 50, 63, 2),
            (12, 51, -63, 99), (17, 52, 1, 100), (24, 37, -1, 50), (5, 30, 40, 1),
        ]):
            base = mc.MATRIX_BIT + slot * mc.ROUTE_BITS
            mc._set_bits(raw, base - 3, 3, source & 7)
            mc._set_bits(raw, base, 3, (source >> 3) & 7)
            mc._set_bits(raw, base + 5, 6, destination)
            mc._set_bits(raw, base + 11, 10, fade * 4)
            mc._set_bits(raw, base + 21, 8, mc.encode_amount(amount))
        for slot, route in enumerate(mc.decode_matrix(bytes(raw))):
            with self.subTest(slot=slot):
                self.assertEqual(route['source_file_id'], [
                    0, 21, 63, 37, 7, 14, 22, 9, 19, 2, 30, 31, 12, 17, 24, 5][slot])
                self.assertEqual(route['destination_file_id'], [
                    0, 15, 63, 53, 3, 41, 49, 45, 46, 47, 48, 50, 51, 52, 37, 30][slot])

    def test_single_edit_leaves_other_routes_untouched(self):
        raw = bytearray(mc.RAW_STATE_SIZE)
        for slot in range(16):
            base = mc.MATRIX_BIT + slot * mc.ROUTE_BITS
            mc._set_bits(raw, base - 3, 3, (slot * 2) & 7)
            mc._set_bits(raw, base, 3, ((slot * 2) >> 3) & 7)
            mc._set_bits(raw, base + 5, 6, slot)
            mc._set_bits(raw, base + 21, 8, mc.encode_amount(slot - 8))
        before = mc.decode_matrix(bytes(raw))
        after = mc.decode_matrix(mc.encode_matrix(bytes(raw), {7: {'amount': 55}}))
        for slot in range(16):
            with self.subTest(slot=slot):
                if slot == 7:
                    self.assertEqual(after[slot]['amount'], 55)
                else:
                    self.assertEqual(after[slot], before[slot])

    def test_reserved_bits_survive_an_edit(self):
        raw = bytearray(mc.RAW_STATE_SIZE)
        for bit in range(mc.MATRIX_BIT + 3, mc.MATRIX_BIT + 16 * mc.ROUTE_BITS, 7):
            raw[bit // 8] |= 1 << (bit % 8)
        before = mc.decode_matrix(bytes(raw))
        after = mc.decode_matrix(mc.encode_matrix(bytes(raw), {0: {'amount': 5}}))
        self.assertEqual([r['reserved_raw'] for r in before],
                         [r['reserved_raw'] for r in after])

    def test_file_state_packing_round_trips(self):
        raw = bytes((i * 37 + 11) % 256 for i in range(mc.RAW_STATE_SIZE))
        packed = mc.encode_file_state(raw)
        self.assertEqual(len(packed), mc.FILE_STATE_SIZE)
        self.assertEqual(mc.decode_file_state(packed), raw)


class MatrixCodecEvidenceTests(unittest.TestCase):
    """Decodes the controlled captures stored in the evidence database."""

    @classmethod
    def setUpClass(cls):
        cls.con = evidence_db.connect()
        cls.presets = evidence_db.matrix_presets(cls.con)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_evidence_database_is_present_and_populated(self):
        self.assertGreater(evidence_db.corpus_size(self.con), 1000)

    def test_every_controlled_capture_resolves_to_a_known_source(self):
        for key, (blob, _replacement) in sorted(self.presets.items()):
            with self.subTest(capture=key):
                route = mc.decode_matrix(mc.decode_file_state(blob))[0]
                if key in evidence_db.UNRESOLVED_MATRIX_CAPTURES:
                    # Known-mis-saved: must stay unresolved rather than be invented.
                    self.assertEqual(route['source_file_id'], 0)
                else:
                    self.assertIsNotNone(mc.SOURCE_BY_FILE.get(route['source_file_id']),
                                         f'{key}: source {route["source_file_id"]} is unknown')

    def test_validated_captures_match_the_registry(self):
        """Each capture name states the source it routes; decode must agree.

        The capture names are abbreviated in the evidence archive, so the
        expected source is written out explicitly instead of being guessed
        from the filename.
        """
        expected_source = {
            'Base': 'Velocity',          # route present but no modulation source
            'Accent': 'Accent',
            'Gate': 'Gate',
            'Tie': 'Tie',
            'FilterEnv': 'Filter Env',
            'Amp Env': 'Amp Env',
            'CV 1 IN': 'CV 1 IN',
            'CV 2 IN': 'CV 2 IN',
            'GATE 1 IN': 'GATE 1 IN',
            'GATE 2 IN': 'GATE 2 IN',
            'FiltEnvAtt': 'Filter Env Attack',
            'FiltEnvDec': 'Filter Env Decay',
            'FiltEnvSus': 'Filter Env Sustain',
            'FiltEnvRel': 'Filter Env Release',
            'AmpEnvAtt': 'Amp Env Attack',
            'AmpEnvDec': 'Amp Env Decay',
            'AmpEnvSus': 'Amp Env Sustain',
            'AmpEnvRel': 'Amp Env Release',
        }
        for key, (blob, _replacement) in sorted(self.presets.items()):
            if key in evidence_db.UNRESOLVED_MATRIX_CAPTURES:
                continue
            with self.subTest(capture=key):
                self.assertIn(key, expected_source, f'{key} is not covered by this test')
                route = mc.decode_matrix(mc.decode_file_state(blob))[0]
                self.assertEqual(route['source_file_id'],
                                 mc.SOURCE_BY_NAME[expected_source[key]].file_id)

    def test_user_supplied_replacements_decode(self):
        expected = {'AmpEnvSus': 'Amp Env Sustain', 'GATE 2 IN': 'GATE 2 IN'}
        for key, (blob, replacement) in sorted(self.presets.items()):
            if key not in expected:
                continue
            with self.subTest(capture=key):
                self.assertTrue(replacement, f'{key} should be the user-supplied replacement')
                route = mc.decode_matrix(mc.decode_file_state(blob))[0]
                self.assertEqual(route['source_file_id'], mc.SOURCE_BY_NAME[expected[key]].file_id)

    def test_database_records_why_two_captures_are_unresolved(self):
        rows = self.con.execute(
            "SELECT action, reason FROM evidence_exclusions WHERE object_name='Matrix.zip'").fetchall()
        self.assertTrue(rows, 'the exclusion that documents this must stay in the database')
        blob = ' '.join(r['action'] + ' ' + r['reason'] for r in rows)
        self.assertIn('AmpEnvSus', blob)
        self.assertIn('GATE 2 IN', blob)


if __name__ == '__main__':
    unittest.main()
