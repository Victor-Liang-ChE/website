# pages/page2.py
from dash import dcc, html
import dash

dash.register_page(__name__, path='/page2', name="page2")

layout = html.Div([
    html.H1("Page 2"),
    html.P("This is the content of Page 2.")
])