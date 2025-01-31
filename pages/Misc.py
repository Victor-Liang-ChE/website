from dash import dcc, html
import dash

dash.register_page(__name__, path='/misc', name="Miscellaneous")

layout = html.Div([
    html.Div([
        dcc.Link(html.Div("Drop Chance", className="box"), href="/dropchance"),
        dcc.Link(html.Div("Portola Menu", className="box"), href="/menu"),
        dcc.Link(html.Div("Chemical Engineering Economics", className="box"), href="/chemeecon"),
    ], className="box-container")
], className="container")