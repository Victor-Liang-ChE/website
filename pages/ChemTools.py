from dash import html, dcc, callback, Output, Input, State, dash_table, clientside_callback
import dash
import thermo
import re
import pandas as pd
from sympy import symbols, Eq, solve, Symbol
import numpy as np
from dash.exceptions import PreventUpdate

dash.register_page(__name__, path='/chemtools', name="Chemistry Tools")

# Function to format chemical formulas with subscripts for display
def format_chemical_formula_components(formula):
    """Convert a chemical formula into a list of components (regular text and subscripts)
    Returns a list of tuples where each tuple is ('text', is_subscript)
    For example, H2O would return [('H', False), ('2', True), ('O', False)]
    """
    # First, handle the case where there's a leading coefficient (like 2H2O)
    leading_coef_match = re.match(r'^(\d+)([A-Za-z(].*)', formula)
    coefficient = ""
    chemical_part = formula
    
    if leading_coef_match:
        coefficient = leading_coef_match.group(1)
        chemical_part = leading_coef_match.group(2)
    
    components = []
    # Add the coefficient if it exists
    if coefficient:
        components.append((coefficient, False))
    
    # Process the chemical part
    i = 0
    while i < len(chemical_part):
        char = chemical_part[i]
        
        # Case 1: Opening parenthesis, find the matching closing and look for subscript
        if char == '(':
            # Find the closing parenthesis
            paren_depth = 1
            j = i + 1
            while j < len(chemical_part) and paren_depth > 0:
                if chemical_part[j] == '(':
                    paren_depth += 1
                elif chemical_part[j] == ')':
                    paren_depth -= 1
                j += 1
            
            # Get the content inside parentheses
            paren_content = chemical_part[i:j]
            components.append((paren_content, False))
            i = j
            
            # Check if there's a subscript after the parenthesis
            if i < len(chemical_part) and chemical_part[i].isdigit():
                subscript_start = i
                while i < len(chemical_part) and chemical_part[i].isdigit():
                    i += 1
                subscript = chemical_part[subscript_start:i]
                components.append((subscript, True))
        
        # Case 2: Letter followed by digits (e.g., H2)
        elif char.isalpha():
            components.append((char, False))
            i += 1
            
            # Check for subscripts (digits after a letter)
            if i < len(chemical_part) and chemical_part[i].isdigit():
                subscript_start = i
                while i < len(chemical_part) and chemical_part[i].isdigit():
                    i += 1
                subscript = chemical_part[subscript_start:i]
                components.append((subscript, True))
        
        # Case 3: Any other character
        else:
            components.append((char, False))
            i += 1
            
    return components

def create_formula_display(formula):
    """Create an HTML display for a chemical formula with proper subscripts"""
    components = format_chemical_formula_components(formula)
    
    result = []
    for text, is_subscript in components:
        if is_subscript:
            result.append(html.Sub(text))
        else:
            result.append(text)
    
    return result

# Function to parse chemical reaction equation
def parse_reaction_equation(equation):
    # Remove spaces and split by arrow
    parts = equation.replace(" ", "").split("->")
    if len(parts) != 2:
        return None, "Invalid reaction equation. Use format like 'A + B -> C + D'"
    
    reactants_str, products_str = parts
    
    # Split reactants and products by plus sign
    reactants = reactants_str.split("+")
    products = products_str.split("+")
    
    # Parse coefficients and compounds for reactants
    parsed_reactants = []
    for reactant in reactants:
        # Match pattern for coefficient and compound, handling complex formulas with parentheses
        match = re.match(r"^(\d*)([A-Za-z0-9()]+)$", reactant)
        if not match:
            return None, f"Invalid reactant format: {reactant}"
        coef, compound = match.groups()
        coef = int(coef) if coef else 1
        parsed_reactants.append({"compound": compound, "coefficient": coef, "display": format_chemical_formula_components(reactant)})
    
    # Parse coefficients and compounds for products
    parsed_products = []
    for product in products:
        match = re.match(r"^(\d*)([A-Za-z0-9()]+)$", product)
        if not match:
            return None, f"Invalid product format: {product}"
        coef, compound = match.groups()
        coef = int(coef) if coef else 1
        parsed_products.append({"compound": compound, "coefficient": coef, "display": format_chemical_formula_components(product)})
    
    return {
        "reactants": parsed_reactants,
        "products": parsed_products
    }, "Success"

# Function to get molar mass for a compound
def get_molar_mass(compound):
    try:
        return thermo.Chemical(compound).MW
    except Exception as e:
        return None

def calculate_stoichiometry(reaction_data, input_data):
    # Extract reactants and products data
    reactants = reaction_data["reactants"]
    products = reaction_data["products"]
    
    # Get input amounts
    reactant_amounts = {}
    for reactant in reactants:
        compound = reactant["compound"]
        if compound in input_data:
            moles = input_data[compound].get("moles")
            grams = input_data[compound].get("grams")
            molar_mass = input_data[compound].get("molar_mass")
            
            # Convert grams to moles if needed
            if moles is None and grams is not None and molar_mass is not None:
                moles = grams / molar_mass
            
            if moles is not None:
                reactant_amounts[compound] = {
                    "moles": moles,
                    "coefficient": reactant["coefficient"],
                    "moles_per_coefficient": moles / reactant["coefficient"]
                }
    
    # If fewer than two reactants have amounts, return an error
    if len(reactant_amounts) < 1:
        return None, "Please provide amount data for at least one reactant"
    
    # Find limiting reactant
    limiting_reactant = min(reactant_amounts.items(), key=lambda x: x[1]["moles_per_coefficient"])
    limiting_compound = limiting_reactant[0]
    limiting_data = limiting_reactant[1]
    
    # Calculate product amounts
    results = {
        "limiting_reactant": limiting_compound,
        "reactants": {},
        "products": {}
    }
    
    # Calculate amounts for all reactants
    for reactant in reactants:
        compound = reactant["compound"]
        coef = reactant["coefficient"]
        molar_mass = input_data.get(compound, {}).get("molar_mass", None)
        
        if compound in reactant_amounts:
            moles = reactant_amounts[compound]["moles"]
            used_moles = limiting_data["moles_per_coefficient"] * coef
            excess_moles = moles - used_moles if moles > used_moles else 0
            
            results["reactants"][compound] = {
                "initial_moles": moles,
                "used_moles": used_moles,
                "excess_moles": excess_moles,
            }
            
            if molar_mass:
                results["reactants"][compound].update({
                    "initial_grams": moles * molar_mass,
                    "used_grams": used_moles * molar_mass,
                    "excess_grams": excess_moles * molar_mass
                })
    
    # Calculate product amounts
    for product in products:
        compound = product["compound"]
        coef = product["coefficient"]
        molar_mass = input_data.get(compound, {}).get("molar_mass", None)
        
        produced_moles = limiting_data["moles_per_coefficient"] * coef
        
        results["products"][compound] = {
            "produced_moles": produced_moles
        }
        
        if molar_mass:
            results["products"][compound]["produced_grams"] = produced_moles * molar_mass
    
    return results, "Success"

# Define the layout for the stoichiometry calculator
stoichiometry_calculator = html.Div([
    html.Div([
        html.Label("Chemical Reaction Equation (e.g., '2H2 + O2 -> 2H2O'):"),
        dcc.Input(
            id="reaction-equation",
            type="text",
            placeholder="Enter balanced chemical reaction...",
            style={"width": "100%", "marginBottom": "10px"}
        ),
        html.Button("Parse Reaction", id="parse-button", n_clicks=0),
    ]),
    
    html.Div(id="reaction-parse-output"),
    html.Div(id="compound-inputs-container", style={"marginTop": "20px", "display": "none"}),
    html.Button("Calculate", id="calculate-button", n_clicks=0, style={"marginTop": "20px", "display": "none"}),
    html.Div(id="calculation-results", style={"marginTop": "20px"})
])

# Placeholder for other chemistry tools
placeholder_tool_1 = html.Div([
    html.H2("Acid-Base Equilibrium (Coming Soon)"),
    html.P("This tool will help calculate pH, pKa and equilibrium concentrations.")
])

placeholder_tool_2 = html.Div([
    html.H2("Gas Laws Calculator (Coming Soon)"),
    html.P("Tools for ideal gas law and real gas calculations.")
])

# Main layout with tabs for different chemistry tools
layout = html.Div([
    dcc.Dropdown(
        id='chem-tool-selector',
        options=[
            {'label': 'Stoichiometry Calculator', 'value': 'stoichiometry'},
            {'label': 'Acid-Base Equilibrium (Coming Soon)', 'value': 'acid-base'},
            {'label': 'Gas Laws Calculator (Coming Soon)', 'value': 'gas-laws'}
        ],
        value='stoichiometry',
        clearable=False,
        style={"width": "100%", "marginBottom": "20px", "color": "black"}
        style={"width": "100%", "marginBottom": "20px", "color": "black"}
    ),
    
    html.Div(id='chem-tool-content')
])

@callback(
    Output('chem-tool-content', 'children'),
    Input('chem-tool-selector', 'value')
)
def render_tool_content(selected_tool):
    if selected_tool == 'stoichiometry':
        return stoichiometry_calculator
    elif selected_tool == 'acid-base':
        return placeholder_tool_1
    elif selected_tool == 'gas-laws':
        return placeholder_tool_2
    else:
        return html.Div("Select a tool from the dropdown menu")

@callback(
    [
        Output("reaction-parse-output", "children"),
        Output("compound-inputs-container", "style"),
        Output("compound-inputs-container", "children"),
        Output("calculate-button", "style")
    ],
    Input("parse-button", "n_clicks"),
    State("reaction-equation", "value"),
    prevent_initial_call=True
)
def parse_reaction(n_clicks, equation):
    if not equation:
        return "Please enter a reaction equation", {"display": "none"}, None, {"display": "none"}
    
    parsed_reaction, message = parse_reaction_equation(equation)
    
    if parsed_reaction is None:
        return message, {"display": "none"}, None, {"display": "none"}
    
    # Create the formatted reaction equation display with proper pluses and arrow
    eq_parts = []
    eq_parts.append("Reaction: ")  # Add inline label
    eq_parts.append("Reaction: ")  # Add inline label
    
    # Add reactants with plus signs between them
    for i, reactant in enumerate(parsed_reaction["reactants"]):
        if i > 0:
            eq_parts.append(" + ")
            eq_parts.append(" + ")
            
        if reactant["coefficient"] > 1:
            eq_parts.append(str(reactant["coefficient"]))
        eq_parts.extend(create_formula_display(reactant["compound"]))
    
    eq_parts.append(" → ")
    
    for i, product in enumerate(parsed_reaction["products"]):
        if i > 0:
            eq_parts.append(" + ")
            eq_parts.append(" + ")
            
        if product["coefficient"] > 1:
            eq_parts.append(str(product["coefficient"]))
        eq_parts.extend(create_formula_display(product["compound"]))
    
    parsed_output = html.Div(
        eq_parts,
        style={
            "fontSize": "1.2em", 
            "marginBottom": "0px", 
            "marginTop": "20px", 
            "display": "inline-block",
            "width": "100%"
        }
    )
    parsed_output = html.Div(
        eq_parts,
        style={
            "fontSize": "1.2em", 
            "marginBottom": "0px", 
            "marginTop": "20px", 
            "display": "inline-block",
            "width": "100%"
        }
    )
    
    # Create compound boxes with input fields for reactants and products
    compound_inputs = []
    
    # Add reactants
    # Create compound boxes with input fields for reactants and products
    compound_inputs = []
    
    # Add reactants
    for reactant in parsed_reaction["reactants"]:
        compound = reactant["compound"]
        molar_mass = get_molar_mass(compound)
        
        compound_inputs.append(html.Div([
            html.Div([
                *create_formula_display(compound),
                f" ({molar_mass:.2f} g/mol)" if molar_mass else ""
            ], style={"fontSize": "1.2em", "marginBottom": "10px"}),
        compound_inputs.append(html.Div([
            html.Div([
                *create_formula_display(compound),
                f" ({molar_mass:.2f} g/mol)" if molar_mass else ""
            ], style={"fontSize": "1.2em", "marginBottom": "10px"}),
            html.Div([
                # Input boxes with results
                html.Div([
                    html.Div(style={"width": "60px"}, children=[
                        dcc.Input(
                            id={"type": "moles-input", "compound": compound},
                            type="number",
                            placeholder="moles",
                            style={"width": "60px"}
                        ),
                    ]),
                    html.Div(style={"width": "150px", "marginLeft": "10px"}, children=[
                        html.Span(" → Used: ", id={"type": "used-text-moles", "compound": compound}, style={"visibility": "hidden"}),
                        html.Span(id={"type": "used-moles", "compound": compound}, children="", style={"visibility": "hidden"}),
                    ]),
                    html.Div(style={"width": "150px"}, children=[
                        html.Span(" Excess: ", id={"type": "excess-text-moles", "compound": compound}, style={"visibility": "hidden"}),
                        html.Span(id={"type": "excess-moles", "compound": compound}, children="", style={"visibility": "hidden"}),
                    ]),
                    html.Div(style={"flex": "1"}, children=[
                        html.Span(id={"type": "limiting-indicator", "compound": compound}, 
                                children="", 
                                style={"marginLeft": "10px", "color": "red", "fontWeight": "bold", "visibility": "hidden"})
                    ])
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
                
                # Grams row
                html.Div([
                    html.Div(style={"width": "60px"}, children=[
                        dcc.Input(
                            id={"type": "grams-input", "compound": compound},
                            type="number",
                            placeholder="grams",
                            style={"width": "60px"}
                        ),
                    ]),
                    html.Div(style={"width": "150px", "marginLeft": "10px"}, children=[
                        html.Span(" → Used: ", id={"type": "used-text-grams", "compound": compound}, style={"visibility": "hidden"}),
                        html.Span(id={"type": "used-grams", "compound": compound}, children="", style={"visibility": "hidden"}),
                    ]),
                    html.Div(style={"width": "150px"}, children=[
                        html.Span(" Excess: ", id={"type": "excess-text-grams", "compound": compound}, style={"visibility": "hidden"}),
                        html.Span(id={"type": "excess-grams", "compound": compound}, children="", style={"visibility": "hidden"})
                    ])
                ], style={"display": "flex", "alignItems": "center"})
            ])
        ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}))
    
    # Add products
    # Add products
    for product in parsed_reaction["products"]:
        compound = product["compound"]
        molar_mass = get_molar_mass(compound)
        
        compound_inputs.append(html.Div([
            html.Div([
                *create_formula_display(compound),
                f" ({molar_mass:.2f} g/mol)" if molar_mass else ""
            ], style={"fontSize": "1.2em", "marginBottom": "10px"}),
            html.Div([
                html.Span("Produced: ", id={"type": "produced-text", "compound": compound}, style={"marginRight": "5px", "visibility": "hidden"}),
                html.Span(id={"type": "produced-moles", "compound": compound}, children="", style={"visibility": "hidden"}),
                html.Span(" moles ", id={"type": "produced-moles-text", "compound": compound}, style={"marginRight": "5px", "visibility": "hidden"}),
                html.Span("(", id={"type": "produced-paren1", "compound": compound}, style={"visibility": "hidden"}),
                html.Span(id={"type": "produced-grams", "compound": compound}, children="", style={"visibility": "hidden"}),
                html.Span(" grams)", id={"type": "produced-paren2", "compound": compound}, style={"visibility": "hidden"})
            ])
        compound_inputs.append(html.Div([
            html.Div([
                *create_formula_display(compound),
                f" ({molar_mass:.2f} g/mol)" if molar_mass else ""
            ], style={"fontSize": "1.2em", "marginBottom": "10px"}),
            html.Div([
                html.Span("Produced: ", id={"type": "produced-text", "compound": compound}, style={"marginRight": "5px", "visibility": "hidden"}),
                html.Span(id={"type": "produced-moles", "compound": compound}, children="", style={"visibility": "hidden"}),
                html.Span(" moles ", id={"type": "produced-moles-text", "compound": compound}, style={"marginRight": "5px", "visibility": "hidden"}),
                html.Span("(", id={"type": "produced-paren1", "compound": compound}, style={"visibility": "hidden"}),
                html.Span(id={"type": "produced-grams", "compound": compound}, children="", style={"visibility": "hidden"}),
                html.Span(" grams)", id={"type": "produced-paren2", "compound": compound}, style={"visibility": "hidden"})
            ])
        ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}))
    
    # Store data for later use
    inputs_container = html.Div([
    # Store data for later use
    inputs_container = html.Div([
        dcc.Store(id='reaction-data-store', data=parsed_reaction),
        html.Div(compound_inputs)
    ])
        html.Div(compound_inputs)
    ])
    
    return parsed_output, {"display": "block", "marginTop": "20px"}, inputs_container, {"display": "block", "marginTop": "20px"}

def html_to_markdown_subscripts(components):
    """Convert formula components to markdown format with HTML subscripts
    For example: H2O becomes H<sub>2</sub>O"""
    result = ""
    for text, is_subscript in components:
        if is_subscript:
            result += f"<sub>{text}</sub>"
        else:
            result += text
    return result
    return parsed_output, {"display": "block", "marginTop": "20px"}, inputs_container, {"display": "block", "marginTop": "20px"}

def html_to_markdown_subscripts(components):
    """Convert formula components to markdown format with HTML subscripts
    For example: H2O becomes H<sub>2</sub>O"""
    result = ""
    for text, is_subscript in components:
        if is_subscript:
            result += f"<sub>{text}</sub>"
        else:
            result += text
    return result

@callback(
    [
        Output({"type": "used-moles", "compound": dash.ALL}, "children"),
        Output({"type": "excess-moles", "compound": dash.ALL}, "children"),
        Output({"type": "used-grams", "compound": dash.ALL}, "children"),
        Output({"type": "excess-grams", "compound": dash.ALL}, "children"),
        Output({"type": "produced-moles", "compound": dash.ALL}, "children"),
        Output({"type": "produced-grams", "compound": dash.ALL}, "children"),
        Output({"type": "limiting-indicator", "compound": dash.ALL}, "children"),
        # Add new outputs for visibility
        Output({"type": "used-moles", "compound": dash.ALL}, "style"),
        Output({"type": "excess-moles", "compound": dash.ALL}, "style"),
        Output({"type": "used-grams", "compound": dash.ALL}, "style"),
        Output({"type": "excess-grams", "compound": dash.ALL}, "style"),
        Output({"type": "produced-moles", "compound": dash.ALL}, "style"),
        Output({"type": "produced-grams", "compound": dash.ALL}, "style"),
        Output({"type": "limiting-indicator", "compound": dash.ALL}, "style"),
        Output("calculation-results", "children", allow_duplicate=True),
        Output({"type": "used-text-moles", "compound": dash.ALL}, "style"),
        Output({"type": "used-text-grams", "compound": dash.ALL}, "style"),
        Output({"type": "excess-text-moles", "compound": dash.ALL}, "style"),
        Output({"type": "excess-text-grams", "compound": dash.ALL}, "style"),
        Output({"type": "produced-text", "compound": dash.ALL}, "style"),
        Output({"type": "produced-moles-text", "compound": dash.ALL}, "style"),
        Output({"type": "produced-paren1", "compound": dash.ALL}, "style"),
        Output({"type": "produced-paren2", "compound": dash.ALL}, "style"),
    ],
    [
        Output({"type": "used-moles", "compound": dash.ALL}, "children"),
        Output({"type": "excess-moles", "compound": dash.ALL}, "children"),
        Output({"type": "used-grams", "compound": dash.ALL}, "children"),
        Output({"type": "excess-grams", "compound": dash.ALL}, "children"),
        Output({"type": "produced-moles", "compound": dash.ALL}, "children"),
        Output({"type": "produced-grams", "compound": dash.ALL}, "children"),
        Output({"type": "limiting-indicator", "compound": dash.ALL}, "children"),
        # Add new outputs for visibility
        Output({"type": "used-moles", "compound": dash.ALL}, "style"),
        Output({"type": "excess-moles", "compound": dash.ALL}, "style"),
        Output({"type": "used-grams", "compound": dash.ALL}, "style"),
        Output({"type": "excess-grams", "compound": dash.ALL}, "style"),
        Output({"type": "produced-moles", "compound": dash.ALL}, "style"),
        Output({"type": "produced-grams", "compound": dash.ALL}, "style"),
        Output({"type": "limiting-indicator", "compound": dash.ALL}, "style"),
        Output("calculation-results", "children", allow_duplicate=True),
        Output({"type": "used-text-moles", "compound": dash.ALL}, "style"),
        Output({"type": "used-text-grams", "compound": dash.ALL}, "style"),
        Output({"type": "excess-text-moles", "compound": dash.ALL}, "style"),
        Output({"type": "excess-text-grams", "compound": dash.ALL}, "style"),
        Output({"type": "produced-text", "compound": dash.ALL}, "style"),
        Output({"type": "produced-moles-text", "compound": dash.ALL}, "style"),
        Output({"type": "produced-paren1", "compound": dash.ALL}, "style"),
        Output({"type": "produced-paren2", "compound": dash.ALL}, "style"),
    ],
    Input("calculate-button", "n_clicks"),
    [
        State("reaction-data-store", "data"),
        State({"type": "moles-input", "compound": dash.ALL}, "value"),
        State({"type": "grams-input", "compound": dash.ALL}, "value"),
        State({"type": "moles-input", "compound": dash.ALL}, "id"),
        State({"type": "grams-input", "compound": dash.ALL}, "id"),
        State({"type": "used-moles", "compound": dash.ALL}, "id"),
        State({"type": "excess-moles", "compound": dash.ALL}, "id"),
        State({"type": "used-grams", "compound": dash.ALL}, "id"),
        State({"type": "excess-grams", "compound": dash.ALL}, "id"),
        State({"type": "produced-moles", "compound": dash.ALL}, "id"),
        State({"type": "produced-grams", "compound": dash.ALL}, "id")
    ],
    [
        State("reaction-data-store", "data"),
        State({"type": "moles-input", "compound": dash.ALL}, "value"),
        State({"type": "grams-input", "compound": dash.ALL}, "value"),
        State({"type": "moles-input", "compound": dash.ALL}, "id"),
        State({"type": "grams-input", "compound": dash.ALL}, "id"),
        State({"type": "used-moles", "compound": dash.ALL}, "id"),
        State({"type": "excess-moles", "compound": dash.ALL}, "id"),
        State({"type": "used-grams", "compound": dash.ALL}, "id"),
        State({"type": "excess-grams", "compound": dash.ALL}, "id"),
        State({"type": "produced-moles", "compound": dash.ALL}, "id"),
        State({"type": "produced-grams", "compound": dash.ALL}, "id")
    ],
    prevent_initial_call=True
)
def update_calculation_results(
    n_clicks, reaction_data, moles_values, grams_values, 
    moles_ids, grams_ids, used_moles_ids, excess_moles_ids, 
    used_grams_ids, excess_grams_ids, produced_moles_ids, produced_grams_ids
):
def update_calculation_results(
    n_clicks, reaction_data, moles_values, grams_values, 
    moles_ids, grams_ids, used_moles_ids, excess_moles_ids, 
    used_grams_ids, excess_grams_ids, produced_moles_ids, produced_grams_ids
):
    if not reaction_data:
        raise PreventUpdate
        raise PreventUpdate
    
    # Prepare input data
    input_data = {}
    
    # Process moles inputs
    for i, moles in enumerate(moles_values):
        if moles is not None:
            compound = moles_ids[i]["compound"]
            if compound not in input_data:
                input_data[compound] = {}
            input_data[compound]["moles"] = moles
            input_data[compound]["moles"] = moles
    
    # Process grams inputs
    for i, grams in enumerate(grams_values):
        if grams is not None:
            compound = grams_ids[i]["compound"]
            if compound not in input_data:
                input_data[compound] = {}
            input_data[compound]["grams"] = grams
            input_data[compound]["grams"] = grams
    
    # Add molar mass data
    for compound in input_data:
        input_data[compound]["molar_mass"] = get_molar_mass(compound)
        input_data[compound]["molar_mass"] = get_molar_mass(compound)
    
    results, message = calculate_stoichiometry(reaction_data, input_data)
    if not results:
        # Return empty strings for all outputs if calculation fails
        empty_strings = [""] * len(used_moles_ids)
        return empty_strings, empty_strings, empty_strings, empty_strings, empty_strings, empty_strings
    
    # Find if there is a true limiting reactant
    moles_per_coef = []
    for reactant in reaction_data["reactants"]:
        compound = reactant["compound"]
        if compound in results["reactants"]:
            moles = results["reactants"][compound]["initial_moles"]
            coef = reactant["coefficient"]
            moles_per_coef.append(moles/coef)
    
    # Only mark as limiting if it's truly limiting (less moles/coef than others)
    has_limiting = len(set([round(x, 6) for x in moles_per_coef])) > 1
    
    # Process results for reactants
    used_moles_values = []
    excess_moles_values = []
    used_grams_values = []
    excess_grams_values = []
    
    # Map compounds to their results
    compound_results = {}
    if not results:
        # Return empty strings for all outputs if calculation fails
        empty_strings = [""] * len(used_moles_ids)
        return empty_strings, empty_strings, empty_strings, empty_strings, empty_strings, empty_strings
    
    # Find if there is a true limiting reactant
    moles_per_coef = []
    for reactant in reaction_data["reactants"]:
        compound = reactant["compound"]
        if compound in results["reactants"]:
            moles = results["reactants"][compound]["initial_moles"]
            coef = reactant["coefficient"]
            moles_per_coef.append(moles/coef)
    
    # Only mark as limiting if it's truly limiting (less moles/coef than others)
    has_limiting = len(set([round(x, 6) for x in moles_per_coef])) > 1
    
    # Process results for reactants
    used_moles_values = []
    excess_moles_values = []
    used_grams_values = []
    excess_grams_values = []
    
    # Map compounds to their results
    compound_results = {}
    for compound, data in results["reactants"].items():
        compound_results[compound] = {
            "used_moles": f"{data['used_moles']:.3f}",
            "excess_moles": f"{data['excess_moles']:.3f}",
            "used_grams": f"{data['used_grams']:.3f}" if "used_grams" in data else "N/A",
            "excess_grams": f"{data['excess_grams']:.3f}" if "excess_grams" in data else "N/A"
        }
    
    for cid in used_moles_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        used_moles_values.append(data.get("used_moles", ""))
    
    for cid in excess_moles_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        excess_moles_values.append(data.get("excess_moles", ""))
    
    for cid in used_grams_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        used_grams_values.append(data.get("used_grams", ""))
    
    for cid in excess_grams_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        excess_grams_values.append(data.get("excess_grams", ""))
        compound_results[compound] = {
            "used_moles": f"{data['used_moles']:.3f}",
            "excess_moles": f"{data['excess_moles']:.3f}",
            "used_grams": f"{data['used_grams']:.3f}" if "used_grams" in data else "N/A",
            "excess_grams": f"{data['excess_grams']:.3f}" if "excess_grams" in data else "N/A"
        }
    
    for cid in used_moles_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        used_moles_values.append(data.get("used_moles", ""))
    
    for cid in excess_moles_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        excess_moles_values.append(data.get("excess_moles", ""))
    
    for cid in used_grams_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        used_grams_values.append(data.get("used_grams", ""))
    
    for cid in excess_grams_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        excess_grams_values.append(data.get("excess_grams", ""))
    
    # Process results for products
    produced_moles_values = []
    produced_grams_values = []
    
    # Map product compounds to their results
    # Process results for products
    produced_moles_values = []
    produced_grams_values = []
    
    # Map product compounds to their results
    for compound, data in results["products"].items():
        molar_mass = input_data.get(compound, {}).get("molar_mass")
        if molar_mass is None:
            molar_mass = get_molar_mass(compound)
        
        produced_moles = data['produced_moles']
        produced_grams = produced_moles * molar_mass if molar_mass else None
        
        compound_results[compound] = {
            "produced_moles": f"{produced_moles:.3f}",
            "produced_grams": f"{produced_grams:.3f}" if produced_grams is not None else "N/A"
        }
    
    for cid in produced_moles_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        produced_moles_values.append(data.get("produced_moles", ""))
        
    for cid in produced_grams_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        produced_grams_values.append(data.get("produced_grams", ""))
    
    # Add limiting reactant indicators
    limiting_indicators = []
    for cid in used_moles_ids:  # Using used_moles_ids since it matches reactant order
        compound = cid["compound"]
        is_limiting = has_limiting and compound == results["limiting_reactant"]
        limiting_indicators.append("(Limiting Reactant)" if is_limiting else "")

    # Create visibility styles - need to create an array of style objects, not just one object
    visible_style = {"visibility": "visible"}
    n_reactants = len(used_moles_ids)
    n_products = len(produced_moles_ids)
    
    # Create arrays of style objects for each element
    used_moles_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    excess_moles_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    used_grams_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    excess_grams_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    produced_moles_styles = [{"visibility": "visible"} for _ in range(n_products)]
    produced_grams_styles = [{"visibility": "visible"} for _ in range(n_products)]
    limiting_indicator_styles = [{"visibility": "visible", "color": "red", "fontWeight": "bold"} for _ in range(n_reactants)]
    
    # Text styles
    used_text_moles_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    used_text_grams_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    excess_text_moles_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    excess_text_grams_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    
    # Product text styles
    produced_text_styles = [{"visibility": "visible", "marginRight": "5px"} for _ in range(n_products)]
    produced_moles_text_styles = [{"visibility": "visible", "marginRight": "5px"} for _ in range(n_products)]
    produced_paren1_styles = [{"visibility": "visible"} for _ in range(n_products)]
    produced_paren2_styles = [{"visibility": "visible"} for _ in range(n_products)]
    
    return (
        used_moles_values, 
        excess_moles_values, 
        used_grams_values, 
        excess_grams_values, 
        produced_moles_values, 
        produced_grams_values,
        limiting_indicators,
        used_moles_styles,
        excess_moles_styles,
        used_grams_styles,
        excess_grams_styles,
        produced_moles_styles,
        produced_grams_styles,
        limiting_indicator_styles,
        None,  # for allow_duplicate output
        used_text_moles_styles,
        used_text_grams_styles,
        excess_text_moles_styles,
        excess_text_grams_styles,
        produced_text_styles,
        produced_moles_text_styles,
        produced_paren1_styles,
        produced_paren2_styles
    )

@callback(
    [Output({"type": "moles-input", "compound": dash.ALL}, "disabled"),
     Output({"type": "grams-input", "compound": dash.ALL}, "disabled")],
    [Input({"type": "moles-input", "compound": dash.ALL}, "value"),
     Input({"type": "grams-input", "compound": dash.ALL}, "value")],
    prevent_initial_call=True
)
def disable_inputs(moles_values, grams_values):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    n_compounds = len(moles_values)
    moles_disabled = [False] * n_compounds
    grams_disabled = [False] * n_compounds
    
    for i in range(n_compounds):
        if moles_values[i]:
            grams_disabled[i] = True
        elif grams_values[i]:
            moles_disabled[i] = True
    
    return moles_disabled, grams_disabled
        molar_mass = input_data.get(compound, {}).get("molar_mass")
        if molar_mass is None:
            molar_mass = get_molar_mass(compound)
        
        produced_moles = data['produced_moles']
        produced_grams = produced_moles * molar_mass if molar_mass else None
        
        compound_results[compound] = {
            "produced_moles": f"{produced_moles:.3f}",
            "produced_grams": f"{produced_grams:.3f}" if produced_grams is not None else "N/A"
        }
    
    for cid in produced_moles_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        produced_moles_values.append(data.get("produced_moles", ""))
        
    for cid in produced_grams_ids:
        compound = cid["compound"]
        data = compound_results.get(compound, {})
        produced_grams_values.append(data.get("produced_grams", ""))
    
    # Add limiting reactant indicators
    limiting_indicators = []
    for cid in used_moles_ids:  # Using used_moles_ids since it matches reactant order
        compound = cid["compound"]
        is_limiting = has_limiting and compound == results["limiting_reactant"]
        limiting_indicators.append("(Limiting Reactant)" if is_limiting else "")

    # Create visibility styles - need to create an array of style objects, not just one object
    visible_style = {"visibility": "visible"}
    n_reactants = len(used_moles_ids)
    n_products = len(produced_moles_ids)
    
    # Create arrays of style objects for each element
    used_moles_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    excess_moles_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    used_grams_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    excess_grams_styles = [{"visibility": "visible"} for _ in range(n_reactants)]
    produced_moles_styles = [{"visibility": "visible"} for _ in range(n_products)]
    produced_grams_styles = [{"visibility": "visible"} for _ in range(n_products)]
    limiting_indicator_styles = [{"visibility": "visible", "color": "red", "fontWeight": "bold"} for _ in range(n_reactants)]
    
    # Text styles
    used_text_moles_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    used_text_grams_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    excess_text_moles_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    excess_text_grams_styles = [{"visibility": "visible", "marginLeft": "10px"} for _ in range(n_reactants)]
    
    # Product text styles
    produced_text_styles = [{"visibility": "visible", "marginRight": "5px"} for _ in range(n_products)]
    produced_moles_text_styles = [{"visibility": "visible", "marginRight": "5px"} for _ in range(n_products)]
    produced_paren1_styles = [{"visibility": "visible"} for _ in range(n_products)]
    produced_paren2_styles = [{"visibility": "visible"} for _ in range(n_products)]
    
    return (
        used_moles_values, 
        excess_moles_values, 
        used_grams_values, 
        excess_grams_values, 
        produced_moles_values, 
        produced_grams_values,
        limiting_indicators,
        used_moles_styles,
        excess_moles_styles,
        used_grams_styles,
        excess_grams_styles,
        produced_moles_styles,
        produced_grams_styles,
        limiting_indicator_styles,
        None,  # for allow_duplicate output
        used_text_moles_styles,
        used_text_grams_styles,
        excess_text_moles_styles,
        excess_text_grams_styles,
        produced_text_styles,
        produced_moles_text_styles,
        produced_paren1_styles,
        produced_paren2_styles
    )

@callback(
    [Output({"type": "moles-input", "compound": dash.ALL}, "disabled"),
     Output({"type": "grams-input", "compound": dash.ALL}, "disabled")],
    [Input({"type": "moles-input", "compound": dash.ALL}, "value"),
     Input({"type": "grams-input", "compound": dash.ALL}, "value")],
    prevent_initial_call=True
)
def disable_inputs(moles_values, grams_values):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    n_compounds = len(moles_values)
    moles_disabled = [False] * n_compounds
    grams_disabled = [False] * n_compounds
    
    for i in range(n_compounds):
        if moles_values[i]:
            grams_disabled[i] = True
        elif grams_values[i]:
            moles_disabled[i] = True
    
    return moles_disabled, grams_disabled