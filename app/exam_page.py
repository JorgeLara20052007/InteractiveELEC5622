"""The /exam/ page: practice exam questions with solutions, grouped in sections (weeks).

Like the study page, it is a separate Dash app on the same Flask server. Sections open and
close with a click; each question shows its solution behind "Show solution". Questions are
added and edited in the editor on the right, with a live Markdown preview.
"""

from __future__ import annotations

from pathlib import Path

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from flask import Flask, redirect

from . import exam, trees

SHOW = {"display": "block"}
HIDE = {"display": "none"}

_button = {
    "padding": "6px 12px",
    "marginRight": "8px",
    "borderRadius": "6px",
    "border": "1px solid #d0d7de",
    "background": "#f6f8fa",
    "cursor": "pointer",
}
_small = {**_button, "padding": "3px 10px", "fontSize": "13px"}
_field = {
    "width": "100%",
    "boxSizing": "border-box",
    "fontFamily": "Consolas, monospace",
    "fontSize": "14px",
    "resize": "vertical",
    "marginBottom": "10px",
}
_card = {
    "background": "#ffffff",
    "border": "1px solid #d0d7de",
    "borderRadius": "10px",
    "marginBottom": "10px",
    "overflow": "hidden",
}


def create(server: Flask, assets_folder: str | Path) -> Dash:
    app = Dash(
        __name__,
        server=server,
        url_base_pathname="/exam/",
        title="Practice exam · Course Tree",
        assets_folder=str(assets_folder),
    )
    app.layout = _layout
    _register(app)
    server.add_url_rule("/exam", "exam_without_slash", lambda: redirect("/exam/"))
    return app


def _layout() -> html.Div:
    return html.Div(
        style={
            "minHeight": "100vh",
            "background": "#f7f9fb",
            "color": "#1f2328",
            "fontFamily": "system-ui, Segoe UI, sans-serif",
            "padding": "20px 16px",
            "boxSizing": "border-box",
        },
        children=[
            dcc.Store(id="active-tree", storage_type="local"),  # tree last shown in the main window
            dcc.Store(id="exam-open", data=[]),  # ids of the open sections
            dcc.Store(id="exam-edit"),  # None, or what the editor is doing
            dcc.Store(id="exam-version", data=0),  # bumped after every change
            dcc.Store(id="exam-pending-delete"),
            dcc.ConfirmDialog(id="exam-confirm-delete"),
            html.Div(
                style={"maxWidth": "1200px", "margin": "0 auto"},
                children=[
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline", "flexWrap": "wrap"},
                        children=[
                            html.H1("Practice exam questions", style={"margin": "0 0 12px"}),
                            html.A("← Back to the tree", href="/", style={"color": "#3a5a98"}),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "16px"},
                        children=[
                            dcc.Dropdown(id="exam-tree", options=trees.options(), clearable=False, style={"width": "220px"}),
                            html.Button("Open all", id="btn-open-all", style=_button),
                            html.Button("Close all", id="btn-close-all", style=_button),
                            html.Div(id="exam-status", style={"color": "#8a4b00"}),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "20px", "alignItems": "flex-start", "flexWrap": "wrap"},
                        children=[
                            html.Div(id="exam-sections", style={"flex": "1 1 480px", "minWidth": 0}),
                            _editor(),
                        ],
                    ),
                ],
            ),
        ],
    )


def _editor() -> html.Div:
    """Shown while adding or editing a question; stays in view while the page scrolls."""
    return html.Div(
        id="exam-editor",
        style=HIDE,
        children=[
            html.H3(id="exam-editor-title", style={"marginTop": 0}),
            html.Label("Question (Markdown, $math$, paste pictures)"),
            dcc.Textarea(id="exam-question", className="paste-images", style={**_field, "height": "150px"}),
            html.Label("Solution"),
            dcc.Textarea(id="exam-solution", className="paste-images", style={**_field, "height": "190px"}),
            html.Div(
                [
                    html.Button("Save", id="btn-exam-save", style=_button),
                    html.Button("Cancel", id="btn-exam-cancel", style=_button),
                ]
            ),
            html.Div("Preview", style={"margin": "14px 0 4px", "color": "#57606a", "fontSize": "12px"}),
            html.Div(
                style={"border": "1px solid #d0d7de", "borderRadius": "6px", "padding": "0 12px", "background": "#fbfcfd"},
                children=[
                    dcc.Markdown(id="exam-question-preview", mathjax=True),
                    html.Div("Solution", style={"color": "#57606a", "fontSize": "12px", "borderTop": "1px dashed #d0d7de", "paddingTop": "6px"}),
                    dcc.Markdown(id="exam-solution-preview", mathjax=True),
                ],
            ),
        ],
    )


_EDITOR_SHOWN = {
    "display": "block",
    "flex": "0 1 460px",
    "minWidth": "300px",
    "position": "sticky",
    "top": "16px",
    "maxHeight": "calc(100vh - 32px)",
    "overflowY": "auto",
    "background": "#ffffff",
    "border": "1px solid #d0d7de",
    "borderRadius": "10px",
    "padding": "16px",
    "boxSizing": "border-box",
}


def _section_card(section: dict, is_open: bool) -> html.Div:
    n = len(section["questions"])
    header = html.Button(
        [
            html.Span(("▾ " if is_open else "▸ ") + section["label"], style={"fontWeight": 600}),
            html.Span(f"{n} question{'s' if n != 1 else ''}", style={"color": "#57606a", "fontSize": "13px"}),
        ],
        id={"type": "sec-toggle", "id": section["id"]},
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "width": "100%",
            "padding": "12px 16px",
            "border": "none",
            "background": "#eef2f7" if is_open else "#ffffff",
            "fontSize": "16px",
            "cursor": "pointer",
            "textAlign": "left",
        },
    )
    if not is_open:
        return html.Div([header], style=_card)

    items = []
    for i, q in enumerate(section["questions"], start=1):
        items.append(
            html.Div(
                style={"borderTop": "1px solid #eaeef2", "padding": "10px 16px"},
                children=[
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                        children=[
                            html.Strong(f"Question {i}"),
                            html.Div(
                                [
                                    html.Button("Edit", id={"type": "q-edit", "id": q["id"]}, style=_small),
                                    html.Button("Delete", id={"type": "q-del", "id": q["id"]}, style={**_small, "marginRight": 0}),
                                ]
                            ),
                        ],
                    ),
                    dcc.Markdown(q["question"], mathjax=True, className="exam-md"),
                    html.Details(
                        [
                            html.Summary("Show solution", style={"cursor": "pointer", "color": "#3a5a98"}),
                            dcc.Markdown(q["solution"] or "*No solution written yet.*", mathjax=True, className="exam-md"),
                        ],
                        style={"background": "#f6f8fa", "borderRadius": "6px", "padding": "6px 10px"},
                    ),
                ],
            )
        )
    if not items:
        items.append(html.Div("No questions yet.", style={"padding": "8px 16px", "color": "#8c959f"}))
    items.append(
        html.Div(
            html.Button("+ Add question", id={"type": "q-add", "section": section["id"]}, style=_button),
            style={"padding": "10px 16px", "borderTop": "1px solid #eaeef2"},
        )
    )
    return html.Div([header, *items], style=_card)


def _register(app: Dash) -> None:
    @app.callback(Output("exam-tree", "value"), Input("active-tree", "data"))
    def pick_tree(active):
        return trees.resolve(active)

    @app.callback(
        Output("exam-open", "data"),
        Output("exam-edit", "data"),
        Output("exam-version", "data"),
        Output("exam-status", "children"),
        Output("exam-pending-delete", "data"),
        Output("exam-confirm-delete", "displayed"),
        Output("exam-confirm-delete", "message"),
        Output("exam-question", "value"),
        Output("exam-solution", "value"),
        Input({"type": "sec-toggle", "id": ALL}, "n_clicks"),
        Input({"type": "q-add", "section": ALL}, "n_clicks"),
        Input({"type": "q-edit", "id": ALL}, "n_clicks"),
        Input({"type": "q-del", "id": ALL}, "n_clicks"),
        Input("btn-exam-save", "n_clicks"),
        Input("btn-exam-cancel", "n_clicks"),
        Input("exam-confirm-delete", "submit_n_clicks"),
        Input("btn-open-all", "n_clicks"),
        Input("btn-close-all", "n_clicks"),
        Input("exam-tree", "value"),
        State("exam-open", "data"),
        State("exam-edit", "data"),
        State("exam-version", "data"),
        State("exam-pending-delete", "data"),
        State("exam-question", "value"),
        State("exam-solution", "value"),
        prevent_initial_call=True,
    )
    def handle_event(
        _toggle, _add, _edit, _delete, _save, _cancel, _confirm, _open_all, _close_all, slug,
        open_ids, editing, version, pending, question, solution,
    ):
        trigger = ctx.triggered_id
        if isinstance(trigger, dict) and not ctx.triggered[0]["value"]:
            raise PreventUpdate  # buttons appearing after a redraw, not a click
        if not slug:
            raise PreventUpdate
        db = trees.db_path(slug)
        open_ids = list(open_ids or [])
        status = ""
        out = {"pending": no_update, "confirm": no_update, "message": no_update, "q": no_update, "s": no_update}

        def result():
            return (
                open_ids, editing, version, status, out["pending"], out["confirm"], out["message"],
                out["q"], out["s"],
            )

        section_labels = {s["id"]: s["label"] for s in exam.sections(db)}

        if trigger == "exam-tree":
            open_ids, editing, version = [], None, version + 1
        elif isinstance(trigger, dict) and trigger["type"] == "sec-toggle":
            sid = trigger["id"]
            open_ids = [i for i in open_ids if i != sid] if sid in open_ids else [*open_ids, sid]
        elif trigger == "btn-open-all":
            open_ids = list(section_labels)
        elif trigger == "btn-close-all":
            open_ids = []
        elif isinstance(trigger, dict) and trigger["type"] == "q-add":
            sid = trigger["section"]
            editing = {"mode": "add", "section": sid, "label": section_labels.get(sid, "")}
            out["q"], out["s"] = "", ""
        elif isinstance(trigger, dict) and trigger["type"] == "q-edit":
            q = exam.get_question(db, trigger["id"])
            if q is None:
                raise PreventUpdate
            editing = {
                "mode": "edit",
                "question": q["id"],
                "section": q["section_id"],
                "label": section_labels.get(q["section_id"], ""),
            }
            out["q"], out["s"] = q["question"], q["solution"]
        elif isinstance(trigger, dict) and trigger["type"] == "q-del":
            q = exam.get_question(db, trigger["id"])
            if q is None:
                raise PreventUpdate
            preview = " ".join(q["question"].split())[:80]
            out["pending"], out["confirm"] = q["id"], True
            out["message"] = f"Delete this question from {section_labels.get(q['section_id'], 'this section')}?\n\n{preview}"
        elif trigger == "exam-confirm-delete":
            if pending is None:
                raise PreventUpdate
            try:
                exam.delete_question(db, pending)
            except KeyError:
                pass
            if editing and editing.get("question") == pending:
                editing = None
            out["pending"], version, status = None, version + 1, "Question deleted."
        elif trigger == "btn-exam-cancel":
            editing = None
        elif trigger == "btn-exam-save":
            if not editing:
                raise PreventUpdate
            try:
                if editing["mode"] == "add":
                    exam.add_question(db, editing["section"], question, solution)
                    status = f"Question added to {editing['label']}."
                else:
                    exam.update_question(db, editing["question"], question, solution)
                    status = "Question saved."
            except (KeyError, ValueError) as err:
                status = str(err).strip("'\"")
                return result()
            if editing["section"] not in open_ids:
                open_ids.append(editing["section"])
            editing, version = None, version + 1
            out["q"], out["s"] = "", ""
        return result()

    @app.callback(
        Output("exam-sections", "children"),
        Input("exam-version", "data"),
        Input("exam-open", "data"),
        Input("exam-tree", "value"),
    )
    def render_sections(_version, open_ids, slug):
        if not slug:
            raise PreventUpdate
        open_ids = set(open_ids or [])
        return [_section_card(s, s["id"] in open_ids) for s in exam.sections(trees.db_path(slug))]

    @app.callback(
        Output("exam-editor", "style"),
        Output("exam-editor-title", "children"),
        Input("exam-edit", "data"),
    )
    def show_editor(editing):
        if not editing:
            return HIDE, ""
        verb = "New question" if editing["mode"] == "add" else "Edit question"
        return _EDITOR_SHOWN, f"{verb} · {editing['label']}"

    @app.callback(
        Output("exam-question-preview", "children"),
        Output("exam-solution-preview", "children"),
        Input("exam-question", "value"),
        Input("exam-solution", "value"),
    )
    def preview(question, solution):
        return question or "*The question will appear here.*", solution or "*The solution will appear here.*"
