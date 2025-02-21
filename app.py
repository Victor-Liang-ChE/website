# app.py
from dash import Dash, html, dcc, Output, Input
import dash
import plotly.express as px

px.defaults.template = "ggplot2"

external_css = ["/assets/styles.css"]
# inline scripts dont work (html.Script dosn't work, cdnjs has to be loaded here or local script has to be in assets)
external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.4/jquery.min.js", \
                    "https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.min.js"]

app = Dash(__name__, pages_folder='pages', use_pages=True, external_stylesheets=external_css, external_scripts=external_scripts,suppress_callback_exceptions=True)

navbar_pages = ['About', 'McCabe-Thiele', 'Reaction Kinetics', 'Process Dynamics', 'PID Tuning', 'Miscellaneous']
# nav bar ordering system determined by the number in the filename, e.g. 7_processdynamics.py

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
        return 'McCabe-Thiele'
    elif pathname == '/kinetics':
        return 'Kinetics'
    elif pathname == '/dropchance':
        return 'Drop Chance Calculator'
    elif pathname == '/misc':
        return 'Miscellaneous'
    elif pathname == '/menu':
        return 'Portola Menu'
    elif pathname == '/processdynamics':
        return 'Process Dynamics'
    elif pathname == '/PIDTuning':
        return 'PID Tuning'
    elif pathname == '/jplyrics':
        return 'Japanese Lyrics Analyzer'
    elif pathname == '/chemeecon':
        return 'Chemical Engineering Economics'
    elif pathname == '/latex-converter':
        return 'LaTex Converter'
    else:
        return 'My Website'

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)

# Dash is not actually running on http://0.0.0.0:8080/, its is running on localhost:8080
# Python app.py may not run if there are corrupted packages and cannot be uninstalled using 
#   pip uninstall <package>
# Try manually deleting the package and if the package is being ran somewhere, use resource monitor 
#   to end all python processes and then delete the package