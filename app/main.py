"""Entry point: `python -m app.main`, then open http://127.0.0.1:8050."""

from pathlib import Path

import dash_cytoscape as cyto
from dash import Dash

from . import callbacks, images, storage
from .layout import build_layout

cyto.load_extra_layouts()  # enables the 'dagre' top-down tree layout

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"  # keyboard shortcuts, paste, CSS


def create_app() -> Dash:
    storage.init()
    app = Dash(__name__, title="ELEC5622 Tree", assets_folder=str(ASSETS_DIR))
    app.layout = build_layout()
    callbacks.register(app)
    images.register_routes(app.server)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8050, debug=False)
