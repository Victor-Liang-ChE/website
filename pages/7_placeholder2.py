from dash import html, dcc, callback, Output, Input
import dash


dash.register_page(__name__, path='/placeholder2', name="Placeholder")

def dropchance(percent, attempts):
    print(f'There is a {100 - ((100 - percent) / 100) ** attempts * 100:.1f}% chance that you will receive the {percent}% drop at least once in {attempts} tries.')

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
