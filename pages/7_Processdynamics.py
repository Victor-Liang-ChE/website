from dash import Dash, html, dcc, callback, Output, Input, State, ctx, MATCH, ALL
import dash
import plotly.graph_objs as go
import numpy as np

dash.register_page(__name__, path='/processdynamics', name="Process Dynamics")

layout = html.Div([
    html.Div([
        html.Button('1st Order', id='first-order-button', className='btn btn-primary', style={'margin-right': '10px'}),
        html.Button('2nd Order', id='second-order-button', className='btn btn-secondary', style={'margin-right': '10px'})
    ], id='order-buttons', style={'margin-bottom': '20px', 'text-align': 'left'}),
    
    html.Div(id='function-buttons', style={'text-align': 'left', 'margin-bottom': '20px'}),
    
    html.Div([
        html.Div(id='sliders-container', style={'display': 'none', 'float': 'left', 'width': '25%'}),  # Increased width to 25%
        dcc.Graph(id='graph-output', style={'display': 'none', 'float': 'right', 'width': '70%'})  # Decreased width to 70%
    ], style={'display': 'flex'}),
    
    dcc.Store(id='order-store'),
    dcc.Store(id='function-store'),
    dcc.Store(id='axes-limits-store', data={'x': None, 'y': None}),  # Store for axes limits
    
    dcc.Checklist(
        id='lock-axes',
        options=[{'label': 'Lock Axes', 'value': 'lock'}],
        value=[],
        style={'margin-top': '10px'}
    )
])

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
        ]), order_store
    elif order_store == 'second':
        return html.Div([
            html.Button('Step Function', id='step-function-button', className='btn btn-info', style={'margin-right': '10px'}),
            html.Button('Ramp Function', id='ramp-function-button', className='btn btn-warning', style={'margin-right': '10px', 'background-color': 'grey', 'pointer-events': 'none'})
        ]), order_store
    return html.Div(), order_store

@callback(
    [Output('sliders-container', 'children'),
     Output('sliders-container', 'style'),
     Output('graph-output', 'style'),
     Output('function-store', 'data')],
    [Input('step-function-button', 'n_clicks'),
     Input('ramp-function-button', 'n_clicks')],
    [State('order-store', 'data')],
    prevent_initial_call=True
)
def update_sliders_visibility(step_function_clicks, ramp_function_clicks, order_store):
    ctx_triggered = ctx.triggered_id
    sliders = []
    sliders_style = {'display': 'none'}
    graph_style = {'display': 'none'}
    function_store = None

    if ctx_triggered in ['step-function-button', 'ramp-function-button']:
        sliders = [
            html.Div([
                html.Label('Gain (K):'),
                dcc.Slider(id={'type': 'slider', 'name': 'K'}, min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag')
            ], style={'margin-bottom': '10px'}),
            html.Div([
                html.Label('Magnitude (M):'),
                dcc.Slider(id={'type': 'slider', 'name': 'M'}, min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag')
            ], style={'margin-bottom': '10px'}),
            html.Div([
                html.Label('Time Constant (τ):'),
                dcc.Slider(id={'type': 'slider', 'name': 'tau'}, min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag')
            ], style={'margin-bottom': '10px'})
        ]
        sliders_style = {'display': 'block'}
        graph_style = {'display': 'block'}  # Make the graph visible when function buttons are clicked

    if order_store == 'second':
        sliders.append(
            html.Div([
                html.Label('Damping Ratio (ζ):'),
                dcc.Slider(id={'type': 'slider', 'name': 'zeta'}, min=0, max=2, step=0.01, value=1, marks={i: str(i) for i in range(3)}, updatemode='drag')
            ], style={'margin-bottom': '10px'})
        )

    if ctx_triggered == 'step-function-button':
        function_store = 'step'
    elif ctx_triggered == 'ramp-function-button':
        function_store = 'ramp'

    return sliders, sliders_style, graph_style, function_store

@callback(
    [Output('graph-output', 'figure', allow_duplicate=True),
     Output('axes-limits-store', 'data', allow_duplicate=True)],
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
        return go.Figure(), axes_limits  # Return a default figure if sliders are not ready

    # Assign values from sliders, using default values if sliders are not populated
    K = slider_values[0] if len(slider_values) > 0 else 1
    M = slider_values[1] if len(slider_values) > 1 else 1
    tau = slider_values[2] if len(slider_values) > 2 else 1
    zeta = slider_values[3] if len(slider_values) > 3 else None

    t = np.linspace(0, 5 * tau, 100)
    y = np.zeros_like(t)
    y_input = np.zeros_like(t)
    title = ''

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
            t = np.linspace(0, 10 * tau, 200)  # Extend the time range for better visibility of oscillations
            y = K * M * (1 - np.exp(-zeta * t / tau) * (np.cos(np.sqrt(1 - zeta**2) * t / tau) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(np.sqrt(1 - zeta**2) * t / tau)))
        elif zeta is not None:
            y = K * M * (1 - (1 + t / tau) * np.exp(-zeta * t / tau))
        y_input = np.full_like(t, M)
        title = 'Second Order Step Function Response'
        y_limit = None  # No specific y-limit condition provided for second order

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

    # Return the figure and updated axes limits separately
    return figure, axes_limits