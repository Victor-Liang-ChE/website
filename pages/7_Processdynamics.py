from dash import html, dcc, callback, Output, Input, State, ctx
import dash
import plotly.graph_objs as go
import numpy as np

dash.register_page(__name__, path='/processdynamics', name="Process Dynamics")

layout = html.Div([
    html.Div(id='order-buttons', children=[
        html.Button('First Order', id='first-order-button', className='btn btn-primary', style={'margin-right': '10px'}),
        html.Button('Second Order', id='second-order-button', className='btn btn-secondary')
    ], style={'display': 'flex', 'justify-content': 'center', 'margin-top': '20px'}),
    html.Div(id='function-buttons', children=[
        html.Div(id='step-function-container', children=[
            html.Div('↓', id='step-function-arrow', style={'display': 'none', 'color': 'white', 'font-size': '20px'}),
            html.Button('Step Function', id='step-function-button', className='btn btn-info', style={'margin-right': '10px', 'display': 'none'})
        ], style={'display': 'inline-block', 'text-align': 'center'}),
        html.Div(id='ramp-function-container', children=[
            html.Div('↓', id='ramp-function-arrow', style={'display': 'none', 'color': 'white', 'font-size': '20px'}),
            html.Button('Ramp Function', id='ramp-function-button', className='btn btn-warning', style={'margin-right': '10px', 'display': 'none'})
        ], style={'display': 'inline-block', 'text-align': 'center'}),
        html.Button('Back', id='back-button', className='btn btn-danger', style={'display': 'none'})
    ], style={'text-align': 'center', 'margin-top': '20px'}),
    html.Div(id='function-output', style={'text-align': 'center', 'margin-top': '20px'}),
    html.Div([
        dcc.Input(id='input-K', type='number', placeholder='Enter K', style={'margin-right': '10px'}),
        dcc.Input(id='input-tau', type='number', placeholder='Enter tau', style={'margin-right': '10px'}),
        dcc.Input(id='input-M', type='number', placeholder='Enter M', style={'margin-right': '10px'}),
        html.Button('Generate Graph', id='generate-graph-button', className='btn btn-success', style={'margin-left': '10px'})
    ], style={'display': 'flex', 'justify-content': 'center', 'margin-top': '20px'}),
    dcc.Graph(id='graph-output', style={'display': 'none', 'margin-top': '20px'})
])

@callback(
    [Output('order-buttons', 'style'),
     Output('step-function-button', 'style'),
     Output('ramp-function-button', 'style'),
     Output('back-button', 'style')],
    [Input('first-order-button', 'n_clicks'),
     Input('second-order-button', 'n_clicks'),
     Input('back-button', 'n_clicks')]
)
def display_function_buttons(first_order_clicks, second_order_clicks, back_clicks):
    ctx_triggered = ctx.triggered_id
    if ctx_triggered == 'back-button':
        return {'display': 'flex', 'justify-content': 'center'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    elif first_order_clicks or second_order_clicks:
        return {'display': 'none'}, {'display': 'inline-block', 'margin-right': '10px'}, {'display': 'inline-block', 'margin-right': '10px'}, {'display': 'inline-block'}
    return {'display': 'flex', 'justify-content': 'center'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

@callback(
    [Output('step-function-arrow', 'style'),
     Output('ramp-function-arrow', 'style')],
    [Input('step-function-button', 'n_clicks'),
     Input('ramp-function-button', 'n_clicks')]
)
def display_arrow(step_function_clicks, ramp_function_clicks):
    ctx_triggered = ctx.triggered_id
    step_arrow_style = {'display': 'none', 'color': 'white', 'font-size': '20px'}
    ramp_arrow_style = {'display': 'none', 'color': 'white', 'font-size': '20px'}
    if ctx_triggered == 'step-function-button':
        step_arrow_style = {'display': 'block', 'color': 'white', 'font-size': '20px', 'text-align': 'center', 'margin-bottom': '5px'}
    elif ctx_triggered == 'ramp-function-button':
        ramp_arrow_style = {'display': 'block', 'color': 'white', 'font-size': '20px', 'text-align': 'center', 'margin-bottom': '5px'}

    return step_arrow_style, ramp_arrow_style

@callback(
    [Output('graph-output', 'figure'),
     Output('graph-output', 'style')],
    [Input('generate-graph-button', 'n_clicks')],
    [State('step-function-button', 'n_clicks'),
     State('ramp-function-button', 'n_clicks'),
     State('input-K', 'value'),
     State('input-tau', 'value'),
     State('input-M', 'value')]
)
def generate_graph(n_clicks, step_function_clicks, ramp_function_clicks, K, tau, M):
    if not n_clicks:
        return go.Figure(), {'display': 'none'}

    t = np.linspace(0, 10, 100)
    if step_function_clicks:
        y = K * M * (1 - np.exp(-t / tau))
        title = 'First Order Step Function Response'
    elif ramp_function_clicks:
        y = K * M * (np.exp(-t / tau) - 1) + K * M * t
        title = 'First Order Ramp Function Response'
    else:
        return go.Figure(), {'display': 'none'}

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=t, y=y, mode='lines', name='y vs. t'))
    figure.update_layout(title=title, xaxis_title='Time (t)', yaxis_title='Response (y)')

    return figure, {'display': 'block'}