import dash
from dash import html
import random

dash.register_page(__name__, path='/', name="About")

# URLs
warriors_logo_url = "https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg"
niners_logo_url = "https://upload.wikimedia.org/wikipedia/commons/3/3a/San_Francisco_49ers_logo.svg"
github_logo_url = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
linkedin_logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"
ucsb_logo_url = "https://upload.wikimedia.org/wikipedia/commons/d/d4/UC_Santa_Barbara_logo.svg"

# List of sample sentences
sentences = [
    "I'm a Chemical Engineer. 🔧",
    html.P([
        "Currently a senior at the University of California, Santa Barbara. ",
        html.Img(src=ucsb_logo_url, style={'height': '20px'})
    ]),
    "Will pursue a masters degree in materials next year. 🎓",
    "Learned a little bit of Python and thought I could make some cool things with it. 🤓",
    html.P([
        "Big Warriors ", 
        html.Img(src=warriors_logo_url, style={'height': '20px'}), 
        " and Niners ", 
        html.Img(src=niners_logo_url, style={'height': '20px'}), 
        " fan. (Cowboys suck ", 
        html.Span("💩"), 
        " but Lakers are cool)"
    ]),
    html.P(["I am a ", html.B("gamer"), ". 🎮"]), 
    "Want to contact me? victorliang@ucsb.edu 📧",
    "Under construction, but take a look around! 😄"
]

# Define the layout
layout = html.Div([
    html.Div([html.P(sentence) for sentence in sentences]),
    html.Div([
        html.A(href="https://github.com/Victor-Liang-ChE", children=[
            html.Img(src=github_logo_url, className="logo", style={'height': '30px', 'margin-right': '10px'})
        ]),
        html.A(href="https://www.linkedin.com/in/victor-liang-567238231", children=[
            html.Img(src=linkedin_logo_url, className="logo", style={'height': '30px'})
        ])
    ], style={'margin-top': '20px'})
], style={'margin': '20px'})