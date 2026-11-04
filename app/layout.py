"""Page layout: tree on the left, detail / edit panel on the right."""

import dash_cytoscape as cyto
from dash import dcc, html

from . import trees
from .styles import STYLESHEET

# The side panel can be resized by dragging the bar on its left edge (assets/app.js sets
# --panel-width and remembers it); this is the width until you do.
PANEL_WIDTH = "var(--panel-width, clamp(300px, 35vw, 440px))"

_button = {"marginRight": "8px", "padding": "6px 12px", "cursor": "pointer"}
_tool = {**_button, "marginRight": 0, "pointerEvents": "auto"}
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
            dcc.Store(id="focus-dummy"),
            dcc.Store(id="collapsed", data=[]),  # ids of nodes whose children are hidden
            dcc.Store(id="focus"),  # {"id": ..., "n": ...}: "zoom to this node" request
            dcc.Store(id="active-tree", storage_type="local"),  # slug of the tree being shown, remembered
            dcc.Store(id="selected", data=None),  # None = the root of the active tree
            dcc.Store(id="mode", data="view"),  # "view" | "add" | "edit"
            dcc.Store(id="version", data=0),  # bumped after every database write
            dcc.ConfirmDialog(id="confirm-delete"),
            html.Div(
                style={"flex": "1", "minWidth": 0, "overflow": "hidden", "position": "relative", "background": "#f7f9fb"},
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
                    html.Div(
                        style={
                            "position": "absolute",
                            "top": "12px",
                            "left": "12px",
                            "right": "12px",
                            "zIndex": 5,
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "8px",
                            "flexWrap": "wrap",
                            "pointerEvents": "none",  # let drags through the empty toolbar area
                        },
                        children=[
                            dcc.Dropdown(
                                id="tree-select",
                                options=trees.options(),
                                clearable=False,
                                style={"width": "200px", "pointerEvents": "auto", "color": "#1f2328"},
                            ),
                            html.Button("+ New tree", id="btn-new-tree", style=_tool),
                            html.A(
                                html.Button("📚 Study", style=_tool),
                                href="/study/",
                                target="_blank",  # flashcards open in their own window/tab
                                title="Flashcards: test yourself on one week",
                                style={"pointerEvents": "auto"},
                            ),
                            # Handled in assets/pdf.js: opens PDFs from this computer in floating windows.
                            html.Button(
                                "📄 PDF",
                                id="btn-pdf",
                                title="Open a PDF from your computer in a floating window",
                                style=_tool,
                            ),
                            html.Button("↶ Undo", id="btn-undo", disabled=True, style=_tool),
                            html.Button("↷ Redo", id="btn-redo", disabled=True, style=_tool),
                            html.Button("Fit to screen", id="btn-fit", style=_tool),
                            html.Button("Collapse all", id="btn-collapse-all", style=_tool),
                            html.Button("Expand all", id="btn-expand-all", style=_tool),
                            dcc.Dropdown(
                                id="search",
                                options=[],
                                placeholder="Search nodes…",
                                style={"width": "280px", "pointerEvents": "auto", "color": "#1f2328"},
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="splitter",
                title="Drag to resize the panel · double-click to reset",
            ),
            html.Div(
                id="side-panel",
                style={
                    "width": PANEL_WIDTH,
                    "flexShrink": 0,
                    "padding": "16px",
                    "overflowY": "auto",
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
                            html.Button("Collapse", id="btn-toggle", style=_button),
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
                            html.Label("Definition (Markdown, $math$ and images supported)"),
                            dcc.Textarea(
                                id="form-definition",
                                style={**_field, "height": "260px", "resize": "vertical", "fontFamily": "Consolas, monospace"},
                            ),
                            dcc.Upload(
                                id="image-upload",
                                accept="image/png,image/jpeg,image/gif,image/webp",
                                children=html.Div(
                                    "🖼 Add an image: drop a file here or click. "
                                    "You can also paste a screenshot into the box above."
                                ),
                                style={
                                    "border": "1px dashed #8c959f",
                                    "borderRadius": "6px",
                                    "padding": "10px",
                                    "textAlign": "center",
                                    "fontSize": "13px",
                                    "cursor": "pointer",
                                    "marginBottom": "12px",
                                },
                            ),
                            html.Button("Save", id="btn-save", style=_button),
                            html.Button("Cancel", id="btn-cancel", style=_button),
                            html.Div("Preview", style={"margin": "16px 0 4px", "color": "#57606a", "fontSize": "12px"}),
                            dcc.Markdown(id="form-preview", mathjax=True, style={"borderTop": "1px solid #d0d7de"}),
                        ],
                    ),
                    html.Div(
                        id="new-tree",
                        style={"display": "none"},
                        children=[
                            html.H3("New tree", style={"marginTop": 0}),
                            html.P(
                                "Start a completely separate tree, for another course or any other "
                                "subject. It gets its own database and its own JSON file in data/trees/.",
                                style={"color": "#57606a", "fontSize": "13px"},
                            ),
                            html.Label("Name (becomes the root node)"),
                            dcc.Input(
                                id="new-tree-name",
                                type="text",
                                placeholder="e.g. ELEC5xxx Signal Processing",
                                style=_field,
                            ),
                            html.Button("Create", id="btn-create-tree", style=_button),
                            html.Button("Cancel", id="btn-cancel-tree", style=_button),
                        ],
                    ),
                    html.Div(id="status", style={"marginTop": "12px", "color": "#8a4b00"}),
                ],
            ),
        ],
    )
