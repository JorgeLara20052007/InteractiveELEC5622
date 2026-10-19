"""Cytoscape stylesheet: colour by depth, highlight for the selected node, '+' ghost node."""

DEPTH_COLOURS = {0: "#1d3557", 1: "#3a5a98", 2: "#457b9d", 3: "#5a9bb5"}
DEEP_COLOUR = "#6b9e9a"

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
            "background-color": DEEP_COLOUR,
        },
    },
    *[
        {"selector": f"node[depth = {d}]", "style": {"background-color": c}}
        for d, c in DEPTH_COLOURS.items()
    ],
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
        "selector": "node.sel",
        "style": {"border-width": 4, "border-color": "#ffb703"},
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
