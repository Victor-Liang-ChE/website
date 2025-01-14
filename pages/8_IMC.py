from dash import html, dcc, Input, Output, callback, ALL, clientside_callback
from dash.exceptions import PreventUpdate
import dash
import numpy as np
import plotly.graph_objs as go
from dash import callback_context as ctx
from scipy.signal import lti, step

dash.register_page(__name__, path='/PIDTuning', name="PID Tuning")

# Dictionary to store the associated values for each model
epsilon = 1e-9  # Small value to prevent division by zero

model_parameters = {
    "1st Order": {"expression": r'$\frac{K}{\tau s + 1}$', 
                  "system": lambda K, tau: lti([K], [tau, 1])},
    "2nd Order (Overdamped)": {"expression": r'$\frac{K}{(\tau_{1}s+1)(\tau_{2}s+1)}$', 
                               "system": lambda K, tau1, tau2: lti([K], [tau1 * tau2, tau1 + tau2, 1])},
    "2nd Order (General)": {"expression": r'$\frac{K}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                            "system": lambda K, tau, zeta: lti([K], [tau**2, 2*zeta*tau, 1])},
    "2nd Order (Unstable Zero)": {"expression": r'$\frac{K(-\beta s + 1)}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                                  "system": lambda K, tau, zeta, beta: lti([-K*beta, K], [tau**2, 2*zeta*tau, 1])},
    "Integrator": {"expression": r'$\frac{K}{s}$', 
                   "system": lambda K: lti([K], [1, 0])},
    "1st Order with Integrator": {"expression": r'$\frac{K}{s(\tau s + 1)}$', 
                                  "system": lambda K, tau: lti([K], [tau, 1, 0])},
    "FOPTD (Taylor Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$', 
                               "system": lambda K, tau, theta: lti([-K*theta, K], [tau, 1])},  # Approximate delay with Taylor series
    "FOPTD (Padé Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$', 
                             "system": lambda K, tau, theta: lti([-K*theta/2, K], [tau*theta/2, tau+theta/2, 1])},  # Approximate delay with Padé approximation
    "SOPTD (Overdamped, Stable Zero)": {"expression": r'$\frac{K(\tau_{3}s+1)e^{-\theta s}}{(\tau_{1}s+1)(\tau_{2}s+1)}$', 
                                        "system": lambda K, tau1, tau2, tau3, theta: lti([K*tau3, K], [tau1*tau2, tau1+tau2, 1])},  # Approximate delay with Taylor series
    "SOPTD (General, Stable Zero)": {"expression": r'$\frac{K(\tau_{3}s+1)e^{-\theta s}}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                                     "system": lambda K, tau, zeta, tau3, theta: lti([K*tau3, K], [tau**2, 2*zeta*tau, 1])},  # Approximate delay with Taylor series
    "SOPTD (Overdamped, Unstable Zero)": {"expression": r'$\frac{K(-\tau_{3}s+1)e^{-\theta s}}{(\tau_{1}s+1)(\tau_{2}s+1)}$', 
                                          "system": lambda K, tau1, tau2, tau3, theta: lti([-K*tau3, K], [tau1*tau2, tau1+tau2, 1])},  # Approximate delay with Taylor series
    "SOPTD (General, Unstable Zero)": {"expression": r'$\frac{K(-\tau_{3}s+1)e^{-\theta s}}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                                       "system": lambda K, tau, zeta, tau3, theta: lti([-K*tau3, K], [tau**2, 2*zeta*tau, 1])},  # Approximate delay with Taylor series
    "Integrator with Delay (Taylor Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{s}$', 
                                               "system": lambda K, theta: lti([-K*theta, K], [1, 0])},  # Approximate delay with Taylor series
    "Integrator with Delay (Padé Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{s}$', 
                                             "system": lambda K, theta: lti([-K*theta/2, K], [K*theta/2, K, 0])},  # Approximate delay with Padé approximation
    "1st Order with Integrator and Delay": {"expression": r'$\frac{Ke^{-\theta s}}{s(\tau s + 1)}$', 
                                            "system": lambda K, tau, theta: lti([K], [tau, 1, 0])}  # Approximate delay with Taylor series
}

# The rest of your code remains unchanged
layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='model-dropdown',
            options=[{'label': model, 'value': model} for model in model_parameters.keys()],
            placeholder="Select a model",
            style={
                'width': '100%',  # Full width within its container
                'min-width': '350px',  # Minimum width to prevent shrinking
                'max-width': '350px',  # Maximum width to prevent expanding
                'color': 'black'
            }
        ),
        html.Div(id='sliders-container')  # Container for sliders
    ], style={'width': '30%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top'}),  # Left container with dropdown menu and sliders
    
    html.Div([
        dcc.Markdown(id='model-expression', style={'margin-bottom': '10px', 'color': 'white'}, mathjax=True),
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
        dcc.Graph(id='response-graph', style={'display': 'none'}),  # Graph for system response
    ], style={'width': '60%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top', 'text-align': 'center'})  # Right container for graph
], style={'display': 'flex', 'width': '100%'})  # Set the main container to use flexbox and take up 100% width

@callback(
    [Output('model-expression', 'children'),
     Output('response-graph', 'figure'),
     Output('response-graph', 'style')],
    [Input('model-dropdown', 'value'),
     Input({'type': 'slider', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def display_model_details(selected_model, slider_values):
    if selected_model is None:
        # Hide the graph if no model is selected
        return [None, go.Figure(), {'display': 'none'}]

    # Retrieve model information
    model_info = model_parameters[selected_model]

    # Extract dynamically generated slider IDs
    slider_ids = [param for param in model_info['system'].__code__.co_varnames] + ['tauc']

    # Ensure slider_values and slider_ids match
    if len(slider_values) != len(slider_ids):
        # Assign default values if sliders haven't been initialized
        default_values = {
            'K': 1, 'tau': 3, 'tau1': 2, 'tau2': 1, 'zeta': 0.7, 'tau3': 0.5, 'beta': 0.1,
            'theta': 0.2, 'tauc': 1
        }
        slider_values = [default_values[param] for param in slider_ids]

    # Map slider values to their respective IDs
    slider_values_dict = {slider_ids[i]: slider_values[i] for i in range(len(slider_values))}

    # Ensure all required arguments are present
    required_args = {**slider_values_dict}

    def get_args(func):
        """Extract arguments required by the function from slider_values_dict."""
        return {arg: required_args[arg] for arg in func.__code__.co_varnames if arg in required_args}

    # Extract arguments for each parameter calculation
    system_args = get_args(model_info['system'])

    # Generate system transfer function
    system = model_info['system'](**system_args)

    # Simulate the system with step response
    t = np.linspace(0, 30, 200)
    u = np.ones_like(t)  # Default step input signal

    # Apply time delay only to specific models
    models_with_delay = [
        "SOPTD (Overdamped, Stable Zero)",
        "SOPTD (General, Stable Zero)",
        "SOPTD (Overdamped, Unstable Zero)",
        "SOPTD (General, Unstable Zero)",
        "1st Order with Integrator and Delay"
    ]
    if selected_model in models_with_delay and 'theta' in system_args:
        u = apply_time_delay(t, u, system_args['theta'])

    t, y = step(system, T=t)

    # Create the response graph
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=t, y=y, mode='lines', name='Output'))
    figure.add_trace(go.Scatter(x=t, y=u, mode='lines', name='Input', line=dict(dash='dash')))
    figure.update_layout(
        title=f"System Response for {selected_model}",
        xaxis_title="Time",
        yaxis_title="Output",
        legend_title="Legend",
        template="plotly_dark",
        plot_bgcolor="#010131",
        paper_bgcolor="#010131",
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )

    return [
        f"Model: {model_info['expression']}",
        figure,
        {'display': 'block'}
    ]

# Add clientside callback for computing PID parameters and updating the display
clientside_callback(
    """
    function(selected_model, slider_values) {
        const model_parameters = {
            "1st Order": {
                "Kc": (K, tau, tauc) => tau / (K * tauc),
                "tauI": (tau) => tau,
                "tauD": () => 0
            },
            "2nd Order (Overdamped)": {
                "Kc": (K, tau1, tau2, tauc) => (tau1 + tau2) / (K * tauc),
                "tauI": (tau1, tau2) => tau1 + tau2,
                "tauD": (tau1, tau2) => (tau1 * tau2) / (tau1 + tau2)
            },
            "2nd Order (General)": {
                "Kc": (K, tau, zeta, tauc) => (2 * zeta * tau) / (K * tauc),
                "tauI": (tau, zeta) => 2 * zeta * tau,
                "tauD": (tau, zeta) => tau / (2 * zeta + 1e-9)
            },
            "2nd Order (Unstable Zero)": {
                "Kc": (K, tau, zeta, beta, tauc) => (2 * zeta * tau) / (K * (tauc + beta)),
                "tauI": (tau, zeta) => 2 * zeta * tau,
                "tauD": (tau, zeta) => tau / (2 * zeta + 1e-9)
            },
            "Integrator": {
                "Kc": (K, tauc) => 2 / (K * tauc),
                "tauI": (tauc) => 2 * tauc,
                "tauD": () => 0
            },
            "1st Order with Integrator": {
                "Kc": (K, tau, tauc) => (2 * tau + tauc) / (K * tauc**2),
                "tauI": (tau, tauc) => (2 * tauc + tau),
                "tauD": (tau, tauc) => 2 * tauc * tau / (2 * tauc + tau)
            },
            "FOPTD (Taylor Approx.)": {
                "Kc": (K, tau, theta, tauc) => tau / (K * (tauc + theta)),
                "tauI": (tau) => tau,
                "tauD": () => 0
            },
            "FOPTD (Padé Approx.)": {
                "Kc": (K, tau, theta, tauc) => (tau + theta / 2) / (K * (tauc + theta / 2)),
                "tauI": (tau, theta) => tau + theta / 2,
                "tauD": (tau, theta) => tau * theta / (2 * tau + theta)
            },
            "SOPTD (Overdamped, Stable Zero)": {
                "Kc": (K, tau1, tau2, tau3, theta, tauc) => (tau1 + tau2 - tau3) / (K * (tauc + theta)),
                "tauI": (tau1, tau2, tau3) => tau1 + tau2 - tau3,
                "tauD": (tau1, tau2, tau3) => (tau1 * tau2 - (tau1 + tau2 - tau3) * tau3) / (tau1 + tau2 - tau3 + 1e-9)
            },
            "SOPTD (General, Stable Zero)": {
                "Kc": (K, tau, zeta, tau3, theta, tauc) => (2 * zeta * tau - tau3) / (K * (tauc + theta)),
                "tauI": (tau, zeta, tau3) => 2 * zeta * tau - tau3,
                "tauD": (tau, tau3, zeta) => (tau**2 - (2 * zeta * tau - tau3) * tau3) / (2 * zeta * tau - tau3 + 1e-9)
            },
            "SOPTD (Overdamped, Unstable Zero)": {
                "Kc": (K, tau1, tau2, tau3, theta, tauc) => (tau1 + tau2 + tau3 * theta / (tauc + tau3 + theta)) / (K * (tauc + tau3 + theta)),
                "tauI": (tau1, tau2, tau3, theta, tauc) => (tau1 + tau2 + tau3 * theta / (tauc + tau3 + theta)),
                "tauD": (tau1, tau2, tau3, theta, tauc) => tau3 * theta / (tauc + tau3 + theta) + tau1 * tau2 / (tau1 + tau2 + tau3 * theta / (tauc + tau3 + theta) + 1e-9)
            },
            "SOPTD (General, Unstable Zero)": {
                "Kc": (K, tau, zeta, tau3, theta, tauc) => (2 * zeta * tau + tau3 * theta / (tauc + tau3 + theta)) / (K * (tauc + tau3 + theta)),
                "tauI": (tau, zeta, tau3, theta, tauc) => (2 * zeta * tau + tau3 * theta / (tauc + tau3 + theta)),
                "tauD": (tau, zeta, tau3, theta, tauc) => tau3 * theta / (tauc + tau3 + theta) + tau**2 / (2 * zeta * tau + tau3 * theta / (tauc + tau3 + theta) + 1e-9)
            },
            "Integrator with Delay (Taylor Approx.)": {
                "Kc": (K, tauc, theta) => (2 * tauc + theta) / (K * (tauc + theta)**2),
                "tauI": (tauc, theta) => 2 * tauc + theta,
                "tauD": () => 0
            },
            "Integrator with Delay (Padé Approx.)": {
                "Kc": (K, tauc, theta) => (2 * tauc + theta) / (K * (tauc + theta / 2)**2),
                "tauI": (tauc, theta) => 2 * tauc + theta,
                "tauD": (tauc, theta) => (tauc * theta + theta**2 / 4) / (2 * tauc + theta)
            },
            "1st Order with Integrator and Delay": {
                "Kc": (K, tau, tauc, theta) => (2 * tauc + tau + theta) / (K * (tauc + theta)**2),
                "tauI": (tau, tauc, theta) => 2 * tauc + tau + theta,
                "tauD": (tau, tauc, theta) => (2 * tauc + theta) * tau / (2 * tauc + tau + theta)
            }
        };

        const params = model_parameters[selected_model];
        if (!params) {
            return ["", "", ""];
        }

        const [K, tau, tau1, tau2, zeta, tau3, beta, theta, tauc] = slider_values;

        const Kc = params.Kc(K || 0, tau || 0, tau1 || 0, tau2 || 0, zeta || 0, tau3 || 0, beta || 0, theta || 0, tauc || 0);
        const tauI = params.tauI(tau || 0, tau1 || 0, tau2 || 0, zeta || 0, tau3 || 0, beta || 0, theta || 0, tauc || 0);
        const tauD = params.tauD(tau || 0, tau1 || 0, tau2 || 0, zeta || 0, tau3 || 0, beta || 0, theta || 0, tauc || 0);

        const tauD_display = tauD > 10000000 ? "∞" : tauD.toFixed(3);

        return [
            `${Kc.toFixed(3)}`,
            `${tauI.toFixed(3)}`,
            `${tauD_display}`
        ];
    }
    """,
    [Output('model-Kc', 'children'),
     Output('model-tauI', 'children'),
     Output('model-tauD', 'children')],
    [Input('model-dropdown', 'value'),
     Input({'type': 'slider', 'index': ALL}, 'value')],
    prevent_initial_call=True
)

# Update the update_sliders function to use the updated param_labels
@callback(
    [Output('sliders-container', 'children', allow_duplicate=True)],
    [Input('model-dropdown', 'value')],
    prevent_initial_call=True
)
def update_sliders(selected_model):
    if selected_model is None:
        raise PreventUpdate

    model_info = model_parameters[selected_model]
    sliders = []

    # Define min, max, and step values for each parameter
    slider_limits = {
        'K': {'min': 1, 'max': 10, 'step': 1},
        'tau': {'min': 1, 'max': 10, 'step': 1},
        'tau1': {'min': 1, 'max': 10, 'step': 1},
        'tau2': {'min': 1, 'max': 10, 'step': 1},
        'zeta': {'min': 0, 'max': 2, 'step': 0.1, 'marks': {0: '0', 0.5: '0.5', 1: '1', 1.5: '1.5', 2: '2'}},
        'tau3': {'min': 1, 'max': 10, 'step': 1},
        'beta': {'min': 1, 'max': 10, 'step': 1},
        'theta': {'min': 1, 'max': 10, 'step': 1},
        'tauc': {'min': 1, 'max': 10, 'step': 1}
    }

    default_values = {
        'K': 1, 'tau': 3, 'tau1': 2, 'tau2': 1, 'zeta': 0, 'tau3': 0.5, 'beta': 0.1,
        'theta': 1, 'tauc': 1
    }

    # Parameter display names with proper symbols
    param_labels = {
        'K': 'K',
        'tau': 'τ',
        'tau1': 'τ_{1}',
        'tau2': 'τ_{2}',
        'zeta': 'ζ',
        'tau3': 'τ₃',
        'beta': 'β',
        'theta': 'θ',
        'tauc': 'τ_{c}'
    }

    for param in slider_limits:
        if param in model_info['system'].__code__.co_varnames or param == 'tauc':
            label = param_labels[param]

            slider = dcc.Slider(
                id={'type': 'slider', 'index': param},
                min=slider_limits[param]['min'],
                max=slider_limits[param]['max'],
                step=slider_limits[param]['step'],
                value=default_values[param],
                updatemode='drag'  # Ensure dynamic updates
            )

            # Add custom marks for zeta slider
            if param == 'zeta':
                slider.marks = slider_limits[param]['marks']

            sliders.append(html.Div([
                html.Div([
                    dcc.Markdown(f'${label}$:', style={'margin-right': '10px'}, mathjax=True),
                    dcc.Markdown(f"{default_values[param]:.1f}", id=f'{param}-display', style={'margin-right': '10px'}, mathjax=True)
                ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '2px'}),
                html.Div([
                    slider
                ], style={'margin-bottom': '2px'})
            ]))

    return [sliders]

# Add clientside callback for K slider display
clientside_callback(
    """
    function(K) {
        console.log('K:', K);
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
        console.log('tau:', tau);
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
        console.log('theta:', theta);
        return `${theta.toFixed(1)}`;
    }
    """,
    Output('theta-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'theta'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(tau1) {
        console.log('tau1:', tau1);
        return `${tau1.toFixed(1)}`;
    }
    """,
    Output('tau1-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'tau1'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(tau2) {
        console.log('tau2:', tau2);
        return `${tau2.toFixed(1)}`;
    }
    """,
    Output('tau2-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'tau2'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(beta) {
        console.log('beta:', beta);
        return `${beta.toFixed(1)}`;
    }
    """,
    Output('beta-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'beta'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(tauc) {
        console.log('tauc:', tauc);
        return `${tauc.toFixed(1)}`;
    }
    """,
    Output('tauc-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'tauc'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(zeta) {
        console.log('zeta:', zeta);
        return `${zeta.toFixed(1)}`;
    }
    """,
    Output('zeta-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'zeta'}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(tau3) {
        console.log('tau3:', tau3);
        return `${tau3.toFixed(1)}`;
    }
    """,
    Output('tau3-display', 'children', allow_duplicate=True),
    Input({'type': 'slider', 'index': 'tau3'}, 'value'),
    prevent_initial_call=True
)

def apply_time_delay(time, signal, theta):
    """
    Apply a time delay of theta to the input signal.
    """
    delayed_signal = np.zeros_like(signal)
    delay_steps = int(theta / (time[1] - time[0]))  # Calculate steps corresponding to the delay
    if delay_steps < len(signal):
        delayed_signal[delay_steps:] = signal[:-delay_steps]
    return delayed_signal

@callback(
    [Output('label-Kc', 'style'),
     Output('model-Kc', 'style'),
     Output('label-tauI', 'style'),
     Output('model-tauI', 'style'),
     Output('label-tauD', 'style'),
     Output('model-tauD', 'style')],
    [Input('model-dropdown', 'value')],
    prevent_initial_call=True
)
def update_label_visibility(selected_model):
    if selected_model is None:
        raise PreventUpdate

    return [{'margin-bottom': '10px', 'color': 'white', 'display': 'block'}] * 6