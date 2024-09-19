# app.py
from dash import Dash, html, dcc, Output, Input
import dash
import plotly.express as px

px.defaults.template = "ggplot2"

external_css = ["/assets/styles.css"]

app = Dash(__name__, pages_folder='pages', use_pages=True, external_stylesheets=external_css)

navbar_pages = ['About', 'McCabe-Thiele Interactive Plot', 'Kinetics Graph', 'Miscellaneous']

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Br(),
    html.P(id='page-title', className="text-white text-center fw-bold fs-1"),
    html.Nav([
        html.Div([
            dcc.Link(page['name'], href=page["relative_path"], className="nav-link text-white")
            for page in dash.page_registry.values() if page['name'] in navbar_pages
        ], className="navbar bg-blue")
    ]),
    dash.page_container
], className="bg-dark-blue", style={'width': '100%', 'height': '100%', 'margin': '0', 'padding': '0'})

@app.callback(
    Output('page-title', 'children'),
    Input('url', 'pathname')
)
def update_title(pathname):
    if pathname == '/':
        return 'Victor Liang'
    elif pathname == '/mccabe':
        return 'McCabe-Thiele Interactive Plot'
    elif pathname == '/kinetics':
        return 'Kinetics'
    elif pathname == '/dropchance':
        return 'Drop Chance Calculator'
    elif pathname == '/emailgen':
        return 'Email Generator'
    elif pathname == '/robin':
        return 'Robinhood Autoseller'
    else:
        return 'My Website'

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
