from dash import html, dcc, Input, Output, State, MATCH, ALL, callback, callback_context, clientside_callback
import dash
import plotly.graph_objs as go
import numpy as np
import control as ctrl

dash.register_page(__name__, path='/PIDTuning', name="PID Tuning")

# Define the FOPTD model parameters
model_parameters = {
    "IMC_PI": {
        "expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$',
        "system": lambda K, tau, theta: ctrl.TransferFunction([K], [tau, 1]) * ctrl.TransferFunction(*ctrl.pade(theta, 1)),
        "Kc": lambda K, tau, theta, tau_c: tau / (K * (tau_c + theta) + 1e-9),
        "tauI": lambda tau: tau
    },
    "AMIGO_PI": {
        "expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$',
        "system": lambda K, tau, theta: ctrl.TransferFunction([K], [tau, 1]) * ctrl.TransferFunction(*ctrl.pade(theta, 1)),
        "Kc": lambda K, tau, theta: 0.15 / (K + 1e-9) + (0.35 - theta * tau / (theta + tau)**2) * (tau / (K + 1e-9) / (theta + 1e-9)),
        "tauI": lambda tau, theta: 0.35 * theta + 13 * theta * tau**2 / (tau**2 + 12 * theta * tau + 7 * theta**2)
    },
    "AMIGO_PID": {
        "expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$',
        "system": lambda K, tau, theta: ctrl.TransferFunction([K], [tau, 1]) * ctrl.TransferFunction(*ctrl.pade(theta, 1)),
        "Kc": lambda K, tau, theta: 1 / (K + 1e-9) * (0.2 + 0.45 * tau / theta),
        "tauI": lambda tau, theta: (0.4 * theta + 0.8 * tau) * theta / (theta + 0.1 * tau),
        "tauD": lambda tau, theta: 0.5 * theta * tau / (0.3 * theta + tau)
    },
    "ITAE_PI": {
        "expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$',
        "system": lambda K, tau, theta: ctrl.TransferFunction([K], [tau, 1]) * ctrl.TransferFunction(*ctrl.pade(theta, 1)),
        "Kc": lambda K, tau, theta: 0.859 * (theta / tau) ** -0.977 / (K + 1e-9),
        "tauI": lambda tau, theta: tau / (0.674 * (theta / tau) ** -0.68)
    },
    "ITAE_PID": {
        "expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$',
        "system": lambda K, tau, theta: ctrl.TransferFunction([K], [tau, 1]) * ctrl.TransferFunction(*ctrl.pade(theta, 1)),
        "Kc": lambda K, tau, theta: 1.357 * (theta / tau) ** -0.947 / (K + 1e-9),
        "tauI": lambda tau, theta: tau / (0.842 * (theta / tau) ** -0.738),
        "tauD": lambda tau, theta: tau * (0.381 * (theta / tau) ** 0.995)
    }
}

layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='method-dropdown',
            options=[
                {'label': 'IMC', 'value': 'IMC'},
                {'label': 'AMIGO', 'value': 'AMIGO'},
                {'label': 'ITAE', 'value': 'ITAE'}
            ],
            placeholder="Select a tuning method",
            style={
                'width': '100%',  # Full width within its container
                'min-width': '350px',  # Minimum width to prevent shrinking
                'max-width': '350px',  # Maximum width to prevent expanding
                'color': 'black'
            }
        ),
        dcc.Dropdown(
            id='model-dropdown',
            options=[
                {'label': 'PI FOPTD', 'value': 'PI_FOPTD'},
                {'label': 'PID FOPTD', 'value': 'PID_FOPTD'}
            ],
            placeholder="Select a model",
            style={
                'width': '100%',  # Full width within its container
                'min-width': '350px',  # Minimum width to prevent shrinking
                'max-width': '350px',  # Maximum width to prevent expanding
                'color': 'black',
                'display': 'none'  # Initially hidden
            }
        ),
        html.Div(id='sliders-container', style={'display': 'none'})  # Container for sliders, initially hidden
    ], style={'width': '30%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top'}),  # Left container with dropdown menu and sliders
    
    html.Div([
        dcc.Markdown(id='model-expression', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True),
        html.Div([
            html.Div([
                dcc.Markdown(r'$K_{c}:$', id='label-Kc', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True),
                dcc.Markdown(id='model-Kc', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True)
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div([
                dcc.Markdown(r'$\tau_{I}:$', id='label-tauI', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True),
                dcc.Markdown(id='model-tauI', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True)
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div([
                dcc.Markdown(r'$\tau_{D}:$', id='label-tauD', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True),
                dcc.Markdown(id='model-tauD', style={'margin-bottom': '10px', 'color': 'white', 'display': 'none'}, mathjax=True)
            ], style={'display': 'flex', 'align-items': 'center'})
        ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'})
    ], style={'margin-left': '2px', 'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'text-align': 'center'}),  # Div for displaying model details

    html.Div([
        dcc.Graph(id='response-graph', style={'display': 'none'}),  # Graph for system response, initially hidden
    ], style={'width': '60%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top', 'text-align': 'center'})  # Right container for graph
], style={'display': 'flex', 'width': '100%'})  # Set the main container to use flexbox and take up 100% width

@callback(
    [Output('model-dropdown', 'style', allow_duplicate=True),
     Output('model-dropdown', 'options', allow_duplicate=True),
     Output('model-dropdown', 'value', allow_duplicate=True),
     Output('sliders-container', 'style', allow_duplicate=True),
     Output('response-graph', 'style', allow_duplicate=True),
     Output('sliders-container', 'children', allow_duplicate=True),
     Output('model-expression', 'style', allow_duplicate=True),
     Output('label-Kc', 'style', allow_duplicate=True),
     Output('model-Kc', 'style', allow_duplicate=True),
     Output('label-tauI', 'style', allow_duplicate=True),
     Output('model-tauI', 'style', allow_duplicate=True),
     Output('label-tauD', 'style', allow_duplicate=True),
     Output('model-tauD', 'style', allow_duplicate=True)],
    [Input('method-dropdown', 'value'),
     Input('model-dropdown', 'value')],
    prevent_initial_call=True
)
def toggle_elements(selected_method, selected_model):
    ctx = callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'method-dropdown':
        if selected_method == 'IMC':
            model_options = [{'label': 'PI FOPTD', 'value': 'PI_FOPTD'}]
        elif selected_method == 'ITAE':
            model_options = [
                {'label': 'PI FOPTD Disturbance', 'value': 'PI_FOPTD'},
                {'label': 'PID FOPTD Disturbance', 'value': 'PID_FOPTD'}
            ]
        else:
            model_options = [
                {'label': 'PI FOPTD', 'value': 'PI_FOPTD'},
                {'label': 'PID FOPTD', 'value': 'PID_FOPTD'}
            ]
        return {
            'width': '100%',  # Full width within its container
            'min-width': '350px',  # Minimum width to prevent shrinking
            'max-width': '350px',  # Maximum width to prevent expanding
            'color': 'black',
            'display': 'block'  # Show the dropdown
        }, model_options, None, {'display': 'none'}, {'display': 'none'}, [], {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    
    if trigger_id == 'model-dropdown' and selected_model:
        sliders = [
            html.Div([
                dcc.Markdown(r'$K:$', style={'color': 'white', 'display': 'inline-block'}, mathjax=True),
                dcc.Markdown(f'1.0', id='K-display', style={'color': 'white', 'display': 'inline-block', 'margin-left': '10px'}),
                dcc.Slider(id={'type': 'slider', 'index': 'K'}, min=0.1, max=10, step=0.1, value=1, marks={i: str(i) for i in range(1, 11)}, updatemode='drag')
            ]),
            html.Div([
                dcc.Markdown(r'$\tau:$', style={'color': 'white', 'display': 'inline-block'}, mathjax=True),
                dcc.Markdown(f'1.0', id='tau-display', style={'color': 'white', 'display': 'inline-block', 'margin-left': '10px'}),
                dcc.Slider(id={'type': 'slider', 'index': 'tau'}, min=0.1, max=10, step=0.1, value=1, marks={i: str(i) for i in range(1, 11)}, updatemode='drag')
            ]),
            html.Div([
                dcc.Markdown(r'$\theta:$', style={'color': 'white', 'display': 'inline-block'}, mathjax=True),
                dcc.Markdown(f'1.0', id='theta-display', style={'color': 'white', 'display': 'inline-block', 'margin-left': '10px'}),
                dcc.Slider(id={'type': 'slider', 'index': 'theta'}, min=0.1, max=10, step=0.1, value=1, marks={i: str(i) for i in range(1, 11)}, updatemode='drag')
            ])
        ]

        if selected_method == 'IMC' and selected_model == 'PI_FOPTD':
            sliders.append(
                html.Div([
                    dcc.Markdown(r'$\tau_{c}$:', style={'color': 'white', 'display': 'inline-block'}, mathjax=True),
                    dcc.Markdown(f'1.0', id='tauc-display', style={'color': 'white', 'display': 'inline-block', 'margin-left': '10px'}),
                    dcc.Slider(id={'type': 'slider', 'index': 'tauc'}, min=0.1, max=10, step=0.1, value=1, marks={i: str(i) for i in range(1, 11)}, updatemode='drag')
                ])
            )

        show_tauD = selected_model == 'PID_FOPTD'
        return dash.no_update, dash.no_update, dash.no_update, {'display': 'block'}, {'display': 'block'}, sliders, {'margin-bottom': '10px', 'color': 'white', 'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block' if show_tauD else 'none'}, {'display': 'block' if show_tauD else 'none'}

    return dash.no_update, dash.no_update, dash.no_update, {'display': 'none'}, {'display': 'none'}, [], {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

# Clientside callbacks to update the display of slider values
clientside_callback(
    """
    function(K) {
        return `${K.toFixed(1)}`;
    }
    """,
    Output('K-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'K'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(tau) {
        return `${tau.toFixed(1)}`;
    }
    """,
    Output('tau-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'tau'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(theta) {
        return `${theta.toFixed(1)}`;
    }
    """,
    Output('theta-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'theta'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(tauc) {
        return `${tauc.toFixed(1)}`;
    }
    """,
    Output('tauc-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'tauc'}, 'value'),
    prevent_initial_call=True
)

@callback(
    [Output('model-expression', 'children', allow_duplicate=True),
     Output('response-graph', 'figure', allow_duplicate=True),
     Output('model-Kc', 'children', allow_duplicate=True),
     Output('model-tauI', 'children', allow_duplicate=True),
     Output('model-tauD', 'children', allow_duplicate=True)],
    [Input({'type': 'slider', 'index': ALL}, 'value')],
    [State('method-dropdown', 'value'),
     State('model-dropdown', 'value')],
    prevent_initial_call=True
)
def update_graph(slider_values, selected_method, selected_model):
    if selected_method is None or selected_model is None or any(v is None for v in slider_values):
        raise dash.exceptions.PreventUpdate

    K, tau, theta = slider_values[:3]
    tau_c = slider_values[3] if selected_method == 'IMC' and selected_model == 'PI_FOPTD' else None

    # Retrieve model information
    model_key = f"{selected_method}_{selected_model.split('_')[0]}"
    model_info = model_parameters[model_key]

    # Generate system transfer function
    system = model_info['system'](K, tau, theta)

    # Calculate tuning parameters
    Kc = model_info['Kc'](K, tau, theta, tau_c) if selected_method == 'IMC' and selected_model == 'PI_FOPTD' else model_info['Kc'](K, tau, theta)
    tauI = model_info['tauI'](tau, theta) if selected_method != 'IMC' or selected_model != 'PI_FOPTD' else model_info['tauI'](tau)
    tauD = model_info['tauD'](tau, theta) if selected_model == 'PID_FOPTD' else None

    # Create the PID controller transfer function
    if selected_model == 'PID_FOPTD':
        Gc = ctrl.TransferFunction([Kc * tauD, Kc, Kc / tauI], [1, 0])
    else:
        Gc = ctrl.TransferFunction([Kc, Kc / tauI], [1, 0])

    # Closed-loop transfer function
    T = ctrl.feedback(system * Gc)

    # Simulate the system with step response
    t = np.linspace(0, 30, 200)
    t, y = ctrl.step_response(T, T=t)

    # Set negative responses to zero
    y = np.maximum(y, 0)

    # Create the response graph
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=t, y=y, mode='lines', name=f'{selected_method} Output'))
    figure.update_layout(
        title=f"System Response for FOPTD Model with {selected_method} Tuning",
        xaxis_title="Time",
        yaxis_title="Output",
        legend_title="Legend",
        template="plotly_dark",
        plot_bgcolor="#08306b",
        paper_bgcolor="#08306b",
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )

    return [
        f"Model: {model_info['expression']}",
        figure,
        f"{Kc:.2f}",
        f"{tauI:.2f}",
        f"{tauD:.2f}" if tauD else dash.no_update
    ]