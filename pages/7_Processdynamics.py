from dash import Dash, html, dcc, clientside_callback, callback, Output, Input, State, ctx, MATCH, ALL
import dash
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import numpy as np

dash.register_page(__name__, path='/processdynamics', name="Process Dynamics")

layout = html.Div([
    html.Div([
        html.Div([
            html.Button('1st Order', id='first-order-button', className='btn btn-primary', style={'margin-right': '10px'}),
            html.Button('2nd Order', id='second-order-button', className='btn btn-secondary', style={'margin-right': '10px'})
        ], id='order-buttons', style={'margin-bottom': '20px', 'text-align': 'left', 'display': 'flex'}),
        
        html.Div(id='function-buttons', style={'text-align': 'left', 'margin-bottom': '20px', 'display': 'flex'}),
        
        html.Div(id='sliders-container', style={'display': 'block', 'padding': '10px', 'text-align': 'center', 'width': '100%'}),
        
        html.Div([
            dcc.Checklist(
                id='lock-axes',
                options=[{'label': 'Lock Y-axis', 'value': 'lock'}],
                value=[],
                style={'margin-top': '10px'}
            )
        ], style={'text-align': 'left', 'margin-top': '20px'})
    ], style={'width': '30%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top'}),  # Left container with order buttons, function buttons, sliders, and lock axes button
    
    html.Div([
        dcc.Graph(id='graph-output', style={'display': 'block', 'width': '100%', 'height': '100vh'})  # Graph width set to 100% of its container
    ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),  # Allows the graph container to expand to fill remaining space

    html.Div([
        html.Div(id='peak-time-output', style={'margin-bottom': '10px', 'color': 'white'}),
        html.Div(id='overshoot-output', style={'margin-bottom': '10px', 'color': 'white'}),
        html.Div(id='oscillation-period-output', style={'margin-bottom': '10px', 'color': 'white'}),
        html.Div(id='decay-ratio-output', style={'margin-bottom': '10px', 'color': 'white'})
    ], style={'margin-left': '2px', 'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center'}),  # Div for displaying metrics

    dcc.Store(id='order-store', data='first'),  # Set initial order to 'first'
    dcc.Store(id='function-store', data='step'),  # Set initial function to 'step'
    dcc.Store(id='axes-limits-store', data={'x': None, 'y': None}),  # Store for axes limits
    dcc.Store(id='metrics-store', data={})  # Store for metrics data
], style={'display': 'flex', 'width': '100%'})  # Set the main container to use flexbox and take up 100% width

@callback(
    [Output('function-buttons', 'children'),
     Output('order-store', 'data')],
    [Input('first-order-button', 'n_clicks'),
     Input('second-order-button', 'n_clicks')],
    [State('order-store', 'data')]
)
def display_function_buttons(first_order_clicks, second_order_clicks, order_store):
    ctx_triggered = ctx.triggered_id
    if ctx_triggered == 'first-order-button':
        order_store = 'first'
    elif ctx_triggered == 'second-order-button':
        order_store = 'second'

    if order_store == 'first':
        return html.Div([
            html.Button('Step Function', id='step-function-button', className='btn btn-info', style={'margin-right': '10px'}),
            html.Button('Ramp Function', id='ramp-function-button', className='btn btn-warning', style={'margin-right': '10px'})
        ], style={'display': 'flex'}), order_store
    elif order_store == 'second':
        return html.Div([
            html.Button('Step Function', id='step-function-button', className='btn btn-info', style={'margin-right': '10px'}),
            html.Button('Ramp Function', id='ramp-function-button', className='btn btn-warning', style={'margin-right': '10px', 'background-color': 'grey', 'pointer-events': 'none'})
        ], style={'display': 'flex'}), order_store
    return html.Div(), order_store

@callback(
    [Output('sliders-container', 'children'),
     Output('sliders-container', 'style'),
     Output('function-store', 'data')],
    [Input('step-function-button', 'n_clicks'),
     Input('ramp-function-button', 'n_clicks'),
     Input('order-store', 'data')],
    [State('function-store', 'data')],
    prevent_initial_call=False
)
def update_sliders(step_function_clicks, ramp_function_clicks, order_store, function_store):
    ctx_triggered = ctx.triggered_id
    sliders = []
    sliders_style = {'display': 'none'}
    function_store = function_store or 'step'

    if ctx_triggered in ['step-function-button', 'ramp-function-button', 'order-store']:
        sliders = [
            html.Div([
                html.Label('Gain (K):', style={'margin-right': '10px'}),
                html.Span(id='K-display', style={'margin-right': '10px'}),
                dcc.Slider(id={'type': 'slider', 'name': 'K'}, min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag')
            ], style={'margin-bottom': '10px'}),
            html.Div([
                html.Label('Magnitude (M):', style={'margin-right': '10px'}),
                html.Span(id='M-display', style={'margin-right': '10px'}),
                dcc.Slider(id={'type': 'slider', 'name': 'M'}, min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag')
            ], style={'margin-bottom': '10px'}),
            html.Div([
                html.Label('Time Constant (τ):', style={'margin-right': '10px'}),
                html.Span(id='tau-display', style={'margin-right': '10px'}),
                dcc.Slider(id={'type': 'slider', 'name': 'tau'}, min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag')
            ], style={'margin-bottom': '10px'})
        ]
        sliders_style = {'display': 'block', 'width': '100%'}

    if order_store == 'second':
        sliders.append(
            html.Div([
                html.Label('Damping Ratio (ζ):', style={'margin-right': '10px'}),
                html.Span(id='zeta-display', style={'margin-right': '10px'}),
                dcc.Slider(id={'type': 'slider', 'name': 'zeta'}, min=0, max=2, step=0.01, value=1, marks={i: str(i) for i in range(3)}, updatemode='drag')
            ], style={'margin-bottom': '10px'})
        )

    if ctx_triggered == 'step-function-button':
        function_store = 'step'
    elif ctx_triggered == 'ramp-function-button':
        function_store = 'ramp'

    return sliders, sliders_style, function_store

clientside_callback(
    """
    function(K, M, tau) {
        return [`${K.toFixed(1)}`, `${M.toFixed(1)}`, `${tau.toFixed(1)}`];
    }
    """,
    [Output('K-display', 'children'),
     Output('M-display', 'children'),
     Output('tau-display', 'children')],
    [Input({'type': 'slider', 'name': 'K'}, 'value'),
     Input({'type': 'slider', 'name': 'M'}, 'value'),
     Input({'type': 'slider', 'name': 'tau'}, 'value')]
)

clientside_callback(
    """
    function(zeta, order_store) {
        if (order_store === 'second') {
            return [`${zeta.toFixed(2)}`];
        }
        return [dash_clientside.no_update];
    }
    """,
    Output('zeta-display', 'children'),
    [Input({'type': 'slider', 'name': 'zeta'}, 'value'),
     Input('order-store', 'data')]
)

clientside_callback(
    """
    function(slider_values, lock_axes, order_store, function_store, axes_limits) {
        if (slider_values.length < 3) {
            return [[], axes_limits];  // Return default figure if sliders are not ready
        }

        const K = slider_values[0] || 1;
        const M = slider_values[1] || 1;
        const tau = slider_values[2] || 1;
        const zeta = slider_values[3] || null;

        let t = Array.from({length: 100}, (_, i) => i * 50 / 99);  // Ensure time extends to 50

        let y = Array(t.length).fill(0);
        let y_input = Array(t.length).fill(0);
        let title = '';
        let peak_time = null;
        let overshoot = null;
        let oscillation_period = null;
        let decay_ratio = null;

        if (order_store === 'first' && function_store === 'step') {
            y = t.map(ti => K * M * (1 - Math.exp(-ti / tau)));
            y_input = y_input.map(() => M);
            title = 'First Order Step Function Response';
        } else if (order_store === 'first' && function_store === 'ramp') {
            y = t.map(ti => K * M * (Math.exp(-ti / tau) - 1) + K * M * ti);
            y_input = t.map(ti => M * ti);
            title = 'First Order Ramp Function Response';
        } else if (order_store === 'second' && function_store === 'step') {
            if (zeta !== null && zeta < 1) {
                y = t.map(ti => K * M * (1 - Math.exp(-zeta * ti / tau) * (Math.cos(Math.sqrt(1 - zeta**2) * ti / tau) + (zeta / Math.sqrt(1 - zeta**2)) * Math.sin(Math.sqrt(1 - zeta**2) * ti / tau))));
                peak_time = Math.PI * tau / Math.sqrt(1 - zeta**2);
                overshoot = Math.exp(-Math.PI * zeta / Math.sqrt(1 - zeta**2));
                oscillation_period = 2 * Math.PI * tau / Math.sqrt(1 - zeta**2);
                decay_ratio = overshoot**2;
            } else if (zeta !== null) {
                y = t.map(ti => K * M * (1 - (1 + ti / tau) * Math.exp(-zeta * ti / tau)));
            }
            y_input = y_input.map(() => M);
            title = 'Second Order Step Function Response';
        }

        const figure = {
            data: [
                {x: t, y: y, mode: 'lines', name: 'System Response', line: {color: 'yellow'}},
                {x: t, y: y_input, mode: 'lines', name: 'Input', line: {color: 'red', dash: 'dot'}}
            ],
            layout: {
                title: {
                    text: title,
                    x: 0.5,
                    font: {size: 24, family: 'Merriweather Sans', color: 'white'}
                },
                xaxis: {
                    title: 'Time',
                    titlefont: {size: 24, family: 'Merriweather Sans', color: 'white'},  // Set x-axis title color to white
                    tickfont: {size: 18, family: 'Merriweather Sans', color: 'white'},
                    ticks: 'outside',
                    ticklen: 5,
                    tickwidth: 2,
                    tickcolor: 'white',
                    gridcolor: 'rgba(0,0,0,0)'
                },
                yaxis: {
                    title: 'Response/Input',
                    titlefont: {size: 24, family: 'Merriweather Sans', color: 'white'},  // Set y-axis title color to white
                    tickfont: {size: 18, family: 'Merriweather Sans', color: 'white'},
                    ticks: 'outside',
                    ticklen: 5,
                    tickwidth: 2,
                    tickcolor: 'white',
                    gridcolor: 'rgba(0,0,0,0)'
                },
                legend: {
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: 1.02,
                    xanchor: 'right',
                    x: 1,
                    font: {color: 'white'}
                },
                template: 'plotly_dark',
                plot_bgcolor: '#08306b',
                paper_bgcolor: '#08306b',
                autosize: false,
                width: 500,
                height: 500
            }
        };

        if (lock_axes.includes('lock')) {
            if (axes_limits.x && axes_limits.y) {
                figure.layout.xaxis.range = axes_limits.x;
                figure.layout.yaxis.range = axes_limits.y;
            }
        } else {
            const x_range = [0, 50];  // Ensure x-axis extends to 50
            const y_range = y.length ? [Math.min(...y) * 1.1, Math.max(...y) * 1.1] : [0, 1];
            figure.layout.xaxis.range = x_range;
            figure.layout.yaxis.range = y_range;
            axes_limits = {x: x_range, y: y_range};  // Update store with the new axes limits
        }

        let metrics_data = {};
        if (order_store === 'second') {
            metrics_data = {
                peak_time: peak_time !== null ? peak_time.toFixed(2) : '',
                overshoot: overshoot !== null ? overshoot.toFixed(2) : '',
                oscillation_period: oscillation_period !== null ? oscillation_period.toFixed(2) : '',
                decay_ratio: decay_ratio !== null ? decay_ratio.toFixed(2) : ''
            };
        } else {
            metrics_data = {
                peak_time: '',
                overshoot: '',
                oscillation_period: '',
                decay_ratio: ''
            };
        }

        return [figure, axes_limits, metrics_data];
    }
    """,
    [Output('graph-output', 'figure', allow_duplicate=True),
     Output('axes-limits-store', 'data', allow_duplicate=True),
     Output('metrics-store', 'data')],
    [Input({'type': 'slider', 'name': ALL}, 'value'),
     Input('lock-axes', 'value')],
    [State('order-store', 'data'),
     State('function-store', 'data'),
     State('axes-limits-store', 'data')],
    prevent_initial_call=True
)

clientside_callback(
    """
    function(metrics_data, order_store) {
        if (order_store !== 'second') {
            return ["", "", "", ""];
        }
        return [
            `Peak Time: ${metrics_data.peak_time}`,
            `Overshoot: ${metrics_data.overshoot}`,
            `Oscillation Period: ${metrics_data.oscillation_period}`,
            `Decay Ratio: ${metrics_data.decay_ratio}`
        ];
    }
    """,
    [Output('peak-time-output', 'children'),
     Output('overshoot-output', 'children'),
     Output('oscillation-period-output', 'children'),
     Output('decay-ratio-output', 'children')],
    [Input('metrics-store', 'data'),
     Input('order-store', 'data')]
)