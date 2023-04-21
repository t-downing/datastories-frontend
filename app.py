from dash import Dash, html, dcc, callback, Output, Input, State, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import requests

MENU_WIDTH = 0
API_ROOT = "http://127.0.0.1:8000/api/"
API_MODELS = "models/"
API_QUALELEMENTS = "qualelements/"
API_LAYOUTS = "layouts/"
API_QUALPOSITIONS = "qualelementpositions/"

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(children=[
    html.Div(
        id="left-sidebar",
        style={"position": "fixed", "width": "200px", 'top': 0, 'left': MENU_WIDTH, 'zIndex': 1},
        children=[
            dbc.Select(
                id=(MODEL_INPUT := "model-input"),
                className="m-3",
            ),
            dbc.Select(
                id=(LAYOUT_INPUT := "layout-input"),
                className="m-3",
            ),
            dbc.Button(
                id=(ADD_MODEL_OPEN := "add-model-open"),
                className="mx-3",
                children="Create new model"
            ),
            dbc.Button(
                id=(ADD_ELEMENT_OPEN := "add-element-open"),
                className="m-3",
                children="Add an element",
            ),
        ]
    ),
    html.Div(
        style={
            "position": "fixed",
            "top": 0,
            'left': MENU_WIDTH,
            "width": "100%",
            "zIndex": "0",
        },
        children=cyto.Cytoscape(
            id="cyto",
            layout={"name": "preset"},
            style={"height": "100vh", "background-color": "#f8f9fc"},
            # stylesheet=stylesheet,
            # minZoom=0.2,
            # maxZoom=2.0,
            # boxSelectionEnabled=True,
            autoRefreshLayout=True,
            # responsive=True,
            # zoom=0.4,
            # pan={"x": 500, "y": 300},
        ),
    ),
    dbc.Modal(
        id=(ADD_MODEL_MODAL := "add-model-modal"),
        is_open=False,
        children=[
            dbc.ModalHeader("Create new model"),
            dbc.ModalBody([
                dbc.InputGroup(
                    className="mb-2",
                    children=[dbc.InputGroupText("Name"), dbc.Input(id=(ADD_MODEL_LABEL := "add-model-label"))],
                ),
                dbc.Button(id=(ADD_MODEL_SUBMIT := "add-model-submit"), children="Submit"),
            ]),
        ],
    ),
    dbc.Modal(
        id=(ADD_ELEMENT_MODAL := "add-element-modal"),
        is_open=False,
        children=[
            dbc.ModalHeader("Create new element"),
            dbc.ModalBody([
                dbc.InputGroup(
                    className="mb-2",
                    children=[dbc.InputGroupText("Name"), dbc.Input(id=(ADD_ELEMENT_LABEL := "add-element-label"))],
                ),
                dbc.Button(
                    id=(ADD_ELEMENT_SUBMIT := "add-element-submit"),
                    children="Submit"
                ),
            ]),
        ],
    ),
])


@callback(
    Output(LAYOUT_INPUT, "options"),
    Output(LAYOUT_INPUT, "value"),
    Input(MODEL_INPUT, "value"),
)
def layout_options(model_id):
    layouts = requests.get(API_ROOT + API_LAYOUTS + f"?model_id={model_id}").json()
    options = [
        {"value": layout.get("id"), "label": layout.get("label")}
        for layout in layouts
    ]
    value = requests.get(API_ROOT + API_MODELS + str(model_id)).json().get("default_layout_id")
    return options, value


@callback(
    Output(ADD_MODEL_MODAL, "is_open"),
    Input(ADD_MODEL_OPEN, "n_clicks"),
    Input(ADD_MODEL_SUBMIT, "n_clicks"),
    State(ADD_MODEL_MODAL, "is_open"),
)
def add_model_modal(open_clicks, submit_clicks, is_open):
    if open_clicks or submit_clicks:
        return not is_open
    return is_open


@callback(
    Output(ADD_ELEMENT_MODAL, "is_open"),
    Input(ADD_ELEMENT_OPEN, "n_clicks"),
    Input(ADD_ELEMENT_SUBMIT, "n_clicks"),
    State(ADD_ELEMENT_MODAL, "is_open"),
)
def add_element_modal(open_clicks, submit_clicks, is_open):
    if open_clicks or submit_clicks:
        return not is_open
    return is_open


@callback(
    Output(ADD_MODEL_LABEL, "value"),
    Output(MODEL_INPUT, "options"),
    Output(MODEL_INPUT, "value"),
    Input(ADD_MODEL_SUBMIT, "n_clicks"),
    State(ADD_MODEL_LABEL, "value"),
)
def create_model(n_clicks, label):
    if n_clicks is None:
        models = requests.get(API_ROOT + "models").json()
        return (
            None,
            [
                {"value": option.get("id"), "label": option.get("label")}
                for option in models
            ],
            models[0].get("id")
        )
    new_model = requests.post(API_ROOT + "models/", data={"label": label}).json()
    print(f"{new_model=}")
    data = {"label": "default", "model_id": new_model.get("id")}
    default_layout = requests.post(API_ROOT + API_LAYOUTS, data=data).json()
    print(f"{default_layout=}")
    data = {"default_layout_id": default_layout.get("id")}
    requests.put(API_ROOT + API_MODELS, params={"id": new_model.get("id")}, data=data)

    models = requests.get(API_ROOT + "models/").json()
    return (
        None,
        [
            {"value": option.get("id"), "label": option.get("label")}
            for option in models
        ],
        models[-1].get("id")
    )


@callback(
    Output("cyto", "elements"),
    Input(ADD_ELEMENT_SUBMIT, "n_clicks"),
    Input(LAYOUT_INPUT, "value"),
    State(ADD_ELEMENT_LABEL, "value"),
)
def redraw_map(add_element_clicks, layout_id, element_label):
    if layout_id is None:
        raise PreventUpdate
    if ctx.triggered_id == ADD_ELEMENT_SUBMIT:
        print("adding")
        data = {"label": element_label}
        requests.post(API_ROOT + API_QUALELEMENTS, data)

    params = {"layout_id": layout_id}
    qualpositions = requests.get(API_ROOT + API_QUALPOSITIONS, params=params).json()
    print(f"{qualpositions=}")

    cyto_elements = []
    cyto_elements.extend([
        {
            "data":
                {
                    "id": str(obj.get("element").get("id")),
                    "label": obj.get("element").get("label"),
                },
            "position": {"x": obj.get("x"), "y": obj.get("y")},
            "classes": "qualelement"
        }
        for obj in qualpositions
    ])
    print(f"{cyto_elements=}")
    return cyto_elements


if __name__ == '__main__':
    app.run_server(debug=True)