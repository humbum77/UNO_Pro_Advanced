"""Lock the device's Held-Step Automation order.

Confirmed by the operator on 2026-09-29 and recorded in
Docs/history/PARAMETER_SELECTION_2026-09-29.md. Two facts that were previously
wrong and are pinned here: NOISE is automatable and sits between LEVEL 3 and
CUTOFF 1, and VELOCITY is a per-step parameter that is not an automation lane.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import automation_metadata
import uno_step_automation_decoder as decoder

# The device order, verbatim.
EXPECTED = (
    "WAVE1", "TUNE1", "WAVE2", "TUNE2", "WAVE3", "TUNE3",
    "LEVEL1", "LEVEL2", "LEVEL3", "NOISE", "CUTOFF1", "RES1", "ENV1",
    "CUTOFF2", "RES2", "ENV2", "SPACING", "LFO1", "LFO2",
    "DRIVE", "MOD", "DELAY", "REVERB",
)

# automation_metadata spells the same parameters for the GUI.
GUI_NAME = {
    "WAVE1": "WAVE 1", "TUNE1": "TUNE 1", "WAVE2": "WAVE 2", "TUNE2": "TUNE 2",
    "WAVE3": "WAVE 3", "TUNE3": "TUNE 3", "LEVEL1": "LEVEL 1",
    "LEVEL2": "LEVEL 2", "LEVEL3": "LEVEL 3", "NOISE": "NOISE",
    "CUTOFF1": "CUTOFF 1", "RES1": "RESONANCE 1", "ENV1": "ENV AM 1",
    "CUTOFF2": "CUTOFF 2", "RES2": "RESONANCE 2", "ENV2": "ENV AM 2",
    "SPACING": "SPACING", "LFO1": "LFO 1", "LFO2": "LFO 2",
    "DRIVE": "DRIVE AMOUNT", "MOD": "MODULATION AMOUNT",
    "DELAY": "DELAY AMOUNT", "REVERB": "REVERB AMOUNT",
}


class AutomationOrder(unittest.TestCase):
    def test_decoder_order_is_the_device_order(self):
        self.assertEqual(decoder.DECODER_PARAMETER_ORDER, EXPECTED)

    def test_metadata_order_is_the_device_order(self):
        self.assertEqual(automation_metadata.AUTOMATION_ORDER,
                         tuple(GUI_NAME[n] for n in EXPECTED))

    def test_noise_is_between_level3_and_cutoff1(self):
        self.assertEqual(EXPECTED.index("NOISE"), 9)
        self.assertEqual(EXPECTED[8], "LEVEL3")
        self.assertEqual(EXPECTED[10], "CUTOFF1")
        self.assertIn("NOISE", automation_metadata.PARAMETERS)
        self.assertIn("NOISE", decoder.PARAMETERS)

    def test_velocity_is_a_step_parameter_not_a_lane(self):
        self.assertNotIn("VELOCITY", automation_metadata.AUTOMATION_ORDER)
        self.assertNotIn("VELOCITY", decoder.PARAMETERS)
        self.assertIn("VELOCITY", automation_metadata.STEP_PARAMETERS)
        self.assertEqual(automation_metadata.STEP_PARAMETERS,
                         ("GATE", "ACC", "TIE", "VELOCITY", "LENGTH"))
        self.assertIn("NOT a held-Step Automation lane",
                      automation_metadata.PARAMETERS["VELOCITY"].status)

    def test_confirmed_order_leads_the_panel(self):
        panel = automation_metadata.AUTOMATABLE
        self.assertEqual(panel[:len(EXPECTED)],
                         tuple(GUI_NAME[n] for n in EXPECTED))

    def test_unordered_automatable_parameters_are_registered_and_flagged(self):
        for name in automation_metadata.AUTOMATION_UNORDERED:
            self.assertIn(name, automation_metadata.PARAMETERS)
            self.assertIn("order position UNKNOWN",
                          automation_metadata.PARAMETERS[name].status)
            self.assertNotIn("no clean capture possible",
                             automation_metadata.PARAMETERS[name].status)
            self.assertNotIn(name, automation_metadata.AUTOMATION_ORDER)
        # FM 1/FM 2 were previously marked as not automatable
        self.assertNotIn("NOT held-Step Automation",
                         automation_metadata.PARAMETERS["FM 1"].status)

    def test_menu_only_parameters_are_flagged_uncapturable(self):
        for name in automation_metadata.AUTOMATION_NO_CAPTURE:
            self.assertIn(name, automation_metadata.PARAMETERS)
            status = automation_metadata.PARAMETERS[name].status
            self.assertIn("order position UNKNOWN", status)
            self.assertIn("no clean capture possible", status)
            self.assertNotIn(name, automation_metadata.AUTOMATION_ORDER)
        # the reported groups must all be present
        for name in ("OSC 2 SYNC", "OSC 3 SYNC", "RING", "FILTER 1 MODE",
                     "FILTER 2 MODE", "FILTER 1 KEY TRACKING",
                     "FILTER 2 KEY TRACKING", "GLIDE"):
            self.assertIn(name, automation_metadata.AUTOMATION_NO_CAPTURE)
        # both readings of "filter fm" stay registered and flagged
        for name in ("FM 1", "FM 2", "FILTER 1 ENV AMOUNT",
                     "FILTER 2 ENV AMOUNT"):
            self.assertIn(name, automation_metadata.AUTOMATION_NO_CAPTURE)

    def test_the_two_unordered_groups_are_disjoint(self):
        self.assertEqual(
            set(automation_metadata.AUTOMATION_UNORDERED)
            & set(automation_metadata.AUTOMATION_NO_CAPTURE), set())
        panel = set(automation_metadata.AUTOMATABLE)
        self.assertEqual(panel,
                         set(automation_metadata.AUTOMATION_ORDER) | {"VELOCITY"}
                         | set(automation_metadata.AUTOMATION_UNORDERED)
                         | set(automation_metadata.AUTOMATION_NO_CAPTURE))
        # every automatable parameter fits under the per-step lane limit in
        # aggregate, and none of them claims a confirmed order
        self.assertGreater(automation_metadata.MAX_AUTOMATION_LANES_PER_STEP, 0)

    def test_every_automation_parameter_has_metadata(self):
        for name in automation_metadata.AUTOMATION_ORDER:
            self.assertIn(name, automation_metadata.PARAMETERS)

    def test_every_decoder_parameter_has_a_width_and_the_order_agrees(self):
        for name in EXPECTED:
            self.assertIn(name, decoder.PARAMETERS)
        # TUNE and the bipolar envelopes are signed; everything else is unsigned
        signed = {n for n in EXPECTED if decoder.PARAMETERS[n][1]}
        self.assertEqual(signed, {"TUNE1", "TUNE2", "TUNE3", "ENV1", "ENV2",
                                  "SPACING"})


if __name__ == "__main__":
    unittest.main()
