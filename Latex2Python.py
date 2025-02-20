# #%%
# from dash import html, dcc, Input, Output, State, callback
# import dash
# import re

# dash.register_page(__name__, path='/latex-converter', name="LaTeX Converter")

# def latex2python(latex_str: str) -> str:
#     """
#     Convert a simple LaTeX arithmetic expression into Python code.
    
#     Supports:
#       - Fractions: converts '\\frac{a}{b}' to '(a)/(b)'
#       - Exponents: converts 'a^{b}' to 'a**(b)'
#       - Multiplication: converts '\\cdot' to '*'
      
#     Note: This is a basic implementation and may not handle complex expressions.
#     """
#     expr = latex_str.strip('$')
#     expr = re.sub(r'\\frac\s*{([^}]*)}\s*{([^}]*)}', r'(\1)/(\2)', expr)
#     expr = re.sub(r'([a-zA-Z0-9_]+)\s*\^{\s*([^}]*)\s*}', r'\1**(\2)', expr)
#     expr = re.sub(r'\\cdot', '*', expr)
#     return expr

# layout = html.Div([
#     html.H2("LaTeX to Python Converter"),
#     html.Div([
#         dcc.Textarea(
#             id="latex-input",
#             placeholder="Enter LaTeX expression here...",
#             style={"width": "100%", "height": "100px"}
#         ),
#     ], style={"margin": "20px"}),
#     html.Button("Convert", id="convert-button", n_clicks=0, style={"margin": "20px"}),
#     html.Div(id="converted-output", style={"margin": "20px", "fontSize": "18px"})
# ])

# @callback(
#     Output("converted-output", "children"),
#     Input("convert-button", "n_clicks"),
#     State("latex-input", "value")
# )
# def convert_latex(n_clicks, latex_value):
#     if n_clicks > 0 and latex_value:
#         converted = latex2python(latex_value)
#         return [
#             html.P("Converted Python expression:"),
#             html.Code(converted)
#         ]
#     return ""