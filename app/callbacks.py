"""Dash callbacks. Two main ones: `handle_event` changes state, `render` draws it."""

from dash import Input, Output, State, ctx

from . import storage, tree

ADD_ID = "__add__"  # id of the '+' ghost node shown next to the selected node
SHOW = {"display": "block"}
HIDE = {"display": "none"}


def _elements(root: tree.Node, selected: str) -> list[dict]:
    elements = tree.to_elements(root)
    for el in elements:
        # An explicit class on every element: Cytoscape keeps stale classes on elements
        # that come back without any, which would leave old nodes highlighted.
        el["classes"] = "sel" if el["data"].get("id") == selected else "plain"
    if tree.find(root, selected) is not None:
        elements.append({"data": {"id": ADD_ID, "label": "+", "depth": -1}, "classes": "add"})
        elements.append(
            {
                "data": {"id": f"{selected}->{ADD_ID}", "source": selected, "target": ADD_ID},
                "classes": "add",
            }
        )
    return elements


def register(app) -> None:
    @app.callback(
        Output("selected", "data"),
        Output("mode", "data"),
        Output("version", "data"),
        Output("status", "children"),
        Input("cy", "tapNode"),
        Input("btn-add", "n_clicks"),
        Input("btn-edit", "n_clicks"),
        Input("btn-cancel", "n_clicks"),
        Input("btn-save", "n_clicks"),
        Input("confirm-delete", "submit_n_clicks"),
        State("selected", "data"),
        State("mode", "data"),
        State("version", "data"),
        State("form-label", "value"),
        State("form-definition", "value"),
        prevent_initial_call=True,
    )
    def handle_event(tap, _add, _edit, _cancel, _save, _confirm, selected, mode, version, label, definition):
        trigger, status = ctx.triggered_id, ""

        if trigger == "cy":
            node_id = tap["data"]["id"]
            if node_id == ADD_ID:
                mode = "add"
            else:
                selected, mode = node_id, "view"
        elif trigger == "btn-add":
            mode = "add"
        elif trigger == "btn-edit":
            mode = "edit"
        elif trigger == "btn-cancel":
            mode = "view"
        elif trigger == "btn-save":
            label, definition = (label or "").strip(), definition or ""
            if not label:
                return selected, mode, version, "The label cannot be empty."
            try:
                if mode == "add":
                    selected = storage.add_node(selected, label, definition).id
                else:
                    storage.update_node(selected, label, definition)
            except (KeyError, ValueError) as err:
                return selected, mode, version, f"Could not save: {err}"
            mode, version = "view", version + 1
        elif trigger == "confirm-delete":
            root = storage.load()
            path = tree.find_path(root, selected)
            try:
                removed = storage.delete_node(selected)
            except (KeyError, ValueError) as err:
                return selected, mode, version, f"Could not delete: {err}"
            selected, mode, version = path[-2].id, "view", version + 1
            status = f"Deleted {removed} node(s)."
        return selected, mode, version, status

    # dash-cytoscape resets zoom/pan to its own props after a layout, so fit the camera
    # directly on the Cytoscape instance: once when the first elements arrive, then on the button.
    app.clientside_callback(
        """
        function(clicks, elements) {
            const trigger = dash_clientside.callback_context.triggered_id;
            const first = trigger === 'cy' && !window.__treeFitted && elements && elements.length;
            if (trigger === 'btn-fit' || first) {
                window.__treeFitted = true;
                setTimeout(() => {
                    const el = document.getElementById('cy');
                    if (el && el._cyreg && el._cyreg.cy) el._cyreg.cy.fit(undefined, 40);
                }, 150);
            }
            return dash_clientside.no_update;
        }
        """,
        Output("fit-dummy", "data"),
        Input("btn-fit", "n_clicks"),
        Input("cy", "elements"),
    )

    @app.callback(Output("confirm-delete", "displayed"), Input("btn-delete", "n_clicks"), prevent_initial_call=True)
    def ask_to_delete(_clicks):
        return True

    @app.callback(
        Output("cy", "elements"),
        Output("cy", "layout"),
        Output("breadcrumb", "children"),
        Output("title", "children"),
        Output("definition", "children"),
        Output("children-info", "children"),
        Output("btn-delete", "disabled"),
        Output("confirm-delete", "message"),
        Output("view", "style"),
        Output("form", "style"),
        Output("form-title", "children"),
        Output("form-label", "value"),
        Output("form-definition", "value"),
        Input("selected", "data"),
        Input("mode", "data"),
        Input("version", "data"),
    )
    def render(selected, mode, _version):
        root = storage.load()
        path = tree.find_path(root, selected) or [root]
        node = path[-1]
        n_children = len(node.children)
        n_desc = tree.count_descendants(node)

        # fit is False so zoom/pan survive clicks; the camera is fitted by the clientside
        # callback below, on first load and on the Fit button.
        layout = {
            "name": "dagre",
            "rankDir": "TB",
            "nodeSep": 30,
            "rankSep": 70,
            "padding": 40,
            "animate": False,
            "fit": False,
        }

        editing = mode in ("add", "edit")
        if mode == "add":
            form_title, label, definition = f"Add child to “{node.label}”", "", ""
        elif mode == "edit":
            form_title, label, definition = f"Edit “{node.label}”", node.label, node.definition
        else:
            form_title, label, definition = "", "", ""

        return (
            _elements(root, node.id),
            layout,
            " › ".join(n.label for n in path),
            node.label,
            node.definition or "*No definition yet. Press Edit to add one.*",
            f"{n_children} child node(s)" if n_children else "No children yet.",
            node is root,
            f"Delete “{node.label}”"
            + (f" and its {n_desc} descendant(s)" if n_desc else "")
            + "? This cannot be undone.",
            HIDE if editing else SHOW,
            SHOW if editing else HIDE,
            form_title,
            label,
            definition,
        )
