import regex as re
from dash import html, dcc, Input, Output, callback
import dash

dash.register_page(__name__, path='/latex-converter', name="LaTeX Converter")

# Allow one level of nested braces by using a non‑capturing group.
# def replace_fraction(expr):
#     pattern = r'\\frac\s*\{((?:[^{}]+|{[^{}]+})+)\}\s*\{((?:[^{}]+|{[^{}]+})+)\}'
#     new_expr, count = re.subn(pattern, r'(\1)/(\2)', expr)
#     return new_expr, count > 0

# def fully_replace_frac(expr):
#     changed = True
#     while changed:
#         expr, changed = replace_fraction(expr)
#     return expr

def replace_frac_manually(expr: str) -> str:
    # Find the first occurrence of "\frac"
    idx = expr.find(r'\frac')
    if idx == -1:
        return expr  # No fraction found, return as-is.
    
    # Find the numerator: first '{' after "\frac"
    start_num = expr.find('{', idx)
    if start_num == -1:
        return expr  # Malformed fraction.
    stack = []
    i = start_num
    while i < len(expr):
        if expr[i] == '{':
            stack.append(i)
        elif expr[i] == '}':
            stack.pop()
            if not stack:
                end_num = i
                break
        i += 1
    else:
        return expr  # Unbalanced braces.
    
    numerator = expr[start_num+1:end_num]
    
    # Find the denominator: first '{' after numerator.
    start_den = expr.find('{', end_num)
    if start_den == -1:
        return expr  # Malformed fraction.
    stack = []
    i = start_den
    while i < len(expr):
        if expr[i] == '{':
            stack.append(i)
        elif expr[i] == '}':
            stack.pop()
            if not stack:
                end_den = i
                break
        i += 1
    else:
        return expr
    
    denominator = expr[start_den+1:end_den]
    
    # Recursively process numerator and denominator in case they contain nested fractions.
    new_num = replace_frac_manually(numerator)
    new_den = replace_frac_manually(denominator)
    
    # Build the replacement string.
    replacement = f"({new_num})/({new_den})"
    
    # Replace the whole "\frac{...}{...}" with the replacement.
    new_expr = expr[:idx] + replacement + expr[end_den+1:]
    
    # Process the new expression in case more fractions exist.
    return replace_frac_manually(new_expr)

# Now, update your fully_replace_frac function to use the manual parser:
def fully_replace_frac(expr: str) -> str:
    return replace_frac_manually(expr)

def latex2python(latex_str: str) -> str:
    expr = latex_str.strip('$')
    expr = re.sub(r'\\left', '', expr)
    expr = re.sub(r'\\right', '', expr)
    expr = fully_replace_frac(expr)
    expr = re.sub(r'\\operatorname\{([^{}]+)\}', r'\1', expr)
    expr = re.sub(r'\\?exp\(', 'e**(', expr)
    expr = re.sub(r'\\(sin|cos|tan|sinh|cosh|tanh|arcsin|arccos|arctan|arcsinh|arccosh|arctanh|log|ln)', r'\1', expr)
    expr = re.sub(r'([a-zA-Z0-9_]+)\s*\^([a-zA-Z0-9_]+)', r'\1**(\2)', expr)
    expr = re.sub(r'\\cdot\s*', '*', expr)
    expr = re.sub(r'(\S+)\s*\^\{\s*([^}]+?)\s*\}', r'\1**(\2)', expr)
    
    # Simple substitution: replace { with (, } with ), and ^ with **
    expr = expr.replace('{', '(').replace('}', ')').replace('^', '**')
    return expr

def python_to_numpy(expr: str) -> str:
    expr = re.sub(r'([0-9.]+)\*\*\(([^)]+)\)', r'np.power(\1, (\2))', expr)
    expr = re.sub(r'\be\*\*\(([^)]+)\)', r'np.exp(\1)', expr)
    expr = re.sub(r'(?<!np\.)\bln\(([^)]+)\)', r'np.log(\1)', expr)
    expr = re.sub(r'(?<!np\.)\blog\(([^)]+)\)', r'np.log10(\1)', expr)
    expr = re.sub(r'\b(sin|cos|tan|sinh|cosh|tanh|arcsin|arccos|arctan|arcsinh|arccosh|arctanh)\(([^)]+)\)', r'np.\1(\2)', expr)
    expr = re.sub(r'(\S+)\s*\^\{\s*([^}]+?)\s*\}', r'\1**(\2)', expr)
    
    # Simple substitution: replace { with (, } with ), and ^ with **
    expr = expr.replace('{', '(').replace('}', ')').replace('^', '**')
    return expr

def latex2numpy(latex_str: str) -> str:
    # First, convert to a Python-compatible expression.
    python_expr = latex2python(latex_str)
    # Then, convert that into a NumPy-compatible expression.
    numpy_expr = python_to_numpy(python_expr)
    return numpy_expr

layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.H2("LaTeX Constructor and Converter"),
    html.Link(href="https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.css", rel="stylesheet"),
    html.Div(
        [
            html.Div(
                id="mathquill-input",
                className="mathquill-field",
                style={"width": "100%", "minHeight": "100px", "border": "1px solid #ccc", "padding": "10px"}
            ),
            html.Div("Type your equation here!", className="mq-placeholder")
        ],
        style={"position": "relative", "margin": "20px"}
    ),
    html.Button("Get Expression", id="get-expression-button", n_clicks=0, style={"margin": "20px", "fontSize": "18px"}),
    html.Div(id="converted-output", style={"margin": "20px", "fontSize": "18px"}),
    dcc.Store(id="mq-latex")
])
# Re-trigger MathQuill initialization when the page is visited.
dash.clientside_callback(
    """
    function(pathname) {
         console.log("Init callback triggered, pathname:", pathname);
         if(window.initMathQuill) {
             window.initMathQuill();
         }
         return "";
    }
    """,
    Output("mq-latex", "data", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call='initial_duplicate'
)
dash.clientside_callback(
    """
    function(n_clicks) {
         console.log("Button callback triggered, n_clicks:", n_clicks);
         if (!window.mathField) {
             console.log("window.mathField not defined");
             return "";
         }
         var latexValue = window.mathField.latex();
         console.log("Returning latex:", latexValue);
         return { 'latex': latexValue, 'timestamp': new Date().getTime() };
    }
    """,
    Output("mq-latex", "data", allow_duplicate=True),
    Input("get-expression-button", "n_clicks"),
    prevent_initial_call='initial_duplicate'
)

@callback(
    Output("converted-output", "children"),
    Input("mq-latex", "data")
)
def convert_mq(store_data):
    if store_data and isinstance(store_data, dict) and "latex" in store_data:
        latex_val = store_data["latex"]
        if latex_val:
            python_expr = latex2python(latex_val)
            numpy_expr = python_to_numpy(python_expr)
            return [
                # Raw LaTeX Expression Section
                html.Div([
                    html.Div([
                        html.P("Raw LaTeX Expression:", style={
                            "display": "inline-block",
                            "margin": "0",
                            "paddingRight": "10px"
                        }),
                        dcc.Clipboard(
                            target_id="raw-code",
                            title="Copy Raw LaTeX",
                            style={
                                "display": "inline-block",
                                "cursor": "pointer",
                                "padding": "5px",
                                "verticalAlign": "middle"
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.Pre(latex_val, id="raw-code", className="converted-code", style={"margin": "0"})
                ], style={"marginBottom": "20px"}),
                # Converted Python Expression Section
                html.Div([
                    html.Div([
                        html.P("Converted Python Expression:", style={
                            "display": "inline-block",
                            "margin": "0",
                            "paddingRight": "10px"
                        }),
                        dcc.Clipboard(
                            target_id="python-code",
                            title="Copy Python Expression",
                            style={
                                "display": "inline-block",
                                "cursor": "pointer",
                                "padding": "5px",
                                "verticalAlign": "middle"
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.Code(python_expr, id="python-code", className="converted-code")
                ], style={"marginBottom": "20px"}),
                # NumPy Compatible Python Expression Section
                html.Div([
                    html.Div([
                        html.P("NumPy Compatible Python Expression:", style={
                            "display": "inline-block",
                            "margin": "0",
                            "paddingRight": "10px"
                        }),
                        dcc.Clipboard(
                            target_id="numpy-code",
                            title="Copy NumPy Expression",
                            style={
                                "display": "inline-block",
                                "cursor": "pointer",
                                "padding": "5px",
                                "verticalAlign": "middle"
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.Code(numpy_expr, id="numpy-code", className="converted-code")
                ], style={"marginBottom": "20px"})
            ]
    return ""