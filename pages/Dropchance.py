from dash import html, dcc, clientside_callback, callback, Output, Input, State
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
    html.Div([
        html.Label("Desired Number of Drops:"),
        html.Span(id='desired-drops-display', style={'margin-left': '10px'}),
        dcc.Slider(
            id='desired-drops-slider',
            min=0,
            max=100,
            step=1,
            value=1,
            marks={i: str(i) for i in range(0, 101, 10)},
            updatemode='drag'
        ),
    ], id='single-desired-drops-container', style={'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px'}),
    html.Div([
        html.Label("Desired Drops Range:"),
        html.Span(id='desired-drops-range-display', style={'margin-left': '10px'}),
        dcc.RangeSlider(
            id='desired-drops-range-slider',
            min=0,
            max=100,
            step=1,
            value=[1, 2],
            marks={i: str(i) for i in range(0, 101, 10)},
            updatemode='drag'
        ),
    ], id='range-desired-drops-container', style={'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px', 'display': 'none'}),
    html.Div(id='result-output', style={'margin-top': '20px', 'font-size': '20px', 'margin-left': '20px', 'margin-right': '20px'}),
    html.Div([
        html.Button('Toggle Desired Drops Mode', id='toggle-button', n_clicks=0),
    ], style={'margin-top': '20px', 'margin-left': '20px', 'margin-right': '20px'})
])

clientside_callback(
    """
    function(percent, attempts, desired_drops, desired_drops_range, toggle_state) {
        const percent_display = `${percent}%`;
        const attempts_display = `${attempts}`;
        const desired_drops_display = `at least ${desired_drops}`;
        const desired_drops_range_display = `${desired_drops_range[0]} to ${desired_drops_range[1]}`;
        let result;

        function binomialCoefficient(n, k) {
            let coeff = 1;
            for (let x = n - k + 1; x <= n; x++) coeff *= x;
            for (let x = 1; x <= k; x++) coeff /= x;
            return coeff;
        }

        function binomialProbability(n, k, p) {
            return binomialCoefficient(n, k) * Math.pow(p, k) * Math.pow(1 - p, n - k);
        }

        const p = percent / 100;
        let cumulativeProbability = 0;

        if (toggle_state % 2 === 0) {
            // Single desired drops mode
            for (let k = 0; k < desired_drops; k++) {
                cumulativeProbability += binomialProbability(attempts, k, p);
            }
            const chance = Math.max((1 - cumulativeProbability) * 100, 0);

            const attempts_text = attempts === 1 ? 'try' : 'tries';
            const drops_text = desired_drops === 1 ? 'time' : 'times';

            result = `There is a ${chance.toFixed(1)}% chance that you will receive the ${percent}% drop at least ${desired_drops} ${drops_text} in ${attempts} ${attempts_text}.`;
        } else {
            // Range desired drops mode
            for (let k = desired_drops_range[0]; k <= desired_drops_range[1]; k++) {
                cumulativeProbability += binomialProbability(attempts, k, p);
            }
            const chance = Math.max(cumulativeProbability * 100, 0);

            const attempts_text = attempts === 1 ? 'try' : 'tries';
            const range_text = desired_drops_range[1] === 1 ? 'time' : 'times';

            result = `There is a ${chance.toFixed(1)}% chance that you will receive the ${percent}% drop between ${desired_drops_range[0]} and ${desired_drops_range[1]} ${range_text} in ${attempts} ${attempts_text}.`;
        }

        return [percent_display, attempts_display, desired_drops_display, desired_drops_range_display, result];
    }
    """,
    [Output('percent-display', 'children'),
     Output('attempts-display', 'children'),
     Output('desired-drops-display', 'children'),
     Output('desired-drops-range-display', 'children'),
     Output('result-output', 'children')],
    [Input('percent-slider', 'value'),
     Input('attempts-slider', 'value'),
     Input('desired-drops-slider', 'value'),
     Input('desired-drops-range-slider', 'value'),
     Input('toggle-button', 'n_clicks')]
)

@callback(
    [Output('single-desired-drops-container', 'style'),
     Output('range-desired-drops-container', 'style'),
     Output('toggle-button', 'children')],
    [Input('toggle-button', 'n_clicks'),
     State('desired-drops-slider', 'value'),
     State('desired-drops-range-slider', 'value')]
)
def toggle_desired_drops_mode(n_clicks, desired_drops, desired_drops_range):
    if n_clicks % 2 == 0:
        range_text = "time" if desired_drops_range[1] == 1 else "times"
        button_text = f"Change to drop between {desired_drops_range[0]} and {desired_drops_range[1]} {range_text}"
        return {'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px'}, {'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px', 'display': 'none'}, button_text
    else:
        single_text = "time" if desired_drops == 1 else "times"
        button_text = f"Change to drop at least {desired_drops} {single_text}"
        return {'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px', 'display': 'none'}, {'margin-bottom': '20px', 'margin-left': '20px', 'margin-right': '20px'}, button_text