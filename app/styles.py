"""Cytoscape stylesheet: colour per week, shade by depth, selection highlight, '+' ghost node."""

import colorsys

ROOT_COLOUR = "#1d3557"
WEEK_HUES = [210, 150, 25, 280, 350, 180, 320, 100]  # degrees; branch i uses hue i % 8
MAX_SHADED_DEPTH = 5  # depths beyond this reuse the lightest shade


def week_colour(branch: int, depth: int) -> str:
    """Same hue for a whole week; each level down gets a little lighter."""
    hue = WEEK_HUES[branch % len(WEEK_HUES)] / 360
    lightness = 0.28 + 0.05 * (min(depth, MAX_SHADED_DEPTH) - 1)
    r, g, b = colorsys.hls_to_rgb(hue, lightness, 0.5)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def _week_rules() -> list[dict]:
    rules = []
    for branch in range(len(WEEK_HUES)):
        for depth in range(1, MAX_SHADED_DEPTH):
            rules.append(
                {
                    "selector": f"node[branch = {branch}][depth = {depth}]",
                    "style": {"background-color": week_colour(branch, depth)},
                }
            )
        rules.append(
            {
                "selector": f"node[branch = {branch}][depth >= {MAX_SHADED_DEPTH}]",
                "style": {"background-color": week_colour(branch, MAX_SHADED_DEPTH)},
            }
        )
    return rules


STYLESHEET = [
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "shape": "round-rectangle",
            "width": "label",
            "height": "label",
            "padding": "12px",
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": "170px",
            "font-size": "14px",
            "color": "#ffffff",
            "background-color": "#6b7280",
        },
    },
    {"selector": "node[depth = 0]", "style": {"background-color": ROOT_COLOUR}},
    *_week_rules(),
    {
        "selector": "edge",
        "style": {
            "curve-style": "taxi",
            "taxi-direction": "vertical",
            "line-color": "#9aa5b1",
            "width": 2,
        },
    },
    {
        # a collapsed node: double border, as a "there is more under here" hint
        "selector": "node[?collapsed]",
        "style": {"border-width": 5, "border-style": "double", "border-color": "#ffffff"},
    },
    {
        "selector": "node.sel",
        "style": {"border-width": 4, "border-style": "solid", "border-color": "#ffb703"},
    },
    {
        "selector": "node.add",
        "style": {
            "shape": "ellipse",
            "width": 30,
            "height": 30,
            "padding": "0px",
            "font-size": "22px",
            "font-weight": "bold",
            "color": "#1d3557",
            "background-color": "#ffd166",
            "border-width": 2,
            "border-style": "dashed",
            "border-color": "#1d3557",
        },
    },
    {
        "selector": "edge.add",
        "style": {"line-style": "dashed", "line-color": "#ffb703"},
    },
]
