from dash import html, Input, Output, callback, dcc
import dash


dash.register_page(__name__, path='/emailgen', name="Email Generator")

layout = html.Div([
    html.H1("Drop Chance Calculator"),
    html.Div([
        html.Label("Drop Percentage:"),
        dcc.Input(id='percent-input', type='number', value=0, min=0, max=100, step=0.1),
    ]),
    html.Div([
        html.Label("Number of Attempts:"),
        dcc.Input(id='attempts-input', type='number', value=0, min=0, step=1),
    ]),
    html.Button('Calculate', id='calculate-button', n_clicks=0),
    html.Div(id='result-output', style={'margin-top': '20px', 'font-size': '20px'})
])
