"""The device's modulation-matrix destination and source lists, as supplied by the
operator on 2026-09-29.

This is the authoritative statement of the FILE and WIRE ids. The development
report had left Destination OPEN; these lists close it. The registry in
UNO_MATRIX_FULL_REGISTRY.csv was previously justified from the VST3 numeric enum
alone, and the report's priority order put a hardware capture ahead of that for
destinations.

The lists are pinned here so the registry cannot drift from the device without a
test failing.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matrix_codec

# Verbatim, 2026-09-29. 0x00..0x35.
DESTINATIONS = (
    "OFF", "PITCH", "VOLUME", "OSC 1 TUNE", "OSC 1 WAVE", "OSC 1 LEVEL",
    "OSC 2 TUNE", "OSC 2 WAVE", "OSC 2 LEVEL", "OSC 2 FM AMOUNT",
    "OSC 3 TUNE", "OSC 3 WAVE", "OSC 3 LEVEL", "OSC 3 FM AMOUNT",
    "NOISE LEVEL", "FILTER 1 CUTOFF", "FILTER 1 RES", "FILTER 2 CUTOFF",
    "FILTER 2 RES", "FILTER SPACING", "LFO 1 WAVE", "LFO 1 RATE",
    "LFO 1 RETRIGGER", "LFO 2 WAVE", "LFO 2 RATE", "LFO 2 RETRIGGER",
    "FILTER 1 ENV AMOUNT", "FILTER 2 ENV AMOUNT", "AMP ENV AMOUNT",
    "DRIVE AMOUNT", "DELAY AMOUNT", "REVERB AMOUNT", "MOD AMOUNT",
    "CV OUT 1", "GATE OUT 1", "CV OUT 2", "GATE OUT 2", "ACCENT AMOUNT",
) + tuple(f"MOD {n} AMOUNT" for n in range(1, 17))

# Verbatim, 2026-09-29. 0x00..0x25.
SOURCES = (
    "VELOCITY", "MODWHEEL", "AFTERTOUCH", "KEY PITCH", "KEY GATE",
    "OSC 1 TUNE", "OSC 1 LEVEL", "OSC 2 TUNE", "OSC 2 LEVEL",
    "OSC 3 TUNE", "OSC 3 LEVEL", "NOISE", "FILTER 1 CUTOFF", "FILTER 1 RES",
    "FILTER 2 CUTOFF", "FILTER 2 RES", "FILTER SPACING", "LFO 1",
    "LFO 1 FADE IN", "LFO 2", "LFO 2 FADE IN", "FILTER ENV", "AMP ENV",
    "CV 1 IN", "GATE 1 IN", "CV 2 IN", "GATE 2 IN", "ACCENT", "GATE", "TIE",
    "FILTER ENV ATTACK", "FILTER ENV DECAY", "FILTER ENV SUSTAIN",
    "FILTER ENV RELEASE", "AMP ENV ATTACK", "AMP ENV DECAY",
    "AMP ENV SUSTAIN", "AMP ENV RELEASE",
)


def norm(text):
    return " ".join(str(text).upper().replace("_", " ").split())


def key(text):
    """Compare labels ignoring spacing only, so MODWHEEL and MOD WHEEL match."""
    return norm(text).replace(" ", "")


# The only place the registry and the operator's list spell a label differently.
# The registry reads "Mod Wheel", the device list reads "MODWHEEL". Same
# parameter, spacing only, so it is declared here instead of being normalised
# away silently.
KNOWN_SPACING_VARIANTS = {("MOD WHEEL", "MODWHEEL")}


class OperatorMatrixLists(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(DESTINATIONS), 54)
        self.assertEqual(len(SOURCES), 38)
        self.assertEqual(len(matrix_codec.DESTINATIONS), 54)
        self.assertEqual(len(matrix_codec.SOURCES), 38)

    def test_destination_file_and_wire_ids_match(self):
        self.assertEqual(len(matrix_codec.DESTINATIONS), len(DESTINATIONS))
        for expected_id, item in enumerate(matrix_codec.DESTINATIONS):
            self.assertEqual(item.file_id, expected_id,
                             f"destination 0x{expected_id:02X} file id is {item.file_id}")
            self.assertEqual(item.wire_id, expected_id,
                             f"destination 0x{expected_id:02X} wire id is {item.wire_id}")

    def test_destination_names_match_in_order(self):
        for expected_id, (item, want) in enumerate(
                zip(matrix_codec.DESTINATIONS, DESTINATIONS)):
            self.assertEqual(norm(item.name), norm(want),
                             f"destination 0x{expected_id:02X}: "
                             f"registry {item.name!r} vs operator {want!r}")

    def test_source_file_and_wire_ids_match(self):
        self.assertEqual(len(matrix_codec.SOURCES), len(SOURCES))
        for expected_id, item in enumerate(matrix_codec.SOURCES):
            self.assertEqual(item.file_id, expected_id,
                             f"source 0x{expected_id:02X} file id is {item.file_id}")
            self.assertEqual(item.wire_id, expected_id,
                             f"source 0x{expected_id:02X} wire id is {item.wire_id}")

    def test_source_names_match_in_order(self):
        for expected_id, (item, want) in enumerate(
                zip(matrix_codec.SOURCES, SOURCES)):
            if (norm(item.name), norm(want)) in KNOWN_SPACING_VARIANTS:
                self.assertEqual(key(item.name), key(want))
                continue
            self.assertEqual(norm(item.name), norm(want),
                             f"source 0x{expected_id:02X}: "
                             f"registry {item.name!r} vs operator {want!r}")

    def test_the_only_spelling_difference_is_the_declared_one(self):
        differing = []
        for kind, got, want in (("destination", matrix_codec.DESTINATIONS, DESTINATIONS),
                                ("source", matrix_codec.SOURCES, SOURCES)):
            for i, (item, expect) in enumerate(zip(got, want)):
                if norm(item.name) != norm(expect):
                    differing.append((kind, i, item.name, expect))
        self.assertEqual(len(differing), 1, differing)
        kind, i, have, want = differing[0]
        self.assertEqual((kind, i), ("source", 1))
        self.assertEqual((norm(have), norm(want)), ("MOD WHEEL", "MODWHEEL"))
        self.assertEqual(key(have), key(want))

    def test_mod_amount_block(self):
        # 0x26..0x35 is the MOD 1..16 block
        for n in range(1, 17):
            item = matrix_codec.DESTINATIONS[0x25 + n]
            self.assertEqual(norm(item.name), f"MOD {n} AMOUNT")
            self.assertEqual(item.file_id, 0x25 + n)

    def test_destination_ui_index_is_the_rank_among_selectable(self):
        selectable = [x for x in matrix_codec.DESTINATIONS if x.ui_index >= 0]
        for rank, item in enumerate(selectable):
            self.assertEqual(item.ui_index, rank, item.name)
        hidden = [x for x in matrix_codec.DESTINATIONS if x.ui_index < 0]
        self.assertEqual([x.name for x in hidden],
                         ["Pitch", "LFO 1 Retrigger", "LFO 2 Retrigger",
                          "Gate Out 1", "Gate Out 2"])

    def test_source_ui_order_is_the_device_order(self):
        # The operator asked for the source selector to follow the device. The
        # registry previously carried a different permutation, so the UI order is
        # now required to equal the FILE id for every source.
        for item in matrix_codec.SOURCES:
            self.assertEqual(item.ui_index, item.file_id, item.name)
        seen = sorted(x.ui_index for x in matrix_codec.SOURCES)
        self.assertEqual(seen, list(range(38)))

    def test_editor_source_selector_follows_the_registry(self):
        # app.py takes its dropdown from the codec, so there is one copy only.
        from app import MATRIX_SOURCES
        self.assertEqual(list(MATRIX_SOURCES),
                         list(matrix_codec.MATRIX_SOURCE_FILE_NAMES))
        self.assertEqual(len(MATRIX_SOURCES), 38)
        for item, label in zip(sorted(matrix_codec.SOURCES,
                                      key=lambda x: x.ui_index), MATRIX_SOURCES):
            self.assertEqual(item.name, label,
                             f"source 0x{item.file_id:02X}: "
                             f"registry {item.name!r} vs dropdown {label!r}")

    def test_every_selector_label_resolves_to_a_file_id(self):
        # This is the guard that catches a label the codec cannot look up. Four
        # sources used to fail here because the registry and the dropdown spelled
        # CV/Gate IN differently, which made those routes unwritable.
        for label in matrix_codec.MATRIX_SOURCE_FILE_NAMES:
            change = matrix_codec.ui_route_to_file_change(label, 'Osc 1 Level', 32, 0)
            self.assertIn('source_file_id', change, label)
        for label in matrix_codec.MATRIX_DESTINATION_FILE_NAMES:
            change = matrix_codec.ui_route_to_file_change('Velocity', label, 32, 0)
            self.assertIn('destination_file_id', change, label)

    def test_the_cv_and_gate_in_sources_are_writable(self):
        for file_id, label in ((0x17, "CV 1 IN"), (0x18, "GATE 1 IN"),
                               (0x19, "CV 2 IN"), (0x1A, "GATE 2 IN")):
            self.assertIn(label, matrix_codec.MATRIX_SOURCE_FILE_NAMES)
            change = matrix_codec.ui_route_to_file_change(label, 'Osc 1 Level', 32, 0)
            self.assertEqual(change['source_file_id'], file_id, label)
            self.assertEqual(matrix_codec.decode_source_file_id(file_id), label)


if __name__ == "__main__":
    unittest.main()
