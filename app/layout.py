"""Page layout: tree on the left, detail / edit panel on the right."""

import dash_cytoscape as cyto
from dash import dcc, html

from .styles import STYLESHEET

PANEL_WIDTH = "clamp(300px, 35vw, 440px)"

_button = {"marginRight": "8px", "padding": "6px 12px", "cursor": "pointer"}
_field = {"width": "100%", "boxSizing": "border-box", "marginBottom": "10px", "fontSize": "14px"}


def build_layout() -> html.Div:
    return html.Div(
        style={
            "display": "flex",
            "height": "100vh",
            "fontFamily": "system-ui, Segoe UI, sans-serif",
            "background": "#ffffff",
            "color": "#1f2328",
        },
        children=[
            dcc.Store(id="fit-dummy"),
            dcc.Store(id="selected", data="elec5622"),
            dcc.Store(id="mode", data="view"),  # "view" | "add" | "edit"
            dcc.Store(id="version", data=0),  # bumped after every database write
            dcc.ConfirmDialog(id="confirm-delete"),
            html.Div(
                style={"flex": "1", "position": "relative", "background": "#f7f9fb"},
                children=[
                    cyto.Cytoscape(
                        id="cy",
                        elements=[],
                        stylesheet=STYLESHEET,
                        layout={"name": "dagre"},
                        minZoom=0.1,
                        maxZoom=3,
                        wheelSensitivity=0.3,
                        style={"width": "100%", "height": "100%"},
                    ),
                    html.Button(
                        "Fit to screen",
                        id="btn-fit",
                        style={"position": "absolute", "top": "12px", "left": "12px", **_button},
                    ),
                ],
            ),
            html.Div(
                style={
                    "width": PANEL_WIDTH,
                    "flexShrink": 0,
                    "padding": "16px",
                    "overflowY": "auto",
                    "borderLeft": "1px solid #d0d7de",
                    "boxSizing": "border-box",
                },
                children=[
                    html.Div(
                        id="view",
                        children=[
                            html.Div(id="breadcrumb", style={"color": "#57606a", "fontSize": "12px"}),
                            html.H2(id="title", style={"margin": "6px 0 12px"}),
                            dcc.Markdown(id="definition", mathjax=True),
                            html.Div(id="children-info", style={"color": "#57606a", "margin": "12px 0"}),
                            html.Button("+ Add child", id="btn-add", style=_button),
                            html.Button("Edit", id="btn-edit", style=_button),
                            html.Button("Delete", id="btn-delete", style=_button),
                        ],
                    ),
                    html.Div(
                        id="form",
                        children=[
                            html.H3(id="form-title", style={"marginTop": 0}),
                            html.Label("Label"),
                            dcc.Input(id="form-label", type="text", style=_field),
                            html.Label("Definition (Markdown and $math$ supported)"),
                            dcc.Textarea(id="form-definition", style={**_field, "height": "220px"}),
                            html.Button("Save", id="btn-save", style=_button),
                            html.Button("Cancel", id="btn-cancel", style=_button),
                        ],
                    ),
                    html.Div(id="status", style={"marginTop": "12px", "color": "#8a4b00"}),
                ],
            ),
        ],
    )
