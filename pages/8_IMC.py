from dash import html, dcc, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash
import numpy as np
import plotly.graph_objs as go
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
                                  "system": lambda K, tau, zeta, beta: lti([K, -K*beta], [tau**2, 2*zeta*tau, 1])},
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
                               "system": lambda K, tau, theta: lti([K], [tau, 1])},  # Approximate delay with Taylor series
    "FOPTD (Padé Approx.)": {"expression": r'$\frac{Ke^{-\theta s}}{\tau s + 1}$', 
                             "Kc": lambda K, tau, theta, tauc: (tau + theta / 2) / (K * (tauc + theta / 2)), 
                             "tauI": lambda tau, theta: tau + theta / 2, 
                             "tauD": lambda tau, theta: tau * theta / (2 * tau + theta),
                             "system": lambda K, tau, theta: lti([K, -K*theta/2], [tau, 1, theta/2])},  # Approximate delay with Padé approximation
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
    ], style={'width': '30%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top'}),  # Left container with dropdown menu
    
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

@callback(
    [Output('model-expression', 'children'),
     Output('model-Kc', 'children'),
     Output('model-tauI', 'children'),
     Output('model-tauD', 'children'),
     Output('response-graph', 'figure'),
     Output('response-graph', 'style')],  # Update the style for visibility
    [Input('model-dropdown', 'value')]
)
def display_model_details(selected_model):
    if selected_model is None:
        # Hide the graph if no model is selected
        return [None, None, None, None, go.Figure(), {'display': 'none'}]

    # Retrieve model information
    model_info = model_parameters[selected_model]
    
    # Set arbitrary values for K, tau, tauc, etc. for simulation
    K = 1  # Process gain
    tau = 3  # Time constant
    tauc = tau / 3  # Closed-loop time constant
    tau1, tau2, tau3, theta, zeta, beta = 2, 1, 0.5, 0.2, 0.7, 0.1  # Arbitrary additional parameters for some models

    # Dynamically pass arguments based on the required parameters for each lambda function
    required_args = locals()

    def get_args(func):
        return {arg: required_args[arg] for arg in func.__code__.co_varnames if arg in required_args}

    # Extract arguments for each parameter calculation
    Kc_args = get_args(model_info['Kc'])
    tauI_args = get_args(model_info['tauI'])
    tauD_args = get_args(model_info['tauD'])

    # Calculate PID parameters
    Kc = model_info['Kc'](**Kc_args)
    tauI = model_info['tauI'](**tauI_args)
    tauD = model_info['tauD'](**tauD_args)

    # Simulate system response
    system_args = get_args(model_info['system'])
    system = model_info['system'](**system_args)
    t, y = step(system, T=np.linspace(0, 20, 200))

    # Create the response graph
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=t, y=y, mode='lines', name='Output'))
    figure.add_trace(go.Scatter(x=t, y=[1] * len(t), mode='lines', name='Set Point', line=dict(dash='dash')))
    figure.update_layout(
        title=f"System Response for {selected_model}",
        xaxis_title="Time",
        yaxis_title="Output",
        legend_title="Legend",
        template="plotly_dark",  # Use a dark theme
        plot_bgcolor="#010131",  # Match website background
        paper_bgcolor="#010131",  # Match website background
        xaxis_showgrid=False,  # Remove grid
        yaxis_showgrid=False   # Remove grid
    )

    # Show the graph with updated styles
    return [
        f"Model: {model_info['expression']}",
        f"$K_{{c}}:$ {Kc:.3f}",
        f"$\\tau_{{I}}:$ {tauI:.3f}",
        f"$\\tau_{{D}}:$ {tauD:.3f}",
        figure,
        {'display': 'block'}  # Make the graph visible
    ]