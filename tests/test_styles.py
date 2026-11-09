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


def test_every_week_gets_a_colour_even_after_the_eighth():
    # Weeks 9+ used to fall back to grey because only 8 weeks had style rules.
    elements = [{"data": {"id": f"w{i}", "depth": 1, "branch": i}} for i in range(12)]
    styles.paint(elements, [None] * 12)
    assert all(e["data"]["color"].startswith("#") for e in elements)
    assert elements[8]["data"]["color"] == elements[0]["data"]["color"]  # automatic hues repeat


def test_a_chosen_week_colour_is_used_exactly_and_lightened_below():
    elements = [
        {"data": {"id": "w", "depth": 1, "branch": 0}},
        {"data": {"id": "c", "depth": 2, "branch": 0}},
        {"data": {"id": "w->c", "source": "w", "target": "c", "branch": 0}},
        {"data": {"id": "root", "depth": 0, "branch": -1}},
    ]
    styles.paint(elements, ["#E76F51"])
    week, child, edge, root = (e["data"] for e in elements)
    assert week["color"] == "#e76f51"
    assert _lightness(child["color"]) > _lightness(week["color"])
    assert edge["color"].startswith("#")
    assert "color" not in root  # the root keeps its own style


def test_text_is_dark_on_light_colours_and_white_on_dark_ones():
    assert styles.text_colour("#ffe066") == "#1f2328"
    assert styles.text_colour("#1f4e79") == "#ffffff"
