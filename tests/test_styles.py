import colorsys

from app import styles


def _lightness(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)[1]


def test_each_week_gets_its_own_colour():
    colours = {styles.week_colour(branch, 1) for branch in range(len(styles.WEEK_HUES))}
    assert len(colours) == len(styles.WEEK_HUES)


def test_deeper_nodes_are_lighter_within_a_week():
    shades = [_lightness(styles.week_colour(0, d)) for d in range(1, styles.MAX_SHADED_DEPTH + 1)]
    assert shades == sorted(shades)
    assert styles.week_colour(0, 50) == styles.week_colour(0, styles.MAX_SHADED_DEPTH)


def test_branches_wrap_around_the_palette():
    assert styles.week_colour(len(styles.WEEK_HUES), 2) == styles.week_colour(0, 2)
