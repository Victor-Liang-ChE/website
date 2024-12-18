from dash import html, dcc, clientside_callback, Output, Input
import dash

dash.register_page(__name__, path='/dropchance', name="Drop Chance Calculator")

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

clientside_callback(
    """
    function(percent, attempts) {
        const percent_display = `${percent}%`;
        const attempts_display = `${attempts}`;
        let result;
        const chance = 100 - Math.pow((100 - percent) / 100, attempts) * 100;
        if (attempts == 1) {
            result = `There is a ${chance.toFixed(1)}% chance that you will receive the ${percent}% drop at least once in ${attempts} try.`;
        } else {
            result = `There is a ${chance.toFixed(1)}% chance that you will receive the ${percent}% drop at least once in ${attempts} tries.`;
        }
        return [percent_display, attempts_display, result];
    }
    """,
    [Output('percent-display', 'children'),
     Output('attempts-display', 'children'),
     Output('result-output', 'children')],
    [Input('percent-slider', 'value'),
     Input('attempts-slider', 'value')]
)