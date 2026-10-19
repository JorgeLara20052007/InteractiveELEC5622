"""Entry point: `python -m app.main`, then open http://127.0.0.1:8050."""

import dash_cytoscape as cyto
from dash import Dash

from . import callbacks, storage
from .layout import build_layout

cyto.load_extra_layouts()  # enables the 'dagre' top-down tree layout


def create_app() -> Dash:
    storage.init()
    app = Dash(__name__, title="ELEC5622 Tree")
    app.layout = build_layout()
    callbacks.register(app)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8050, debug=False)
