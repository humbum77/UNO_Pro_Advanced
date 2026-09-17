import unittest

from ui_layout import Viewport, split_columns, three_columns


class ResponsiveViewportTests(unittest.TestCase):
    def test_standard_16_by_9_resolutions_use_full_width(self):
        for width, height in ((1366, 768), (1600, 900), (1920, 1080), (2560, 1440)):
            with self.subTest(size=(width, height)):
                viewport = Viewport.fit(width, height, 1000)
                self.assertAlmostEqual(viewport.logical_width * viewport.scale, width)
                self.assertAlmostEqual(viewport.logical_height * viewport.scale, height)
                self.assertGreater(viewport.logical_width, 1600)

    def test_minimum_composition_never_gets_narrower(self):
        viewport = Viewport.fit(1000, 640, 1000)
        self.assertEqual(viewport.logical_width, 1600)
        self.assertAlmostEqual(viewport.scale, 0.625)

    def test_sequencer_centre_absorbs_extra_width(self):
        _, centre_1600, right_1600 = three_columns(1600)
        _, centre_wide, right_wide = three_columns(1777.777777)
        self.assertGreater(centre_wide[1], centre_1600[1])
        self.assertGreater(right_wide[0], right_1600[0])
        self.assertEqual(right_wide[1], right_1600[1])

    def test_fractional_columns_fill_available_width(self):
        columns = split_columns(1777.777777, (3, 2), margin=24, gap=28)
        self.assertAlmostEqual(columns[-1][0] + columns[-1][1], 1777.777777 - 24)
        self.assertAlmostEqual(columns[0][1] / columns[1][1], 1.5)


if __name__ == '__main__':
    unittest.main()
