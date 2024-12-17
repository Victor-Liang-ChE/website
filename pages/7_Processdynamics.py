from dash import Dash, html, dcc, callback, Output, Input, State, ctx, MATCH, ALL
import dash
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
                options=[{'label': 'Lock Axes', 'value': 'lock'}],
                value=[],
                style={'margin-top': '10px'}
            )
        ], style={'text-align': 'left', 'margin-top': '20px'})
    ], style={'width': '30%', 'padding': '10px', 'display': 'inline-block', 'vertical-align': 'top'}),  # Left container with order buttons, function buttons, sliders, and lock axes button
    
    html.Div([
        dcc.Graph(id='graph-output', style={'display': 'block', 'width': '100%', 'height': '100vh'})  # Graph width set to 100% of its container
    ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),  # Allows the graph container to expand to fill remaining space

    html.Div(id='metrics-output', style={'margin-left': '2px', 'color': 'white', 'display': 'flex', 'flex-direction': 'column', 'justify-content': 'center'}),  # Div for displaying metrics
    dcc.Store(id='order-store', data='first'),  # Set initial order to 'first'
    dcc.Store(id='function-store', data='step'),  # Set initial function to 'step'
    dcc.Store(id='axes-limits-store', data={'x': None, 'y': None})  # Store for axes limits    
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

@callback(
    [Output('K-display', 'children'),
     Output('M-display', 'children'),
     Output('tau-display', 'children')],
    [Input({'type': 'slider', 'name': 'K'}, 'value'),
     Input({'type': 'slider', 'name': 'M'}, 'value'),
     Input({'type': 'slider', 'name': 'tau'}, 'value')]
)
def update_slider_values(K, M, tau):
    return f'{K:.1f}', f'{M:.1f}', f'{tau:.1f}'

@callback(
    Output('zeta-display', 'children'),
    [Input({'type': 'slider', 'name': 'zeta'}, 'value'),
     Input('order-store', 'data')]
)
def update_slider_values_zeta(zeta, order_store):
    if order_store == 'second':
        return [f'{zeta:.2f}']
    return [dash.no_update]

@callback(
    [Output('graph-output', 'figure', allow_duplicate=True),
     Output('axes-limits-store', 'data', allow_duplicate=True),
     Output('metrics-output', 'children')],
    [Input({'type': 'slider', 'name': ALL}, 'value'),
     Input('lock-axes', 'value')],
    [State('order-store', 'data'),
     State('function-store', 'data'),
     State('axes-limits-store', 'data')],
    prevent_initial_call=True
)
def update_graph(slider_values, lock_axes, order_store, function_store, axes_limits):
    # Ensure that slider_values contains expected values; if not, assign default values
    if len(slider_values) < 3:
        return go.Figure(), axes_limits, ""  # Return a default figure if sliders are not ready

    # Assign values from sliders, using default values if sliders are not populated
    K = slider_values[0] if len(slider_values) > 0 else 1
    M = slider_values[1] if len(slider_values) > 1 else 1
    tau = slider_values[2] if len(slider_values) > 2 else 1
    zeta = slider_values[3] if len(slider_values) > 3 else None

    # Ensure zeta is set to None if not provided
    if len(slider_values) < 4:
        zeta = None

    # Determine the time range based on whether axes are locked
    if 'lock' in lock_axes and axes_limits['x'] is not None:
        t = np.linspace(axes_limits['x'][0], axes_limits['x'][1], 100)
    else:
        t = np.linspace(0, 5 * tau, 100)

    y = np.zeros_like(t)
    y_input = np.zeros_like(t)
    title = ''
    peak_time = None
    overshoot = None
    oscillation_period = None
    decay_ratio = None

    if order_store == 'first' and function_store == 'step':
        y = K * M * (1 - np.exp(-t / tau))
        y_input = np.full_like(t, M)
        title = 'First Order Step Function Response'
        y_limit = 1.1 * max(K * M, M)
    elif order_store == 'first' and function_store == 'ramp':
        y = K * M * (np.exp(-t / tau) - 1) + K * M * t
        y_input = M * t
        title = 'First Order Ramp Function Response'
        y_limit = None  # No specific y-limit condition provided for ramp
    elif order_store == 'second' and function_store == 'step':
        if zeta is not None and zeta < 1:
            t = np.linspace(0, 10 * tau, 100)  # Extend the time range for better visibility of oscillations
            y = K * M * (1 - np.exp(-zeta * t / tau) * (np.cos(np.sqrt(1 - zeta**2) * t / tau) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(np.sqrt(1 - zeta**2) * t / tau)))
            peak_time = np.pi * tau / np.sqrt(1 - zeta**2)
            overshoot = np.exp(-np.pi * zeta / np.sqrt(1 - zeta**2))
            oscillation_period = 2 * np.pi * tau / np.sqrt(1 - zeta**2)
            decay_ratio = overshoot**2
        elif zeta is not None:
            y = K * M * (1 - (1 + t / tau) * np.exp(-zeta * t / tau))
        y_input = np.full_like(t, M)
        title = 'Second Order Step Function Response'
        y_limit = 1.1 * max(K * M, M)

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=t, y=y, mode='lines', name='System Response', line=dict(color='yellow')))
    figure.add_trace(go.Scatter(x=t, y=y_input, mode='lines', name='Input', line=dict(color='red', dash='dot')))
    layout = dict(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=24, family='Merriweather Sans', color='white')
        ),
        xaxis=dict(
            title='Time',
            title_font=dict(size=24, family='Merriweather Sans', color='white'),
            tickfont=dict(size=18, family='Merriweather Sans', color='white'),
            ticks='outside',
            ticklen=5,
            tickwidth=2,
            tickcolor='white',
            gridcolor='rgba(0,0,0,0)'
        ),
        yaxis=dict(
            title='Response/Input',
            title_font=dict(size=24, family='Merriweather Sans', color='white'),
            tickfont=dict(size=18, family='Merriweather Sans', color='white'),
            ticks='outside',
            ticklen=5,
            tickwidth=2,
            tickcolor='white',
            gridcolor='rgba(0,0,0,0)'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        template='plotly_dark',
        plot_bgcolor='#010131',
        paper_bgcolor='#010131',
        autosize=False,
        width=500,
        height=500
    )

    # Apply or update axes limits based on lock-axes selection
    if 'lock' in lock_axes:
        if axes_limits['x'] is not None and axes_limits['y'] is not None:
            layout['xaxis']['range'] = axes_limits['x']
            layout['yaxis']['range'] = axes_limits['y']
    else:
        x_range = [0, 5 * tau]
        y_range = [0, y_limit] if y_limit is not None else [min(y) * 1.1, max(y) * 1.1]
        layout['xaxis']['range'] = x_range
        layout['yaxis']['range'] = y_range
        axes_limits = {'x': x_range, 'y': y_range}  # Update store with the new axes limits

    figure.update_layout(layout)

    # Create metrics text with line breaks
    if order_store == 'second':
        metrics_text = [
            html.Div(f"Peak Time: {peak_time:.2f}" if isinstance(peak_time, (int, float)) else "Peak Time: N/A"),
            html.Br(),
            html.Div(f"Overshoot: {overshoot:.2f}" if isinstance(overshoot, (int, float)) else "Overshoot: N/A"),
            html.Br(),
            html.Div(f"Oscillation Period: {oscillation_period:.2f}" if isinstance(oscillation_period, (int, float)) else "Oscillation Period: N/A"),
            html.Br(),
            html.Div(f"Decay Ratio: {decay_ratio:.2f}" if isinstance(decay_ratio, (int, float)) else "Decay Ratio: N/A")
        ]
    else:
        metrics_text = []

    # Return the figure, updated axes limits, and metrics text
    return figure, axes_limits, metrics_text