"""Dash callbacks. Two main ones: `handle_event` changes state, `render` draws it."""

import time

from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate

from . import storage, tree

ADD_ID = "__add__"  # id of the '+' ghost node shown next to the selected node
SHOW = {"display": "block"}
HIDE = {"display": "none"}


def _elements(root: tree.Node, selected: str, collapsed: set[str]) -> list[dict]:
    elements = tree.to_elements(root, collapsed)
    for el in elements:
        # An explicit class on every element: Cytoscape keeps stale classes on elements
        # that come back without any, which would leave old nodes highlighted.
        el["classes"] = "sel" if el["data"].get("id") == selected else "plain"
    if any(el["data"].get("id") == selected for el in elements):
        elements.append({"data": {"id": ADD_ID, "label": "+", "depth": -1}, "classes": "add"})
        elements.append(
            {
                "data": {"id": f"{selected}->{ADD_ID}", "source": selected, "target": ADD_ID},
                "classes": "add",
            }
        )
    return elements


def _search_options(root: tree.Node) -> list[dict]:
    """One entry per node (except the root): 'Label  ·  Week › Parent' so you can search by either."""
    options = []
    for path in tree.iter_paths(root):
        if len(path) == 1:
            continue
        context = " › ".join(n.label for n in path[1:-1])
        label = f"{path[-1].label}  ·  {context}" if context else path[-1].label
        options.append({"label": label, "value": path[-1].id})
    return options


def _visible_ancestor(root: tree.Node, node_id: str, collapsed: set[str]) -> str:
    """The node itself, or its highest collapsed ancestor if it is hidden inside one."""
    for ancestor in (tree.find_path(root, node_id) or [root])[:-1]:
        if ancestor.id in collapsed:
            return ancestor.id
    return node_id


def register(app) -> None:
    @app.callback(
        Output("selected", "data"),
        Output("mode", "data"),
        Output("version", "data"),
        Output("status", "children"),
        Output("collapsed", "data"),
        Output("focus", "data"),
        Output("search", "value"),
        Input("cy", "tapNode"),
        Input("btn-add", "n_clicks"),
        Input("btn-edit", "n_clicks"),
        Input("btn-cancel", "n_clicks"),
        Input("btn-save", "n_clicks"),
        Input("confirm-delete", "submit_n_clicks"),
        Input("btn-toggle", "n_clicks"),
        Input("btn-collapse-all", "n_clicks"),
        Input("btn-expand-all", "n_clicks"),
        Input("search", "value"),
        State("selected", "data"),
        State("mode", "data"),
        State("version", "data"),
        State("collapsed", "data"),
        State("form-label", "value"),
        State("form-definition", "value"),
        prevent_initial_call=True,
    )
    def handle_event(
        tap, _add, _edit, _cancel, _save, _confirm, _toggle, _collapse_all, _expand_all, search,
        selected, mode, version, collapsed, label, definition,
    ):
        trigger, status = ctx.triggered_id, ""
        collapsed, focus, search_value = set(collapsed or []), no_update, no_update

        def result():
            return selected, mode, version, status, sorted(collapsed), focus, search_value

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
                status = "The label cannot be empty."
                return result()
            try:
                if mode == "add":
                    collapsed.discard(selected)  # show the parent's children, including the new one
                    selected = storage.add_node(selected, label, definition).id
                else:
                    storage.update_node(selected, label, definition)
            except (KeyError, ValueError) as err:
                status = f"Could not save: {err}"
                return result()
            mode, version = "view", version + 1
        elif trigger == "confirm-delete":
            root = storage.load()
            path = tree.find_path(root, selected)
            try:
                removed = storage.delete_node(selected)
            except (KeyError, ValueError) as err:
                status = f"Could not delete: {err}"
                return result()
            collapsed.discard(selected)
            selected, mode, version = path[-2].id, "view", version + 1
            status = f"Deleted {removed} node(s)."
        elif trigger == "btn-toggle":
            collapsed ^= {selected}
        elif trigger == "btn-collapse-all":
            root = storage.load()
            collapsed = {n.id for n in tree.walk(root) if n.children and n is not root}
            selected = _visible_ancestor(root, selected, collapsed)
        elif trigger == "btn-expand-all":
            collapsed = set()
        elif trigger == "search":
            root = storage.load()
            path = tree.find_path(root, search) if search else None
            if path is None:
                raise PreventUpdate
            collapsed -= {n.id for n in path[:-1]}  # open every ancestor so the node is visible
            selected, mode = search, "view"
            focus = {"id": search, "n": time.time()}
            search_value = None  # clear the box so the same result can be picked again
        return result()

    # dash-cytoscape resets zoom/pan to its own props after a layout, so move the camera
    # directly on the Cytoscape instance: fit once when the first elements arrive, then on the button.
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

    # Zoom to the node picked in the search box. The node may only exist (and be laid out)
    # once the server has re-rendered, so remember the request and act when new elements
    # arrive; the longer timer on the request itself covers the case where nothing re-renders.
    app.clientside_callback(
        """
        function(focus, elements) {
            const trigger = dash_clientside.callback_context.triggered_id;
            if (trigger === 'focus' && focus) window.__pendingFocus = focus.id;
            const tryFocus = () => {
                const id = window.__pendingFocus;
                const el = document.getElementById('cy');
                const cy = el && el._cyreg && el._cyreg.cy;
                if (!id || !cy) return;
                const node = cy.getElementById(id);
                if (!node.length) return;
                window.__pendingFocus = null;
                cy.animate({center: {eles: node}, zoom: Math.max(cy.zoom(), 1)}, {duration: 400});
            };
            if (window.__pendingFocus) setTimeout(tryFocus, trigger === 'cy' ? 500 : 1500);
            return dash_clientside.no_update;
        }
        """,
        Output("focus-dummy", "data"),
        Input("focus", "data"),
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
        Output("btn-toggle", "children"),
        Output("btn-toggle", "disabled"),
        Output("confirm-delete", "message"),
        Output("view", "style"),
        Output("form", "style"),
        Output("form-title", "children"),
        Output("form-label", "value"),
        Output("form-definition", "value"),
        Output("search", "options"),
        Input("selected", "data"),
        Input("mode", "data"),
        Input("version", "data"),
        Input("collapsed", "data"),
    )
    def render(selected, mode, _version, collapsed):
        collapsed = set(collapsed or [])
        root = storage.load()
        path = tree.find_path(root, selected) or [root]
        node = path[-1]
        n_children = len(node.children)
        n_desc = tree.count_descendants(node)

        # fit is False so zoom/pan survive clicks; the camera is fitted by the clientside
        # callback above, on first load and on the Fit button.
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
            _elements(root, node.id, collapsed),
            layout,
            " › ".join(n.label for n in path),
            node.label,
            node.definition or "*No definition yet. Press Edit to add one.*",
            f"{n_children} child node(s)" if n_children else "No children yet.",
            node is root,
            "Expand" if node.id in collapsed else "Collapse",
            n_children == 0,
            f"Delete “{node.label}”"
            + (f" and its {n_desc} descendant(s)" if n_desc else "")
            + "? This cannot be undone.",
            HIDE if editing else SHOW,
            SHOW if editing else HIDE,
            form_title,
            label,
            definition,
            _search_options(root),
        )
