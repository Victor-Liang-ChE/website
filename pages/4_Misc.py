from dash import dcc, html
import dash

dash.register_page(__name__, path='/misc', name="Miscellaneous")

layout = html.Div([
    html.H1("Placeholder"),
    html.P("Placeholder")
])