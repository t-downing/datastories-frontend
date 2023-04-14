from dash import Dash, html, dcc, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import requests

MENU_WIDTH = 0
API_URL = "http://127.0.0.1:8000/api/"

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
            dbc.Button(
                id=(ADD_MODEL_OPEN := "load-model-open"),
                className="mx-3",
                children="Create new model"
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
            # layout={"name": "preset", "fit": False},
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
])


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
    Output(ADD_MODEL_LABEL, "value"),
    Output(MODEL_INPUT, "options"),
    Output(MODEL_INPUT, "value"),
    Input(ADD_MODEL_SUBMIT, "n_clicks"),
    State(ADD_MODEL_LABEL, "value"),
)
def create_model(n_clicks, label):
    if n_clicks is None:
        models = requests.get(API_URL + "models").json()
        return (
            None,
            [
                {"value": option.get("id"), "label": option.get("label")}
                for option in models
            ],
            models[0].get("id")
        )
    data = {"label": label}
    requests.post(API_URL + "models/", data=data)
    models = requests.get(API_URL + "models").json()
    return (
        None,
        [
            {"value": option.get("id"), "label": option.get("label")}
            for option in models
        ],
        models[-1].get("id")
    )


if __name__ == '__main__':
    app.run_server(debug=True)