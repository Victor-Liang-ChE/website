from dash import Dash, html, dcc, callback, Output, Input, State, ctx
import dash
import plotly.graph_objs as go
import numpy as np

dash.register_page(__name__, path='/processdynamics', name="Process Dynamics")

layout = html.Div([
    html.Div([
        html.Div(id='order-buttons', children=[
            html.Button('First Order', id='first-order-button', className='btn btn-primary', style={'margin-right': '10px'}),
            html.Button('Second Order', id='second-order-button', className='btn btn-secondary')
        ], style={'margin-bottom': '20px', 'text-align': 'left'}),
        
        html.Div(id='function-buttons', children=[
            html.Div(id='step-function-container', children=[
                html.Div('↓', id='step-function-arrow', style={'display': 'none', 'color': 'white', 'font-size': '20px'}),
                html.Button('Step Function', id='step-function-button', className='btn btn-info', style={'margin-right': '10px', 'display': 'none'})
            ], style={'display': 'inline-block', 'text-align': 'left'}),
            
            html.Div(id='ramp-function-container', children=[
                html.Div('↓', id='ramp-function-arrow', style={'display': 'none', 'color': 'white', 'font-size': '20px'}),
                html.Button('Ramp Function', id='ramp-function-button', className='btn btn-warning', style={'margin-right': '10px', 'display': 'none'})
            ], style={'display': 'inline-block', 'text-align': 'left'}),
            
            html.Button('Reset', id='reset-button', className='btn btn-danger', style={'display': 'none'})
        ], style={'text-align': 'left', 'margin-bottom': '20px'}),
        
        html.Div(id='function-output', style={'text-align': 'center', 'margin-bottom': '20px'}),
        
        html.Div(id='sliders-container', children=[
            html.Div([
                html.Label('Gain (K):', style={'display': 'inline-block', 'margin-right': '10px'}),
                html.Span(id='K-display', style={'margin-right': '10px'}),
                dcc.Slider(id='input-K', min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag', className='slider-orange')
            ], style={'margin-bottom': '10px'}),
            
            html.Div([
                html.Label('Time Constant (τ):', style={'display': 'inline-block', 'margin-right': '10px'}),
                html.Span(id='tau-display', style={'margin-right': '10px'}),
                dcc.Slider(id='input-tau', min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag', className='slider-green')
            ], style={'margin-bottom': '10px'}),
            
            html.Div([
                html.Label('Magnitude (M):', style={'display': 'inline-block', 'margin-right': '10px'}),
                html.Span(id='M-display', style={'margin-right': '10px'}),
                dcc.Slider(id='input-M', min=0, max=10, step=0.1, value=1, marks={i: str(i) for i in range(11)}, updatemode='drag', className='slider-red')
            ], style={'margin-bottom': '10px'}),

            html.Div([
                html.Label('Damping Ratio (ζ):', style={'display': 'inline-block', 'margin-right': '10px'}),
                html.Span(id='zeta-display', style={'margin-right': '10px'}),
                dcc.Slider(id='input-zeta', min=0, max=2, step=0.01, value=1, marks={i: str(i) for i in range(3)}, updatemode='drag', className='slider-blue')
            ], style={'margin-bottom': '10px'})
        ], style={'display': 'none'}),
        
        html.Button('Generate Graph', id='generate-graph-button', className='btn btn-success', style={'margin-left': '0px', 'margin-top': '10px', 'display': 'none'}),
        dcc.Checklist(
            id='lock-axes',
            options=[{'label': 'Lock Axes', 'value': 'lock'}],
            value=[],
            style={'margin-top': '10px', 'display': 'none'}
        )
    ], style={'flex': '1', 'padding': '20px'}),
    
    html.Div([
        dcc.Graph(id='graph-output', style={'display': 'none', 'margin-top': '20px'})
    ], style={'flex': '2', 'padding': '20px'}),
    
    dcc.Store(id='last-order-store', data=''),
    dcc.Store(id='last-button-store', data=''),
    dcc.Store(id='axes-limits-store', data={'x': None, 'y': None}),
    html.Div(id='js-reload', style={'display': 'none'})
], style={'display': 'flex', 'justify-content': 'space-between'})

@callback(
    [Output('order-buttons', 'style'),
     Output('step-function-button', 'style'),
     Output('ramp-function-button', 'style'),
     Output('reset-button', 'style'),
     Output('generate-graph-button', 'style'),
     Output('last-order-store', 'data'),
     Output('input-zeta', 'style')],
    [Input('first-order-button', 'n_clicks'),
     Input('second-order-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')]
)
def display_function_buttons(first_order_clicks, second_order_clicks, reset_clicks):
    ctx_triggered = ctx.triggered_id
    last_order = ''
    zeta_style = {'display': 'none'}
    if ctx_triggered == 'reset-button':
        return {'display': 'flex', 'justify-content': 'left'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, last_order, zeta_style
    elif ctx_triggered == 'first-order-button':
        last_order = 'first'
        return {'display': 'none'}, {'display': 'inline-block', 'margin-right': '10px'}, {'display': 'inline-block', 'margin-right': '10px'}, {'display': 'inline-block'}, {'display': 'inline-block', 'margin-left': '0px', 'margin-top': '10px'}, last_order, zeta_style
    elif ctx_triggered == 'second-order-button':
        last_order = 'second'
        zeta_style = {'display': 'block'}
        return {'display': 'none'}, {'display': 'inline-block', 'margin-right': '10px'}, {'display': 'none'}, {'display': 'inline-block'}, {'display': 'inline-block', 'margin-left': '0px', 'margin-top': '10px'}, last_order, zeta_style
    return {'display': 'flex', 'justify-content': 'left'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, last_order, zeta_style

@callback(
    [Output('step-function-arrow', 'style'),
     Output('ramp-function-arrow', 'style'),
     Output('last-button-store', 'data'),
     Output('ramp-function-button', 'disabled')],
    [Input('step-function-button', 'n_clicks'),
     Input('ramp-function-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('last-order-store', 'data')]
)
def manage_arrows(step_function_clicks, ramp_function_clicks, reset_clicks, last_order):
    ctx_triggered = ctx.triggered_id
    step_arrow_style = {'display': 'none', 'color': 'white', 'font-size': '20px'}
    ramp_arrow_style = {'display': 'none', 'color': 'white', 'font-size': '20px'}
    last_button = ''
    ramp_disabled = False

    if ctx_triggered == 'step-function-button':
        step_arrow_style = {'display': 'block', 'color': 'white', 'font-size': '20px', 'text-align': 'center', 'margin-bottom': '5px'}
        last_button = 'step'
    elif ctx_triggered == 'ramp-function-button':
        ramp_arrow_style = {'display': 'block', 'color': 'white', 'font-size': '20px', 'text-align': 'center', 'margin-bottom': '5px'}
        last_button = 'ramp'
    elif ctx_triggered == 'reset-button':
        step_arrow_style = {'display': 'none', 'color': 'white', 'font-size': '20px'}
        ramp_arrow_style = {'display': 'none', 'color': 'white', 'font-size': '20px'}
        last_button = ''

    if last_order == 'second':
        ramp_disabled = True

    return step_arrow_style, ramp_arrow_style, last_button, ramp_disabled

@callback(
    Output('K-display', 'children'),
    Output('tau-display', 'children'),
    Output('M-display', 'children'),
    Output('zeta-display', 'children'),
    Input('input-K', 'value'),
    Input('input-tau', 'value'),
    Input('input-M', 'value'),
    Input('input-zeta', 'value')
)
def update_slider_values(K, tau, M, zeta):
    return f'{K:.1f}', f'{tau:.1f}', f'{M:.1f}', f'{zeta:.1f}'

@callback(
    [Output('graph-output', 'figure'),
     Output('graph-output', 'style'),
     Output('sliders-container', 'style'),
     Output('axes-limits-store', 'data'),
     Output('lock-axes', 'style')],
    [Input('generate-graph-button', 'n_clicks'),
     Input('input-K', 'value'),
     Input('input-tau', 'value'),
     Input('input-M', 'value'),
     Input('input-zeta', 'value'),
     Input('lock-axes', 'value')],
    [State('last-button-store', 'data'),
     State('last-order-store', 'data'),
     State('axes-limits-store', 'data')]
)
def generate_graph(n_clicks, K, tau, M, zeta, lock_axes, last_button, last_order, axes_limits):
    if not n_clicks:
        return go.Figure(), {'display': 'none'}, {'display': 'none'}, axes_limits, {'display': 'none'}

    if 'lock' in lock_axes:
        x_range = axes_limits['x']
        y_range = axes_limits['y']
    else:
        x_range = [0, 5 * tau]
        y_range = [0, K * M * 1.1]
        axes_limits = {'x': x_range, 'y': y_range}

    t = np.linspace(x_range[0], x_range[1], 100)
    y = np.zeros_like(t)  # Default value for y
    title = 'System Response'

    if last_button == 'step':
        if last_order == 'first':
            y = K * M * (1 - np.exp(-t / tau))
            title = 'First Order Step Function Response'
        elif last_order == 'second':
            y = K * M * (1 - (1 + t / tau) * np.exp(-zeta * t / tau))
            title = 'Second Order Step Function Response'
        y_input = np.full_like(t, M)
    elif last_button == 'ramp' and last_order == 'first':
        y = K * M * (np.exp(-t / tau) - 1) + K * M * t
        y_input = M * t
        title = 'First Order Ramp Function Response'
    else:
        return go.Figure(), {'display': 'none'}, {'display': 'none'}, axes_limits, {'display': 'none'}

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=t, y=y, mode='lines', name='System Response', line=dict(color='yellow')))
    figure.add_trace(go.Scatter(x=t, y=y_input, mode='lines', name='Input', line=dict(color='red', dash='dot')))
    figure.update_layout(
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
            gridcolor='rgba(0,0,0,0)',
            range=x_range
        ),
        yaxis=dict(
            title='Response / Input',
            title_font=dict(size=24, family='Merriweather Sans', color='white'),
            tickfont=dict(size=18, family='Merriweather Sans', color='white'),
            ticks='outside',
            ticklen=5,
            tickwidth=2,
            tickcolor='white',
            gridcolor='rgba(0,0,0,0)',
            range=y_range
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

    return figure, {'display': 'block'}, {'display': 'block'}, axes_limits, {'display': 'block'}