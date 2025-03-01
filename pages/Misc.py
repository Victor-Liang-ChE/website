from dash import dcc, html
import dash

dash.register_page(__name__, path='/misc', name="Miscellaneous")

layout = html.Div([
    html.Div([
        dcc.Link(html.Div("Drop Chance", className="box"), \
            href="/dropchance"),
        dcc.Link(html.Div("Japanese Lyrics Analyzer", className="box"), \
            href="/jplyrics"),
        dcc.Link(html.Div("Portola Menu", className="box"), \
            href="/menu"),
        dcc.Link(html.Div("Chemical Engineering Economics", className="box"), \
            href="/chemeecon"),
        dcc.Link(html.Div("LaTeX Constructor and Converter", className="box"), \
            href="/latex-converter"),
        dcc.Link(html.Div("Sandbox", className="box"), \
            href="/sandbox"),
    ], className="box-container", style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '10px'})
], className="container")