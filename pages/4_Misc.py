from dash import dcc, html
import dash

dash.register_page(__name__, path='/misc', name="Miscellaneous")

layout = html.Div([
    html.Div([
        dcc.Link(html.Div("Drop Chance", className="box"), href="/dropchance"),
        dcc.Link(html.Div("Email Generator", className="box"), href="/emailgen"),
        dcc.Link(html.Div("Robinhood Autoseller", className="box"), href="/robin")
    ], className="box-container")
], className="container")