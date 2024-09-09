# app.py
from dash import Dash, html, dcc
import dash
import plotly.express as px

px.defaults.template = "ggplot2"

external_css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css", ]

app = Dash(__name__, pages_folder='pages', use_pages=True, external_stylesheets=external_css)

# app.layout = html.Div([
# 	html.Br(),
# 	html.P('Welcome to My Website', className="text-dark text-center fw-bold fs-1"),
#     html.Div(children=[
# 	    dcc.Link(page['name'], href=page["relative_path"], className="btn btn-dark m-2 fs-5")\
# 			  for page in dash.page_registry.values()]
# 	),
# 	dash.page_container
# ], className="col-8 mx-auto")

app.layout = html.Div([
    html.Br(),
    html.P('Welcome to My Website', className="text-dark text-center fw-bold fs-1"),
    html.Nav([
        html.Div([
            html.Button([
                html.Span(className="navbar-toggler-icon")
            ], className="navbar-toggler", type="button", **{
                "data-bs-toggle": "collapse",
                "data-bs-target": "#navbarNav",
                "aria-controls": "navbarNav",
                "aria-expanded": "false",
                "aria-label": "Toggle navigation"
            }),
            html.Div([
                html.Ul([
                    html.Li([
                        dcc.Link(page['name'], href=page["relative_path"], className="nav-link")
                    ], className="nav-item") for page in dash.page_registry.values()
                ], className="navbar-nav me-auto")  # Changed ms-auto to me-auto to align left
            ], className="collapse navbar-collapse", id="navbarNav")
        ], className="container-fluid")
    ], className="navbar navbar-expand-lg navbar-light bg-light"),
    dash.page_container
], className="col-8 mx-auto")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
