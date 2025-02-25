import dash
from dash import html

dash.register_page(__name__, path='/', name="About")

# URLs
warriors_logo_url = "https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg"
niners_logo_url = "https://upload.wikimedia.org/wikipedia/commons/3/3a/San_Francisco_49ers_logo.svg"
github_logo_url = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
linkedin_logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"
ucsb_logo_url = "https://upload.wikimedia.org/wikipedia/commons/d/d4/UC_Santa_Barbara_logo.svg"

# Gonna move the quirky stuff to a separate about page, this should be the page for employers lmao
sentences = [
    "I'm a Chemical Engineer. 🔧",
    html.P(["I develop ", html.B("simulations", style={
               'borderRadius': '4px',  # Rounded corners
               'fontSize': '1.2em',  # Slightly larger text
           }), " for chemical engineering concepts to solve problems more efficiently. 🤓"]),
    html.P([
        "Languages and Frameworks: ",
        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg", 
                title="Python",
                style={'height': '25px', 'margin': '0 5px', 'vertical-align': 'middle'}),
        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png", 
                title="JavaScript",
                style={'height': '25px', 'margin': '0 5px', 'vertical-align': 'middle'}),
        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/6/61/HTML5_logo_and_wordmark.svg", 
                title="HTML5",
                style={'height': '30px', 'margin': '0 5px', 'vertical-align': 'middle'}),
        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/d/d5/CSS3_logo_and_wordmark.svg", 
                title="CSS3",
                style={'height': '35px', 'margin': '0 5px', 'vertical-align': 'middle'}),
        html.Img(src="https://dash.gallery/dash-cytoscape-phylogeny/assets/dash-logo.png", 
                title="Dash",
                style={'height': '30px', 'margin': '0 5px', 'vertical-align': 'middle'})
    ]),
    "Python Packages: NumPy, SciPy, Pandas, Matplotlib, Scikit-learn, Plotly, RegEx, Control, and BeautifulSoup4. 📦",
    html.P([
        "Currently a senior at the University of California, Santa Barbara. ",
        html.Img(src=ucsb_logo_url, style={'height': '20px'})
    ]),
    "Will pursue a masters degree in materials science next year. 🎓",
    # html.P([
    #     "Big Warriors ", 
    #     html.Img(src=warriors_logo_url, style={'height': '20px'}), 
    #     " and Niners ", 
    #     html.Img(src=niners_logo_url, style={'height': '20px'}), 
    #     " fan. (Cowboys suck ", 
    #     html.Span("💩"), 
    #     " but Lakers are cool)"
    # ]),
    # html.P(["I am a ", html.B("gamer"), ". 🎮"]), 
    "Want to contact me? victorliang@ucsb.edu 📧",
    "Under heavy construction, but take a look around! 😄"
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