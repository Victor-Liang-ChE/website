# # pages/page1.py
# from dash import dcc, html
# from dash.dependencies import Input, Output
# from app import app
# from McCabePlotly import mccabeint
# import numpy as np

# layout = html.Div([
#     html.H1("McCabe-Thiele Method Plot - Page 1"),
#     dcc.Graph(id='mccabe-plot-page1'),
#     html.Label('Distillate composition (xd):'),
#     dcc.Slider(id='xd-slider-page1', 
#                min=0, 
#                max=1, 
#                step=0.01, 
#                value=0.9, 
#                marks={i: str(round(i, 1)) for i in np.arange(0, 1.1, 0.1)}, 
#                updatemode='drag'),
#     html.Label('Bottoms composition (xb):'),
#     dcc.Slider(id='xb-slider-page1', 
#                min=0, 
#                max=1, 
#                step=0.01, 
#                value=0.1, 
#                marks={i: str(round(i, 1)) for i in np.arange(0, 1.1, 0.1)}, 
#                updatemode='drag'),
#     html.Label('Feed composition (xf):'),
#     dcc.Slider(id='xf-slider-page1', 
#                min=0, 
#                max=1, 
#                step=0.01, 
#                value=0.5, 
#                marks={i: str(round(i, 1)) for i in np.arange(0, 1.1, 0.1)}, 
#                updatemode='drag'),
#     html.Label('Feed quality (q):'),
#     dcc.Slider(id='q-slider-page1', 
#                min=-2, 
#                max=2, 
#                step=0.1, 
#                value=0.5, 
#                marks={i: str(round(i, 1)) for i in np.arange(-2, 2.1, 0.2)}, 
#                updatemode='drag'),
#     html.Label('Reflux ratio (R):'),
#     dcc.Slider(id='R-slider-page1', 
#                min=0, 
#                max=10, 
#                step=0.1, 
#                value=2, 
#                marks={i: str(round(i, 1)) for i in np.arange(0, 10.1, 0.5)}, 
#                updatemode='drag')
# ])

# @app.callback(
#     Output('mccabe-plot-page1', 'figure'),
#     Input('xd-slider-page1', 'value'),
#     Input('xb-slider-page1', 'value'),
#     Input('xf-slider-page1', 'value'),
#     Input('q-slider-page1', 'value'),
#     Input('R-slider-page1', 'value')
# )
# def update_plot(xd, xb, xf, q, R):
#     return mccabeint(comp1='methanol', comp2='water', T=300, xd=xd, xb=xb, xf=xf, q=q, R=R)