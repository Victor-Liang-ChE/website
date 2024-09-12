from dash import html, dcc, callback, Output, Input
import dash

dash.register_page(__name__, path='/dropchance', name="Drop Chance Calculator")

def dropchance(percent, attempts):
    if attempts == 1:
        return f'There is a {100 - ((100 - percent) / 100) ** attempts * 100:.1f}% chance that you will receive the {percent}% drop at least once in {attempts} try.'
    else:
        return f'There is a {100 - ((100 - percent) / 100) ** attempts * 100:.1f}% chance that you will receive the {percent}% drop at least once in {attempts} tries.'

layout = html.Div([
    html.Div([
        html.Label("Drop Percentage:"),
        html.Span(id='percent-display', style={'margin-left': '10px'}),
        dcc.Slider(
            id='percent-slider',
            min=0,
            max=100,
            step=1,
            value=0,
            marks={i: f'{i}%' for i in range(0, 101, 10)},
            updatemode='drag'
        ),
    ], style={'margin-top': '20px', 'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px'}),
    html.Div([
        html.Label("Number of Attempts:"),
        html.Span(id='attempts-display', style={'margin-left': '10px'}),
        dcc.Slider(
            id='attempts-slider',
            min=0,
            max=100,
            step=1,
            value=0,
            marks={i: str(i) for i in range(0, 101, 10)},
            updatemode='drag'
        ),
    ], style={'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px'}),
    html.Div(id='result-output', style={'margin-top': '20px', 'font-size': '20px', 'margin-left': '20px', 'margin-right': '20px'})
])

@callback(
    Output('percent-display', 'children'),
    Output('attempts-display', 'children'),
    Output('result-output', 'children'),
    Input('percent-slider', 'value'),
    Input('attempts-slider', 'value')
)
def update_output(percent, attempts):
    percent_display = f'{int(percent)}%'
    attempts_display = str(attempts)
    result = dropchance(percent, attempts)
    return percent_display, attempts_display, result