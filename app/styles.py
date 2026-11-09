"""Cytoscape stylesheet and node colours.

Every node gets its colour as data (`color`, `textcolor`; edges `color`) worked out from its
week: the colour you picked for that week, or an automatic one. Deeper levels are lighter.
"""

from __future__ import annotations

import colorsys
import re

ROOT_COLOUR = "#1d3557"
WEEK_HUES = [210, 150, 25, 280, 350, 180, 320, 100]  # automatic colours: week i uses hue i % 8
MAX_SHADED_DEPTH = 5  # depths beyond this reuse the lightest shade
HEX_COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")

# The swatches offered in the side panel for a week's colour.
PALETTE = [
    "#1f4e79", "#2e86ab", "#4361ee", "#3d405b",
    "#0f766e", "#2a9d8f", "#3a7d44", "#6a994e",
    "#b08900", "#e76f51", "#c2410c", "#b91c1c",
    "#be185d", "#7b2cbf", "#5a189a", "#6b7280",
]


def _hex(r: float, g: float, b: float) -> str:
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def _hls(hex_colour: str) -> tuple[float, float, float]:
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def node_colour(branch: int, depth: int, base: str | None = None) -> str:
    """Colour of a node `depth` levels down in week number `branch` (0-based).

    `base` is the colour chosen for the week, if any: the week node gets exactly that colour
    and each level below gets a little lighter. Without one, an automatic hue is used.
    """
    steps = min(depth, MAX_SHADED_DEPTH) - 1
    if base:
        h, l, s = _hls(base)
        if steps == 0:
            return base.lower()
        return _hex(*colorsys.hls_to_rgb(h, min(l + 0.06 * steps, 0.85), s))
    hue = WEEK_HUES[branch % len(WEEK_HUES)] / 360
    return _hex(*colorsys.hls_to_rgb(hue, 0.28 + 0.05 * steps, 0.5))


def week_colour(branch: int, depth: int) -> str:
    """The automatic colour (no week colour chosen)."""
    return node_colour(branch, depth)


def edge_colour(branch: int, base: str | None = None) -> str:
    """A softer version of the week's colour, so lines sit behind the nodes."""
    if base:
        h, _, s = _hls(base)
        return _hex(*colorsys.hls_to_rgb(h, 0.65, min(s, 0.45)))
    hue = WEEK_HUES[branch % len(WEEK_HUES)] / 360
    return _hex(*colorsys.hls_to_rgb(hue, 0.62, 0.4))


def text_colour(background: str) -> str:
    """Dark text on light backgrounds, white text on dark ones."""
    r, g, b = (int(background[i : i + 2], 16) / 255 for i in (1, 3, 5))
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#1f2328" if luminance > 0.6 else "#ffffff"


def paint(elements: list[dict], week_colours: list[str | None]) -> list[dict]:
    """Add colour data to Cytoscape elements. `week_colours[i]` is week i's chosen colour or None."""
    for el in elements:
        data = el["data"]
        branch = data.get("branch")
        if branch is None or branch < 0:
            continue  # the root and the '+' node have their own style
        base = week_colours[branch] if branch < len(week_colours) else None
        if "source" in data:
            data["color"] = edge_colour(branch, base)
        else:
            data["color"] = node_colour(branch, data["depth"], base)
            data["textcolor"] = text_colour(data["color"])
    return elements


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
    {"selector": "node[color]", "style": {"background-color": "data(color)", "color": "data(textcolor)"}},
    {
        # Right-angle connectors: down from the parent, across at the halfway height, down into
        # the child, so siblings share one "bus" line instead of criss-crossing.
        "selector": "edge",
        "style": {
            "curve-style": "taxi",
            "taxi-direction": "downward",
            "taxi-turn": "32px",  # fixed distance, so every sibling's horizontal line is at one height
            "taxi-turn-min-distance": 10,
            "source-endpoint": "outside-to-node",
            "target-endpoint": "outside-to-node",
            "line-color": "#aab4bf",
            "line-cap": "round",
            "width": 2.5,
            "opacity": 0.9,
            "z-index": 0,
        },
    },
    {"selector": "edge[color]", "style": {"line-color": "data(color)"}},
    {
        # a collapsed node: double border, as a "there is more under here" hint
        "selector": "node[?collapsed]",
        "style": {"border-width": 5, "border-style": "double", "border-color": "#ffffff"},
    },
    {
        # left out of study mode: faded, with a dotted outline
        "selector": "node[?noflash]",
        "style": {"background-opacity": 0.35, "color": "#1f2328", "border-width": 2, "border-style": "dotted", "border-color": "#57606a"},
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
