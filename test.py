import dash
from dash import Input, Output, html, dcc, Patch
import plotly.graph_objects as go
import numpy as np

# generate some data
TRACES = 7
DATAPOINTS = 10
COLORS = [['darkgreen', 'gold'][c % 2] for c in range(DATAPOINTS)]

# create figure
figure = go.Figure(layout={'width': 1000, 'height': 800})
for idx in range(TRACES):
    figure.add_scatter(
        x=np.arange(DATAPOINTS),
        y=np.arange(DATAPOINTS) + 10*idx,
        mode='markers',
        marker={'color': 'crimson', 'size': 10},
        name=idx
    )

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.Div(
            [
                dcc.Dropdown(id='drop_post', options=[*range(TRACES)]),
                dcc.Dropdown(id='drop_post_2', options=[*range(TRACES)]),
            ],
            style={'width': '10%'}
        ),
        html.Div([
            dcc.Graph(
                id='graph_post',
                figure=figure,
            )
        ]),
    ]
)


@app.callback(
    Output('graph_post', 'figure', allow_duplicate=True),   # <-- allow component property
    Input('drop_post', 'value'),                            #     to be updated from different
    prevent_initial_call=True                               #     callbacks
)
def new(i):
    # Creating a Patch object
    patched_figure = Patch()

    # update all marker colors for selected trace index (drop down selection)
    patched_figure["data"][i].update({"marker": {'color': 'darkblue', 'size': 20}})
    return patched_figure


@app.callback(
    Output('graph_post', 'figure'),
    Input('drop_post_2', 'value'),
    prevent_initial_call=True
)
def update(j):
    # Creating a Patch object
    patched_figure = Patch()

    # update single marker colors with list of colors
    patched_figure["data"][j].update({"marker": {'color': COLORS, 'size': 20}})
    return patched_figure


if __name__ == '__main__':
    app.run(debug=True, port=8051)