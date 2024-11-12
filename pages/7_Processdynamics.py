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
        html.Div(id='sliders-container', style={'display': 'none', 'float': 'left', 'width': '20%'}),
        dcc.Graph(id='graph-output', style={'display': 'none', 'float': 'right', 'width': '75%'})
    ], style={'display': 'flex'}),
    
    dcc.Store(id='order-store'),
    dcc.Store(id='function-store')
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
     Output('graph-output', 'figure', allow_duplicate=True),
     Output('graph-output', 'style'),
     Output('function-store', 'data')],
    [Input('step-function-button', 'n_clicks'),
     Input('ramp-function-button', 'n_clicks')],
    [State('order-store', 'data')],
    prevent_initial_call=True
)
def update_graph_and_sliders(step_function_clicks, ramp_function_clicks, order_store):
    ctx_triggered = ctx.triggered_id
    sliders = []
    figure = go.Figure()
    graph_style = {'display': 'none'}
    sliders_style = {'display': 'none'}
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
        graph_style = {'display': 'block'}

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

    return sliders, sliders_style, figure, graph_style, function_store

@callback(
    Output('graph-output', 'figure', allow_duplicate=True),
    [Input({'type': 'slider', 'name': ALL}, 'value')],
    [State('order-store', 'data'),
     State('function-store', 'data')],
    prevent_initial_call=True
)
def update_graph(slider_values, order_store, function_store):
    K = slider_values[0]
    M = slider_values[1]
    tau = slider_values[2]
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
        if zeta < 1:
            t = np.linspace(0, 10 * tau, 200)  # Extend the time range for better visibility of oscillations
            y = 1 - np.exp(-zeta * t / tau) * (np.cos(np.sqrt(1 - zeta**2) * t / tau) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(np.sqrt(1 - zeta**2) * t / tau))
        else:
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

    if y_limit is not None:
        layout['yaxis']['range'] = [0, y_limit]

    figure.update_layout(layout)

    return figure