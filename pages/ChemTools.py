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
        style={"width": "100%", "marginBottom": "20px"}
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
    
    # Add reactants with plus signs between them
    for i, reactant in enumerate(parsed_reaction["reactants"]):
        if i > 0:
            eq_parts.append(" + ")  # Add plus between reactants
            
        # Add coefficient if > 1
        if reactant["coefficient"] > 1:
            eq_parts.append(str(reactant["coefficient"]))
        
        # Add formula with subscripts
        eq_parts.extend(create_formula_display(reactant["compound"]))
    
    # Add arrow
    eq_parts.append(" → ")
    
    # Add products with plus signs between them
    for i, product in enumerate(parsed_reaction["products"]):
        if i > 0:
            eq_parts.append(" + ")  # Add plus between products
            
        # Add coefficient if > 1
        if product["coefficient"] > 1:
            eq_parts.append(str(product["coefficient"]))
        
        # Add formula with subscripts
        eq_parts.extend(create_formula_display(product["compound"]))
    
    parsed_output = html.Div([
        html.H3("Parsed Reaction:"),
        html.Div(
            eq_parts,
            style={"fontSize": "1.2em", "marginBottom": "15px"}
        )
    ])
    
    # Create input fields for reactants and products
    reactants_inputs = []
    for reactant in parsed_reaction["reactants"]:
        compound = reactant["compound"]
        molar_mass = get_molar_mass(compound)
        
        reactants_inputs.append(html.Div([
            html.H4([
                "Reactant: ", 
                *create_formula_display(compound)
            ]),
            html.Div([
                html.Label(f"Molar Mass: {molar_mass:.2f} g/mol" if molar_mass else "Molar Mass: Unknown"),
                html.Div([
                    html.Div([
                        html.Label("Enter Moles:"),
                        dcc.Input(
                            id={"type": "moles-input", "compound": compound},
                            type="number",
                            placeholder="moles",
                            style={"width": "100%"}
                        ),
                    ], style={"width": "48%", "display": "inline-block", "marginRight": "4%"}),
                    html.Div([
                        html.Label("Enter Grams:"),
                        dcc.Input(
                            id={"type": "grams-input", "compound": compound},
                            type="number",
                            placeholder="grams",
                            style={"width": "100%"}
                        ),
                    ], style={"width": "48%", "display": "inline-block"}),
                ])
            ])
        ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}))
    
    products_display = []
    for product in parsed_reaction["products"]:
        compound = product["compound"]
        molar_mass = get_molar_mass(compound)
        
        products_display.append(html.Div([
            html.H4([
                "Product: ", 
                *create_formula_display(compound)
            ]),
            html.Label(f"Molar Mass: {molar_mass:.2f} g/mol" if molar_mass else "Molar Mass: Unknown")
        ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}))
    
    # Combine reactants inputs and products display
    compound_inputs = html.Div([
        dcc.Store(id='reaction-data-store', data=parsed_reaction),
        html.Div([
            html.H3("Reactants:"),
            html.Div(reactants_inputs)
        ]),
        html.Div([
            html.H3("Products:"),
            html.Div(products_display)
        ])
    ])
    
    return parsed_output, {"display": "block", "marginTop": "20px"}, compound_inputs, {"display": "block", "marginTop": "20px"}

@callback(
    Output("calculation-results", "children"),
    Input("calculate-button", "n_clicks"),
    [State("reaction-data-store", "data"),
     State({"type": "moles-input", "compound": dash.ALL}, "value"),
     State({"type": "grams-input", "compound": dash.ALL}, "value"),
     State({"type": "moles-input", "compound": dash.ALL}, "id"),
     State({"type": "grams-input", "compound": dash.ALL}, "id")],
    prevent_initial_call=True
)
def perform_calculation(n_clicks, reaction_data, moles_values, grams_values, moles_ids, grams_ids):
    if not reaction_data:
        return "No reaction data available. Please parse a reaction equation first."
    
    # Prepare input data
    input_data = {}
    
    # Process moles inputs
    for i, moles in enumerate(moles_values):
        if moles is not None:
            compound = moles_ids[i]["compound"]
            if compound not in input_data:
                input_data[compound] = {}
            input_data[compound]["moles"] = float(moles)
    
    # Process grams inputs
    for i, grams in enumerate(grams_values):
        if grams is not None:
            compound = grams_ids[i]["compound"]
            if compound not in input_data:
                input_data[compound] = {}
            input_data[compound]["grams"] = float(grams)
    
    # Add molar mass data
    for compound in input_data:
        molar_mass = get_molar_mass(compound)
        if molar_mass:
            input_data[compound]["molar_mass"] = molar_mass
    
    # Calculate stoichiometry
    results, message = calculate_stoichiometry(reaction_data, input_data)
    
    if results is None:
        return html.Div(message, style={"color": "red"})
    
    # Format results
    result_sections = []
    
    # Add limiting reactant info
    result_sections.append(html.Div([
        html.H3("Analysis Results"),
        html.P(f"Limiting Reactant: {results['limiting_reactant']}", style={"color": "white"}),
    ]))
    
    # Create table data for reactants
    reactant_rows = []
    for compound, data in results["reactants"].items():
        row = {
            "Compound": compound,
            "Initial (mol)": f"{data['initial_moles']:.4f}",
            "Used (mol)": f"{data['used_moles']:.4f}",
            "Excess (mol)": f"{data['excess_moles']:.4f}"
        }
        
        if "initial_grams" in data:
            row.update({
                "Initial (g)": f"{data['initial_grams']:.4f}",
                "Used (g)": f"{data['used_grams']:.4f}",
                "Excess (g)": f"{data['excess_grams']:.4f}"
            })
            
        reactant_rows.append(row)
    
    # Create table data for products
    product_rows = []
    for compound, data in results["products"].items():
        row = {
            "Compound": compound,
            "Produced (mol)": f"{data['produced_moles']:.4f}"
        }
        
        if "produced_grams" in data:
            row.update({
                "Produced (g)": f"{data['produced_grams']:.4f}"
            })
        
        product_rows.append(row)
    
    # Create tables for reactants and products
    reactant_columns = [
        {"name": "Compound", "id": "Compound"},
        {"name": "Initial (mol)", "id": "Initial (mol)"},
        {"name": "Used (mol)", "id": "Used (mol)"},
        {"name": "Excess (mol)", "id": "Excess (mol)"}
    ]
    
    # Add mass columns if available
    if any("initial_grams" in data for data in results["reactants"].values()):
        reactant_columns.extend([
            {"name": "Initial (g)", "id": "Initial (g)"},
            {"name": "Used (g)", "id": "Used (g)"},
            {"name": "Excess (g)", "id": "Excess (g)"}
        ])
    
    # Product columns
    product_columns = [
        {"name": "Compound", "id": "Compound"},
        {"name": "Produced (mol)", "id": "Produced (mol)"}
    ]
    
    # Add mass column if available
    if any("produced_grams" in data for data in results["products"].values()):
        product_columns.append(
            {"name": "Produced (g)", "id": "Produced (g)"}
        )
    
    # Add tables to results
    result_sections.append(html.Div([
        html.H3("Reactants"),
        dash_table.DataTable(
            data=reactant_rows,
            columns=reactant_columns,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'color': 'black'}
        )
    ]))
    
    result_sections.append(html.Div([
        html.H3("Products"),
        dash_table.DataTable(
            data=product_rows,
            columns=product_columns,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'color': 'black'}
        )
    ]))
    
    return html.Div(result_sections, style={"marginTop": "20px"})