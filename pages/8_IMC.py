from dash import html, dcc, Input, Output, callback, ALL
from dash.exceptions import PreventUpdate
import dash
import numpy as np
import plotly.graph_objs as go
from dash import callback_context as ctx
from scipy.signal import lti, step

dash.register_page(__name__, path='/PIDTuning', name="PID Tuning")

# Dictionary to store the associated values for each model
model_parameters = {
    "1st Order": {"expression": r'$\frac{K}{\tau s + 1}$', 
                  "Kc": lambda K, tau, tauc: tau / (K * tauc), 
                  "tauI": lambda tau: tau, 
                  "tauD": lambda: 0,
                  "system": lambda K, tau: lti([K], [tau, 1])},
    "2nd Order (Overdamped)": {"expression": r'$\frac{K}{(\tau_{1}s+1)(\tau_{2}s+1)}$', 
                               "Kc": lambda K, tau1, tau2, tauc: (tau1 + tau2) / (K * tauc), 
                               "tauI": lambda tau1, tau2: tau1 + tau2, 
                               "tauD": lambda tau1, tau2: (tau1 * tau2) / (tau1 + tau2),
                               "system": lambda K, tau1, tau2: lti([K], [tau1 * tau2, tau1 + tau2, 1])},
    "2nd Order (General)": {"expression": r'$\frac{K}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                            "Kc": lambda K, tau, zeta, tauc: (2 * zeta * tau) / (K * tauc), 
                            "tauI": lambda tau, zeta: 2 * zeta * tau, 
                            "tauD": lambda tau, zeta: tau / (2 * zeta),
                            "system": lambda K, tau, zeta: lti([K], [tau**2, 2*zeta*tau, 1])},
    "2nd Order (Unstable Zero)": {"expression": r'$\frac{K(-\beta s + 1)}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                                  "Kc": lambda K, tau, zeta, beta, tauc: (2 * zeta * tau) / (K * (tauc + beta)), 
                                  "tauI": lambda tau, zeta: 2 * zeta * tau, 
                                  "tauD": lambda tau, zeta: tau / (2 * zeta),
                                  "system": lambda K, tau, zeta, beta: lti([-K*beta, K], [tau**2, 2*zeta*tau, 1])},
    "Integrator": {"expression": r'$\frac{K}{s}$', 
                   "Kc": lambda K, tauc: 2 / (K * tauc), 
                   "tauI": lambda tauc: 2 * tauc, 
                   "tauD": lambda: 0,
                   "system": lambda K: lti([K], [1, 0])},
    "1st Order with Integrator": {"expression": r'$\frac{K}{s(\tau s + 1)}$', 
                                  "Kc": lambda K, tau, tauc: (2 * tau + tauc) / (K * tauc**2), 
                                  "tauI": lambda tau, tauc: (2 * tauc + tau), 
                                  "tauD": lambda tau, tauc: 2 * tauc * tau / (2 * tauc + tau),
                                  "system": lambda K, tau: lti([K], [tau, 1, 0])},
    "FOPTD (Taylor Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$', 
                               "Kc": lambda K, tau, theta, tauc: tau / (K * (tauc + theta)),
                               "tauI": lambda tau: tau,
                               "tauD": lambda: 0,
                               "system": lambda K, theta: lti([-K*theta, K], [1, 1])},  # Approximate delay with Taylor series
    "FOPTD (Padé Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$', 
                             "Kc": lambda K, tau, theta, tauc: (tau + theta / 2) / (K * (tauc + theta / 2)), 
                             "tauI": lambda tau, theta: tau + theta / 2, 
                             "tauD": lambda tau, theta: tau * theta / (2 * tau + theta),
                             "system": lambda K, tau, theta: lti([-K*theta/2, K], [tau*theta/2, tau+theta/2, 1])},  # Approximate delay with Padé approximation
    "SOPTD (Overdamped, Stable Zero)": {"expression": r'$\frac{K(\tau_{3}s+1)e^{-\theta s}}{(\tau_{1}s+1)(\tau_{2}s+1)}$', 
                                        "Kc": lambda K, tau1, tau2, tau3, theta, tauc: (tau1 + tau2 - tau3) / (K * (tauc + theta)), 
                                        "tauI": lambda tau1, tau2, tau3: tau1 + tau2 - tau3, 
                                        "tauD": lambda tau1, tau2, tau3: (tau1 * tau2 - (tau1 + tau2 - tau3) * tau3) / (tau1 + tau2 - tau3),
                                        "system": lambda K, tau1, tau2, tau3, theta: lti([K*tau3, K], [tau1*tau2, tau1+tau2, 1])},  # Approximate delay with Taylor series
    "SOPTD (General, Stable Zero)": {"expression": r'$\frac{K(\tau_{3}s+1)e^{-\theta s}}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                                     "Kc": lambda K, tau, zeta, tau3, theta, tauc: (2 * zeta * tau - tau3) / (K * (tauc + theta)), 
                                     "tauI": lambda tau, zeta, tau3: 2 * zeta * tau - tau3, 
                                     "tauD": lambda tau, tau3, zeta: (tau**2 - (2 * zeta * tau - tau3) * tau3) / (2 * zeta * tau - tau3),
                                     "system": lambda K, tau, zeta, tau3, theta: lti([K*tau3, K], [tau**2, 2*zeta*tau, 1])},  # Approximate delay with Taylor series
    "SOPTD (Overdamped, Unstable Zero)": {"expression": r'$\frac{K(-\tau_{3}s+1)e^{-\theta s}}{(\tau_{1}s+1)(\tau_{2}s+1)}$', 
                                          "Kc": lambda K, tau1, tau2, tau3, theta, tauc: (tau1 + tau2 + tau3 * theta / (tauc + tau3 + theta)) / (K * (tauc + tau3 + theta)), 
                                          "tauI": lambda tau1, tau2, tau3, theta, tauc: (tau1 + tau2 + tau3 * theta / (tauc + tau3 + theta)), 
                                          "tauD": lambda tau1, tau2, tau3, theta, tauc: tau3 * theta / (tauc + tau3 + theta) + tau1 * tau2 / (tau1 + tau2 + tau3 * theta / (tauc + tau3 + theta)),
                                          "system": lambda K, tau1, tau2, tau3, theta: lti([-K*tau3, K], [tau1*tau2, tau1+tau2, 1])},  # Approximate delay with Taylor series
    "SOPTD (General, Unstable Zero)": {"expression": r'$\frac{K(-\tau_{3}s+1)e^{-\theta s}}{\tau^2 s^2 + 2\zeta\tau s + 1}$', 
                                       "Kc": lambda K, tau, zeta, tau3, theta, tauc: (2 * zeta * tau + tau3 * theta / (tauc + tau3 + theta)) / (K * (tauc + tau3 + theta)), 
                                       "tauI": lambda tau, zeta, tau3, theta, tauc: (2 * zeta * tau + tau3 * theta / (tauc + tau3 + theta)), 
                                       "tauD": lambda tau, zeta, tau3, theta, tauc: tau3 * theta / (tauc + tau3 + theta) + tau**2 / (2 * zeta * tau + tau3 * theta / (tauc + tau3 + theta)),
                                       "system": lambda K, tau, zeta, tau3, theta: lti([-K*tau3, K], [tau**2, 2*zeta*tau, 1])},  # Approximate delay with Taylor series
    "Integrator with Delay (Taylor Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{s}$', 
                                               "Kc": lambda K, tauc, theta: (2 * tauc + theta) / (K * (tauc + theta)**2), 
                                               "tauI": lambda tauc, theta: 2 * tauc + theta, 
                                               "tauD": lambda: 0,
                                               "system": lambda K, theta: lti([K], [1, 0])},  # Approximate delay with Taylor series
    "Integrator with Delay (Padé Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{s}$', 
                                             "Kc": lambda K, tauc, theta: (2 * tauc + theta) / (K * (tauc + theta / 2)**2), 
                                             "tauI": lambda tauc, theta: 2 * tauc + theta,
                                             "tauD": lambda tauc, theta: (tauc * theta + theta**2 / 4) / (2 * tauc + theta),
                                             "system": lambda K, theta: lti([K, -K*theta/2], [1, theta/2, 0])},  # Approximate delay with Padé approximation
    "1st Order with Integrator and Delay": {"expression": r'$\frac{Ke^{-\theta s}}{s(\tau s + 1)}$', 
                                            "Kc": lambda K, tau, tauc, theta: (2 * tauc + tau + theta) / (K * (tauc + theta)**2), 
                                            "tauI": lambda tau, tauc, theta: 2 * tauc + tau + theta, 
                                            "tauD": lambda tau, tauc, theta: (2 * tauc + theta) * tau / (2 * tauc + tau + theta),
                                            "system": lambda K, tau, theta: lti([K], [tau, 1, 0])}  # Approximate delay with Taylor series
}

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
        dcc.Markdown(id='model-Kc', style={'margin-bottom': '10px', 'color': 'white'}, mathjax=True),
        dcc.Markdown(id='model-tauI', style={'margin-bottom': '10px', 'color': 'white'}, mathjax=True),
        dcc.Markdown(id='model-tauD', style={'margin-bottom': '10px', 'color': 'white'}, mathjax=True)
    ], style={'margin-left': '2px', 'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center', 'text-align': 'center'}),  # Div for displaying model details

    html.Div([
        dcc.Graph(id='response-graph', style={'display': 'none'}),  # Graph for system response
    ], style={'width': '60%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top', 'text-align': 'center'})  # Right container for graph
], style={'display': 'flex', 'width': '100%'})  # Set the main container to use flexbox and take up 100% width

from dash.exceptions import PreventUpdate

@callback(
    [Output('model-expression', 'children'),
     Output('model-Kc', 'children'),
     Output('model-tauI', 'children'),
     Output('model-tauD', 'children'),
     Output('response-graph', 'figure'),
     Output('response-graph', 'style')],
    [Input('model-dropdown', 'value'),
     Input({'type': 'slider', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def display_model_details(selected_model, slider_values):
    if selected_model is None:
        # Hide the graph if no model is selected
        return [None, None, None, None, go.Figure(), {'display': 'none'}]

    # Retrieve model information
    model_info = model_parameters[selected_model]

    # Extract dynamically generated slider IDs
    slider_ids = [param for param in model_info['system'].__code__.co_varnames] + ['tauc']

    # Map slider values to their respective IDs
    slider_values_dict = {slider_ids[i]: slider_values[i] for i in range(len(slider_values))}

    # Debug mapping to verify correctness
    print("Slider Mapping:", slider_values_dict)

    # Ensure all required arguments are present
    required_args = {**slider_values_dict}

    def get_args(func):
        """Extract arguments required by the function from slider_values_dict."""
        return {arg: required_args[arg] for arg in func.__code__.co_varnames if arg in required_args}

    # Extract arguments for each parameter calculation
    try:
        Kc_args = get_args(model_info['Kc'])
        tauI_args = get_args(model_info['tauI'])
        tauD_args = get_args(model_info['tauD'])
    except KeyError as e:
        raise ValueError(f"Missing parameter {e} in slider_values_dict: {slider_values_dict}")

    # Compute PID parameters
    Kc = model_info['Kc'](**Kc_args)
    tauI = model_info['tauI'](**tauI_args)
    tauD = model_info['tauD'](**tauD_args)

    # Generate system transfer function
    system_args = get_args(model_info['system'])
    system = model_info['system'](**system_args)

    # Simulate the system with step response
    t = np.linspace(0, 30, 200)
    u = np.ones_like(t)  # Default step input signal

    # Apply time delay only if the model includes `theta`
    if 'theta' in system_args:
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
        f"$K_{{c}}:$ {Kc:.3f}",
        f"$\\tau_{{I}}:$ {tauI:.3f}",
        f"$\\tau_{{D}}:$ {tauD:.3f}",
        figure,
        {'display': 'block'}
    ]

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
        'zeta': {'min': 0.1, 'max': 2, 'step': 0.1},
        'tau3': {'min': 1, 'max': 10, 'step': 1},
        'beta': {'min': 1, 'max': 10, 'step': 1},
        'theta': {'min': 1, 'max': 10, 'step': 1},
        'tauc': {'min': 1, 'max': 10, 'step': 1}
    }

    default_values = {
        'K': 1, 'tau': 3, 'tau1': 2, 'tau2': 1, 'zeta': 0.7, 'tau3': 0.5, 'beta': 0.1,
        'theta': 0.2, 'tauc': 1
    }

    for param in slider_limits:
        if param in model_info['system'].__code__.co_varnames or param == 'tauc':
            sliders.append(html.Div([
                html.Label(f'{param.capitalize()}:'),
                dcc.Slider(
                    id={'type': 'slider', 'index': param},
                    min=slider_limits[param]['min'],
                    max=slider_limits[param]['max'],
                    step=slider_limits[param]['step'],
                    value=default_values[param],
                    updatemode='drag'  # Ensure dynamic updates
                )
            ]))

    return [sliders]

def apply_time_delay(time, signal, theta):
    """
    Apply a time delay of theta to the input signal.
    """
    delayed_signal = np.zeros_like(signal)
    delay_steps = int(theta / (time[1] - time[0]))  # Calculate steps corresponding to the delay
    if delay_steps < len(signal):
        delayed_signal[delay_steps:] = signal[:-delay_steps]
    return delayed_signal
