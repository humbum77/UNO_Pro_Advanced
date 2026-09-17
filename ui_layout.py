"""Pure responsive-layout helpers for the canvas UI.

The drawing code still uses logical coordinates.  A viewport keeps the
historical 1600-pixel minimum composition intact, but exposes additional
logical width on wider screens instead of centring the UI between gutters.
"""

from dataclasses import dataclass


MIN_LOGICAL_WIDTH = 1600.0


@dataclass(frozen=True)
class Viewport:
    pixel_width: int
    pixel_height: int
    logical_width: float
    logical_height: float
    scale: float

    @classmethod
    def fit(cls, pixel_width, pixel_height, logical_height, min_width=MIN_LOGICAL_WIDTH):
        pw = max(1, int(pixel_width))
        ph = max(1, int(pixel_height))
        lh = max(1.0, float(logical_height))
        mw = max(1.0, float(min_width))
        scale = min(pw / mw, ph / lh)
        return cls(pw, ph, pw / scale, lh, scale)

    @property
    def extra_width(self):
        return max(0.0, self.logical_width - MIN_LOGICAL_WIDTH)


def three_columns(total_width, left=295.0, right=325.0, margin=10.0, gap=10.0):
    """Return fixed side rails and a flexible centre column."""
    total = max(MIN_LOGICAL_WIDTH, float(total_width))
    centre_x = margin + left + gap
    right_x = total - margin - right
    centre_width = max(1.0, right_x - gap - centre_x)
    return (margin, left), (centre_x, centre_width), (right_x, right)


def split_columns(total_width, fractions, margin=16.0, gap=14.0):
    """Split the available width into stable fractional columns."""
    total = max(1.0, float(total_width))
    weights = [max(0.0, float(value)) for value in fractions]
    weight_sum = sum(weights) or 1.0
    available = max(1.0, total - 2 * margin - gap * max(0, len(weights) - 1))
    widths = [available * value / weight_sum for value in weights]
    result = []
    x = margin
    for width in widths:
        result.append((x, width))
        x += width + gap
    return result
