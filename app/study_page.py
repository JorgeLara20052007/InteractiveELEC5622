"""The /study page: flashcards for one week, opened in its own window from the tree page.

It is a second, independent Dash app mounted on the same Flask server, so its component ids
and callbacks never clash with the tree page. It only reads the trees, never changes them.
"""

from __future__ import annotations

from pathlib import Path

from dash import Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate
from flask import Flask, redirect

from . import storage, study, tree, trees
from .styles import week_colour

SHOW = {"display": "block"}
HIDE = {"display": "none"}

_button = {
    "padding": "10px 18px",
    "fontSize": "16px",
    "borderRadius": "8px",
    "border": "1px solid #d0d7de",
    "cursor": "pointer",
    "background": "#f6f8fa",
}
_card = {
    "minHeight": "260px",
    "padding": "32px",
    "borderRadius": "16px",
    "background": "#ffffff",
    "boxShadow": "0 4px 16px rgba(0, 0, 0, 0.12)",
    "cursor": "pointer",
    "userSelect": "none",
    "borderTop": "10px solid #3a5a98",
}


def create(server: Flask, assets_folder: str | Path) -> Dash:
    app = Dash(
        __name__,
        server=server,
        url_base_pathname="/study/",
        title="Study · Course Tree",
        assets_folder=str(assets_folder),
    )
    app.layout = _layout  # a function, so the list of trees is fresh on every page load
    _register(app)
    server.add_url_rule("/study", "study_without_slash", lambda: redirect("/study/"))
    return app


def _layout() -> html.Div:
    return html.Div(
        style={
            "minHeight": "100vh",
            "background": "#f7f9fb",
            "color": "#1f2328",
            "fontFamily": "system-ui, Segoe UI, sans-serif",
            "padding": "24px 16px",
            "boxSizing": "border-box",
        },
        children=[
            # The tree the main window last showed (same browser storage key); only read here.
            dcc.Store(id="active-tree", storage_type="local"),
            dcc.Store(id="session"),
            html.Div(
                style={"maxWidth": "720px", "margin": "0 auto"},
                children=[
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"},
                        children=[
                            html.H1("Study", style={"margin": "0 0 16px"}),
                            html.A("← Back to the tree", href="/", style={"color": "#3a5a98"}),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "alignItems": "center"},
                        children=[
                            dcc.Dropdown(
                                id="study-tree",
                                options=trees.options(),
                                clearable=False,
                                placeholder="Tree",
                                style={"width": "200px"},
                            ),
                            dcc.Dropdown(
                                id="study-week",
                                clearable=False,
                                placeholder="Week",
                                style={"width": "300px"},
                            ),
                            dcc.Checklist(
                                id="study-all",
                                options=[{"label": " Include sub-concepts", "value": "all"}],
                                value=[],
                            ),
                            html.Button("Shuffle & restart", id="btn-restart", style={**_button, "fontSize": "14px"}),
                        ],
                    ),
                    html.Div(id="study-progress", style={"margin": "20px 0 10px", "color": "#57606a"}),
                    html.Div(
                        id="study-card",
                        n_clicks=0,
                        style=_card,
                        children=[
                            html.Div(id="card-week", style={"color": "#57606a", "fontSize": "13px"}),
                            html.H2(id="card-title", style={"fontSize": "32px", "margin": "40px 0 16px", "textAlign": "center"}),
                            html.Div(id="card-hint", style={"textAlign": "center", "color": "#8c959f"}),
                            dcc.Markdown(id="study-definition", mathjax=True, style={"fontSize": "17px"}),
                        ],
                    ),
                    html.Div(
                        id="answer-buttons",
                        style=HIDE,
                        children=[
                            html.Div(
                                style={"display": "flex", "gap": "12px", "justifyContent": "center", "marginTop": "18px"},
                                children=[
                                    html.Button(
                                        "✗ I didn't know it",
                                        id="btn-wrong",
                                        style={**_button, "background": "#ffebe9", "borderColor": "#cf222e"},
                                    ),
                                    html.Button(
                                        "✓ I knew it",
                                        id="btn-right",
                                        style={**_button, "background": "#dafbe1", "borderColor": "#1a7f37"},
                                    ),
                                ],
                            )
                        ],
                    ),
                    html.Div(
                        id="summary",
                        style=HIDE,
                        children=[
                            html.Div(
                                style={**_card, "cursor": "default", "textAlign": "center"},
                                children=[
                                    html.H2(id="summary-score", style={"fontSize": "40px", "margin": "16px 0 4px"}),
                                    html.Div(id="summary-text", style={"color": "#57606a"}),
                                    html.Ul(id="missed-list", style={"textAlign": "left", "margin": "20px auto", "maxWidth": "420px"}),
                                    html.Div(
                                        style={"display": "flex", "gap": "12px", "justifyContent": "center"},
                                        children=[
                                            html.Button(id="btn-retry", style=_button),
                                            html.Button("Start again", id="btn-again", style=_button),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                    html.Div(
                        "Shortcuts: Space flips the card · → or Y = I knew it · ← or N = I didn't",
                        style={"marginTop": "24px", "fontSize": "12px", "color": "#8c959f", "textAlign": "center"},
                    ),
                ],
            ),
        ],
    )


def _register(app: Dash) -> None:
    @app.callback(Output("study-tree", "value"), Input("active-tree", "data"))
    def pick_tree(active):
        """Start on the tree the main window was showing."""
        return trees.resolve(active)

    @app.callback(
        Output("study-week", "options"),
        Output("study-week", "value"),
        Input("study-tree", "value"),
    )
    def list_weeks(slug):
        if not slug:
            raise PreventUpdate
        weeks = storage.load(trees.db_path(slug)).children
        options = [{"label": w.label, "value": w.id} for w in weeks]
        return options, (weeks[0].id if weeks else None)

    @app.callback(
        Output("session", "data"),
        Input("study-week", "value"),
        Input("study-all", "value"),
        Input("btn-restart", "n_clicks"),
        Input("btn-again", "n_clicks"),
        Input("btn-retry", "n_clicks"),
        Input("study-card", "n_clicks"),
        Input("btn-right", "n_clicks"),
        Input("btn-wrong", "n_clicks"),
        State("study-tree", "value"),
        State("session", "data"),
        prevent_initial_call=True,
    )
    def update_session(week_id, include, _restart, _again, _retry, _card, _right, _wrong, slug, session):
        trigger = ctx.triggered_id
        if trigger == "study-card" and session:
            return study.flip(session)
        if trigger in ("btn-right", "btn-wrong") and session:
            return study.answer(session, knew_it=trigger == "btn-right")

        # Anything else (new week, new tree, the checkbox, restart, retry) deals a new deck.
        if not slug or not week_id:
            return None
        root = storage.load(trees.db_path(slug))
        week = next((w for w in root.children if w.id == week_id), None)
        if week is None:
            return None
        only = study.missed(session) if trigger == "btn-retry" and session else None
        return study.start(slug, week, include_all="all" in (include or []), only=only)

    @app.callback(
        Output("study-progress", "children"),
        Output("study-card", "style"),
        Output("card-week", "children"),
        Output("card-title", "children"),
        Output("card-hint", "children"),
        Output("study-definition", "children"),
        Output("study-definition", "style"),
        Output("answer-buttons", "style"),
        Output("summary", "style"),
        Output("summary-score", "children"),
        Output("summary-text", "children"),
        Output("missed-list", "children"),
        Output("btn-retry", "children"),
        Output("btn-retry", "style"),
        Input("session", "data"),
    )
    def render(session):
        if not session:
            return (
                "Pick a week to start.", {**_card, "cursor": "default"}, "", "No week selected",
                "", "", HIDE, HIDE, HIDE, "", "", [], "", HIDE,
            )
        root = storage.load(trees.db_path(session["tree"]))
        week_index = next((i for i, w in enumerate(root.children) if w.id == session["week"]), 0)
        week = root.children[week_index] if root.children else root
        card_style = {**_card, "borderTop": f"10px solid {week_colour(week_index, 1)}"}
        total = len(session["cards"])
        right, answered = study.score(session)

        if total == 0:
            return (
                "", {**card_style, "cursor": "default"}, week.label, "This week has no flashcards yet",
                "Add children to it in the tree, or include some of its nodes in flashcards.", "", HIDE, HIDE, HIDE, "", "", [], "", HIDE,
            )

        if study.finished(session):
            missed = study.missed(session)
            labels = {n.id: n.label for n in tree.walk(week)}
            percent = round(100 * right / answered) if answered else 0
            return (
                "",
                HIDE,
                "",
                "",
                "",
                "",
                HIDE,
                HIDE,
                SHOW,
                f"{right} / {answered}",
                f"correct in {week.label} ({percent}%)"
                + (" · all of them, well done!" if right == answered else ""),
                [html.Li(labels.get(i, "(deleted concept)")) for i in missed],
                f"Retry the {len(missed)} I missed",
                _button if missed else HIDE,
            )

        node_id = study.current(session)
        node = tree.find(week, node_id)
        title = node.label if node else "(this concept was deleted from the tree)"
        definition = (node.definition if node else "") or "*No definition yet.*"
        revealed = session["revealed"]
        return (
            f"Card {session['pos'] + 1} of {total} · {right} correct so far",
            card_style,
            week.label,
            title,
            "" if revealed else "Click the card to see the definition",
            definition if revealed else "",
            {"fontSize": "17px", "borderTop": "1px solid #d0d7de", "paddingTop": "12px"} if revealed else HIDE,
            SHOW if revealed else HIDE,
            HIDE,
            "",
            "",
            [],
            "",
            HIDE,
        )
