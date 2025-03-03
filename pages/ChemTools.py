from dash import html, dcc, callback, Output, Input, State, dash_table, clientside_callback
import dash
import thermo
import re
import pandas as pd
from sympy import symbols, Eq, solve, Symbol
import numpy as np
from dash.exceptions import PreventUpdate

# New imports for 3D molecular visualization
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
import pubchempy as pcp
import json

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
        if (char == '('):
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

# Functions for 3D molecular visualization
def get_smiles_from_name(name):
    """Get SMILES string directly from chemical name using PubChem"""
    try:
        compounds = pcp.get_compounds(name, 'name')
        if not compounds:
            return None, "Chemical not found in database"
        return compounds[0].canonical_smiles, compounds[0].iupac_name
    except Exception as e:
        # Check if it's a network error
        if 'urlopen error' in str(e) or 'getaddrinfo failed' in str(e):
            return None, "PubChem servers appear to be unavailable. Please try again later."
        return None, f"Error: {str(e)}"

def create_molecule_from_smiles(smiles):
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES string")
        
        mol = Chem.AddHs(mol)
        params = AllChem.ETKDGv2()
        params.randomSeed = 42
        params.clearConfs = True
        params.useSmallRingTorsions = True
        params.useBasicKnowledge = True
        
        status = AllChem.EmbedMolecule(mol, params=params)
        if (status == -1):
            status = AllChem.EmbedMolecule(mol, useRandomCoords=True, 
                                         randomSeed=42,
                                         clearConfs=True)
            
        if (status == -1):
            raise ValueError("Could not generate 3D coordinates")
            
        try:
            AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
        except Exception as force_field_error:
            try:
                AllChem.UFFOptimizeMolecule(mol, maxIters=200)
            except Exception:
                # Continue without optimization
                pass
        
        return mol, None
    except Exception as e:
        return None, str(e)

def get_element_list(mol):
    """Extract a set of unique elements in the molecule"""
    elements = set()
    if mol:
        for atom in mol.GetAtoms():
            elements.add(atom.GetSymbol())
    return sorted(list(elements))

def create_viewer_html(mol):
    if mol is None:
        return ""
        
    pdb_data = Chem.MolToPDBBlock(mol)
    pdb_data = pdb_data.replace('\\', '\\\\').replace('\n', '\\n').replace("'", "\\'")
    
    # Get list of elements in the molecule
    element_list = get_element_list(mol)
    
    # Complete JMol element color mapping
    element_colors = {
        'H': '#FFFFFF',   # White
        'He': '#D9FFFF',  # Light cyan
        'Li': '#CC80FF',  # Light purple
        'Be': '#C2FF00',  # Light green
        'B': '#FFB5B5',   # Light red
        'C': '#909090',   # Gray
        'N': '#3050F8',   # Blue
        'O': '#FF0D0D',   # Red
        'F': '#90E050',   # Light green
        'Ne': '#B3E3F5',  # Cyan
        'Na': '#AB5CF2',  # Purple
        'Mg': '#8AFF00',  # Bright green
        'Al': '#BFA6A6',  # Gray-brown
        'Si': '#F0C8A0',  # Tan
        'P': '#FF8000',   # Orange
        'S': '#FFFF30',   # Yellow
        'Cl': '#1FF01F',  # Bright green
        'Ar': '#80D1E3',  # Light blue
        'K': '#8F40D4',   # Purple
        'Ca': '#3DFF00',  # Lime green
        'Sc': '#E6E6E6',  # Light gray
        'Ti': '#BFC2C7',  # Gray
        'V': '#A6A6AB',   # Gray
        'Cr': '#8A99C7',  # Gray-blue
        'Mn': '#9C7AC7',  # Purple-gray
        'Fe': '#E06633',  # Orange
        'Co': '#F090A0',  # Pink
        'Ni': '#50D050',  # Green
        'Cu': '#C88033',  # Brown
        'Zn': '#7D80B0',  # Gray-blue
        'Ga': '#C28F8F',  # Pink-brown
        'Ge': '#668F8F',  # Gray-blue
        'As': '#BD80E3',  # Purple
        'Se': '#FFA100',  # Orange
        'Br': '#A62929',  # Brown
        'Kr': '#5CB8D1',  # Light blue
        'Rb': '#702EB0',  # Purple
        'Sr': '#00FF00',  # Green
        'Y': '#94FFFF',   # Light cyan
        'Zr': '#94E0E0',  # Cyan
        'Nb': '#73C2C9',  # Blue-green
        'Mo': '#54B5B5',  # Blue-green
        'Tc': '#3B9E9E',  # Dark cyan
        'Ru': '#248F8F',  # Cyan
        'Rh': '#0A7D8C',  # Dark cyan
        'Pd': '#006985',  # Blue
        'Ag': '#C0C0C0',  # Silver
        'Cd': '#FFD98F',  # Light yellow
        'In': '#A67573',  # Brown
        'Sn': '#668080',  # Gray
        'Sb': '#9E63B5',  # Purple
        'Te': '#D47A00',  # Brown
        'I': '#940094',   # Purple
        'Xe': '#429EB0',  # Blue
        'Cs': '#57178F',  # Purple
        'Ba': '#00C900',  # Green
        'La': '#70D4FF',  # Light blue
        'Ce': '#FFFFC7',  # Very light yellow
        'Pr': '#D9FFC7',  # Light green
        'Nd': '#C7FFC7',  # Light green
        'Pm': '#A3FFC7',  # Light green
        'Sm': '#8FFFC7',  # Light green
        'Eu': '#61FFC7',  # Light green
        'Gd': '#45FFC7',  # Light green
        'Tb': '#30FFC7',  # Light green
        'Dy': '#1FFFC7',  # Light green
        'Ho': '#00FF9C',  # Green
        'Er': '#00E675',  # Green
        'Tm': '#00D452',  # Green
        'Yb': '#00BF38',  # Green
        'Lu': '#00AB24',  # Green
        'Hf': '#4DC2FF',  # Light blue
        'Ta': '#4DA6FF',  # Light blue
        'W': '#2194D6',   # Blue
        'Re': '#267DAB',  # Blue
        'Os': '#266696',  # Blue
        'Ir': '#175487',  # Blue
        'Pt': '#D0D0E0',  # Gray
        'Au': '#FFD123',  # Gold
        'Hg': '#B8B8D0',  # Gray
        'Tl': '#A6544D',  # Brown
        'Pb': '#575961',  # Dark gray
        'Bi': '#9E4FB5',  # Purple
        'Po': '#AB5C00',  # Brown
        'At': '#754F45',  # Dark brown
        'Rn': '#428296',  # Blue
        'Fr': '#420066',  # Dark purple
        'Ra': '#007D00',  # Dark green
        'Ac': '#70ABFA',  # Light blue
        'Th': '#00BAFF',  # Light blue
        'Pa': '#00A1FF',  # Light blue
        'U': '#008FFF',   # Blue
        'Np': '#0080FF',  # Blue
        'Pu': '#006BFF',  # Blue
        'Am': '#545CF2',  # Blue
        'Cm': '#785CE3',  # Blue
        'Bk': '#8A4FE3',  # Purple
        'Cf': '#A136D4',  # Purple
        'Es': '#B31FD4',  # Purple
        'Fm': '#B31FBA',  # Purple
        'Md': '#B30DA6',  # Purple
        'No': '#BD0D87',  # Purple
        'Lr': '#C70066',  # Dark red
        'Rf': '#CC0059',  # Dark red
        'Db': '#D1004F',  # Dark red
        'Sg': '#D90045',  # Dark red
        'Bh': '#E00038',  # Dark red
        'Hs': '#E6002E',  # Dark red
        'Mt': '#EB0026',  # Dark red
        'default': '#1FF01F'  # Bright green for unknown elements
    }   
    
    # Create legend HTML based on actual elements in the molecule
    legend_html = '<div style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap;">\n'
    for element in element_list:
        color = element_colors.get(element, element_colors['default'])
        legend_html += f'<div style="margin: 0 10px;"><span class="elementColor" style="background-color: {color};"></span>{element}</div>\n'
    legend_html += '</div>'
    
    # Use the exact format from test.py which is known to work
    # Modified to ensure full height and no scrollbars
    jsmol_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            html, body {{
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            #loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                z-index: 1000;
                background-color: rgba(255,255,255,0.7);
                padding: 20px;
                border-radius: 10px;
            }}
            #jsmolDiv {{
                width: 100%;
                height: 100%;
                position: relative;
            }}
            #elementLegend {{
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 5px;
                background-color: rgba(250,250,250,0.9);
                border-radius: 5px 5px 0 0;
                z-index: 100;
                font-size: 12px;
                font-family: Arial, sans-serif;
                border-top: 1px solid #ccc;
                text-align: center;
            }}
            .elementColor {{
                display: inline-block;
                width: 12px;
                height: 12px;
                margin-right: 5px;
                border: 1px solid #666;
                vertical-align: middle;
            }}
        </style>
        <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    </head>
    <body>
        <div id="loading">Loading molecule viewer...</div>
        <div id="jsmolDiv"></div>
        
        <!-- Element color legend - positioned at bottom -->
        <div id="elementLegend">
            {1}
        </div>
        
        <script>
            var pdbData = '{0}';
            
            // Load JSmol immediately
            document.addEventListener("DOMContentLoaded", function() {{
                loadJSmol();
            }});
            
            function loadJSmol() {{
                // Create a script element to load JSmol
                var script = document.createElement('script');
                script.src = "https://chemapps.stolaf.edu/jmol/jsmol/JSmol.min.js";
                script.onload = initJSmol;
                document.head.appendChild(script);
            }}
            
            function initJSmol() {{
                var Info = {{ 
                    width: "100%", 
                    height: "100%", 
                    use: "HTML5", 
                    j2sPath: "https://chemapps.stolaf.edu/jmol/jsmol/j2s", 
                    addSelectionOptions: false, 
                    debug: false, 
                    color: "white", 
                    disableInitialConsole: true, 
                    disableJ2SLoadMonitor: true, 
                    allowJavaScript: true 
                }};
                
                $("#jsmolDiv").html(Jmol.getAppletHtml("jmolApplet0", Info));
                setTimeout(loadMolecule, 500);
            }}
            
            function loadMolecule() {{
                try {{
                    Jmol.script(jmolApplet0, "zap");
                    var loadCmd = 'load DATA "pdb"\\n' + pdbData + '\\nEND "pdb"';
                    Jmol.script(jmolApplet0, loadCmd);
                    
                    // Get the elements present in the loaded model
                    var styling = [
                        "select all;",
                        "wireframe 0.15;", 
                        "spacefill 25%;",
                        
                        // Common element colors 
                        "select hydrogen; color white;",
                        "select carbon; color [144,144,144];", 
                        "select nitrogen; color [48,80,248];", 
                        "select oxygen; color [255,13,13];",   
                        "select sulfur; color [255,255,48];", 
                        
                        // Additional element colors
                        "select phosphorus; color [255,128,0];",
                        "select fluorine; color [144,224,80];", 
                        "select chlorine; color [31,240,31];",  
                        "select bromine; color [166,41,41];",   
                        "select iodine; color [148,0,148];",    
                        
                        // General settings
                        "set showHydrogens TRUE;",
                        "zoom 80;", 
                        "center;",
                        "frank off;"
                    ].join('\\n');
                    
                    Jmol.script(jmolApplet0, styling);
                    $("#loading").hide();
                }} catch (e) {{
                    console.error("Error in loadMolecule:", e);
                    $("#loading").html("<p style='color:red'>Error loading molecule: " + e.message + "</p>");
                }}
            }}
        </script>
    </body>
    </html>
    '''.format(pdb_data, legend_html)
    
    return jsmol_html

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
        match = re.match(r"^(\d*)(\w+)$", reactant)
        if not match:
            return None, f"Invalid reactant format: {reactant}"
        coef, compound = match.groups()
        coef = int(coef) if coef else 1
        parsed_reactants.append({"compound": compound, "coefficient": coef})
    
    # Parse coefficients and compounds for products
    parsed_products = []
    for product in products:
        match = re.match(r"^(\d*)(\w+)$", product)
        if not match:
            return None, f"Invalid product format: {product}"
        coef, compound = match.groups()
        coef = int(coef) if coef else 1
        parsed_products.append({"compound": compound, "coefficient": coef})
    
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

def calculate_stoichiometry(reaction_data, input_data, conversion_percentage=100):
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
    
    # Apply conversion percentage to limit how much of the limiting reactant is consumed
    conversion_factor = conversion_percentage / 100.0
    
    # Calculate product amounts
    results = {
        "limiting_reactant": limiting_compound,
        "reactants": {},
        "products": {},
        "conversion_percentage": conversion_percentage
    }
    
    # Calculate amounts for all reactants
    for reactant in reactants:
        compound = reactant["compound"]
        coef = reactant["coefficient"]
        molar_mass = input_data.get(compound, {}).get("molar_mass", None)
        
        if compound in reactant_amounts:
            moles = reactant_amounts[compound]["moles"]
            # Apply conversion factor to used moles
            used_moles = limiting_data["moles_per_coefficient"] * coef * conversion_factor
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
        
        # Apply conversion factor to produced moles
        produced_moles = limiting_data["moles_per_coefficient"] * coef * conversion_factor
        
        results["products"][compound] = {
            "produced_moles": produced_moles
        }
        
        if molar_mass:
            results["products"][compound]["produced_grams"] = produced_moles * molar_mass
    
    return results, "Success"

# Define the layout for the stoichiometry calculator
stoichiometry_calculator = html.Div([
    html.H2("Stoichiometry Calculator"),
    
    html.Div([
        html.Label([
            "Chemical Reaction Equation (e.g., '2H",
            html.Sub("2"),
            " + O",
            html.Sub("2"),
            " → 2H",
            html.Sub("2"),
            "O'):"
        ]),
        # Add keydown event for handling Enter key for the reaction input
        dcc.Input(
            id="reaction-equation",
            type="text",
            placeholder="Enter balanced chemical reaction...",
            style={"width": "100%", "marginBottom": "10px"},
            n_submit=0  # Add n_submit to enable Enter key submission
        ),
        html.Div([
            html.Button("Add Reaction", id="parse-button", n_clicks=0, style={"marginRight": "15px"}),
            # Hide the checkbox initially - don't use disabled as it's not supported
            html.Div(id="conversion-checkbox-container", style={"display": "none"}, children=[
                dcc.Checklist(
                    id="conversion-toggle",
                    options=[{"label": "Specify Conversion", "value": "show"}],
                    value=[],
                    style={"display": "inline-block", "marginRight": "15px"}
                ),
            ]),
            # Add 3D visualization checkbox
            html.Div(id="3d-model-checkbox-container", style={"display": "none"}, children=[
                dcc.Checklist(
                    id="3d-model-toggle",
                    options=[{"label": "Show 3D Models", "value": "show"}],
                    value=[],
                    style={"display": "inline-block", "marginRight": "15px"}
                ),
            ]),
            # Always add the slider to DOM but keep it hidden - this prevents the "nonexistent object" error
        ], style={"display": "flex", "alignItems": "center"}),
    ]),
    # Updated container: restrict width of reaction parse output
    html.Div([
        html.Div(id="reaction-parse-output", style={"flex": "0 1 auto", "maxWidth": "600px"}),
        html.Div(id="conversion-slider-container", style={
            "flex": "none",
            "width": "300px",
            "marginLeft": "10px",
            "position": "relative", 
            "top": "0px",   # shift the slider down slightly
            "verticalAlign": "middle"
        }, children=[
            dcc.Slider(
                id="conversion-slider",
                min=0,
                max=100,
                step=1,
                value=100,
                marks={0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%'},
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="drag"
            )
        ])
    ], style={"display": "flex", "alignItems": "center", "marginTop": "20px"}),
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

# Create molecular visualization tool
molecular_visualization_tool = html.Div([
    html.H2("Molecular Structure Visualization", style={'textAlign': 'center', 'marginBottom': 20}),
    html.Div([
        dcc.Input(
            id='chemical-input',
            type='text',
            placeholder='Enter chemical name (e.g., aspirin, ethanol, or methylbenzene)',
            value='',
            style={'width': '50%', 'marginRight': '10px'},
            n_submit=0
        ),
        html.Button('Visualize', id='submit-button', n_clicks=0, style={'marginRight': '10px'}),
        # Move loading circle to the right so it doesn't overlap the button
        html.Div(
            id='loading-container',
            style={'display': 'inline-block', 'verticalAlign': 'middle', 'position': 'relative', 'left': '10px'},
            children=[
                dcc.Loading(
                    id="loading-search",
                    type="circle",
                    color="#119DFF",
                    children=html.Div(id="loading-output")
                )
            ]
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div(id='error-message', style={'color': 'red', 'textAlign': 'center'}),
    html.Div(id='chemical-name', style={'textAlign': 'center', 'marginBottom': '10px'}),
    html.Div(id='molecule-viewer'),
    html.Div([
        html.P("You can rotate, zoom, and pan the molecule using your mouse.",
              style={'textAlign': 'center', 'marginTop': 15})
    ])
])

# Main layout with tabs for different chemistry tools
layout = html.Div([
    html.H1("Chemistry Tools"),
    
    dcc.Dropdown(
        id='chem-tool-selector',
        options=[
            {'label': 'Stoichiometry Calculator', 'value': 'stoichiometry'},
            {'label': 'Molecular Visualization', 'value': 'molecular-viz'},
            {'label': 'Acid-Base Equilibrium (Coming Soon)', 'value': 'acid-base'},
            {'label': 'Gas Laws Calculator (Coming Soon)', 'value': 'gas-laws'}
        ],
        value='stoichiometry',
        clearable=False,
        style={"width": "100%", "marginBottom": "20px", "color": "black"}
    ),
    
    html.Div(id='chem-tool-content'),
    
    # Add hidden div for storing reaction data
    html.Div(id='reaction-data-json', style={'display': 'none'}),
    
    # Add JavaScript code for client-side calculations
    html.Div([
        dcc.Store(id='molar-masses-store'),
        dcc.Store(id='molecule-models-store'),
    ])
])

@callback(
    Output('chem-tool-content', 'children'),
    Input('chem-tool-selector', 'value')
)
def render_tool_content(selected_tool):
    if selected_tool == 'stoichiometry':
        return stoichiometry_calculator
    elif selected_tool == 'molecular-viz':
        return molecular_visualization_tool
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
        Output("calculate-button", "style"),
        Output("conversion-slider-container", "style"),
        Output("conversion-checkbox-container", "style"),  # Show/hide checkbox container instead of disabling
        Output("reaction-data-json", "children"),  # Store reaction data as JSON
        Output("molar-masses-store", "data"),  # Store molar masses
        Output("3d-model-checkbox-container", "style"),  # Show/hide 3D model checkbox
        Output("molecule-models-store", "data"),  # Store molecule models data
    ],
    [
        Input("parse-button", "n_clicks"),
        Input("reaction-equation", "n_submit")  # Add Enter key support
    ],
    [
        State("reaction-equation", "value"), 
        State("conversion-toggle", "value")
    ]
)
def parse_reaction(n_clicks, n_submit, equation, conversion_toggle):
    # Combine n_clicks and n_submit to trigger on either button click or Enter key
    trigger_count = n_clicks + n_submit
    
    # Only check for empty equation when button has been clicked or Enter pressed
    if trigger_count > 0 and not equation:
        return "Please enter a reaction equation", {"display": "none"}, None, {"display": "none"}, {"display": "none"}, {"display": "none"}, None, None, {"display": "none"}, None
    
    # If neither button clicked nor Enter pressed, return empty response
    if trigger_count == 0:
        return "", {"display": "none"}, None, {"display": "none"}, {"display": "none"}, {"display": "none"}, None, None, {"display": "none"}, None
    
    parsed_reaction, message = parse_reaction_equation(equation)
    
    if parsed_reaction is None:
        return message, {"display": "none"}, None, {"display": "none"}, {"display": "none"}, {"display": "none"}, None, None, {"display": "none"}, None
    
    # Create a dictionary to store molar masses
    molar_masses = {}
    
    # Create a dictionary to store molecule visualization data - start with empty
    # We'll load models asynchronously later
    molecule_models = {}
    
    # Get molar masses for all compounds
    for reactant in parsed_reaction["reactants"]:
        compound = reactant["compound"]
        molar_masses[compound] = get_molar_mass(compound)
    
    for product in parsed_reaction["products"]:
        compound = product["compound"]
        molar_masses[product["compound"]] = get_molar_mass(product["compound"])
    
    show_slider = "show" in conversion_toggle
    slider_style = {"display": "inline-block", "width": "300px", "marginLeft": "10px", "verticalAlign": "middle"} if show_slider else {"display": "none"}
    
    # Create the formatted reaction equation display with proper pluses and arrow
    eq_parts = []
    eq_parts.append("Reaction: ")  # Add inline label
    
    # Add reactants with plus signs between them
    for i, reactant in enumerate(parsed_reaction["reactants"]):
        if i > 0:
            eq_parts.append(" + ")
            
        if reactant["coefficient"] > 1:
            eq_parts.append(str(reactant["coefficient"]))
        eq_parts.extend(create_formula_display(reactant["compound"]))
    
    eq_parts.append(" → ")
    
    for i, product in enumerate(parsed_reaction["products"]):
        if i > 0:
            eq_parts.append(" + ")
            
        if product["coefficient"] > 1:
            eq_parts.append(str(product["coefficient"]))
        eq_parts.extend(create_formula_display(product["compound"]))
    
    parsed_output = html.Div(
        eq_parts,
        style={
            "fontSize": "1.2em", 
            "marginBottom": "8px", 
            "marginTop": "8px", 
            "display": "inline-block",
            "width": "100%",
            "verticalAlign": "middle"
        }
    )
    
    # Create compound boxes with input fields for reactants and products
    compound_inputs = []
    
    # Add reactants
    for reactant in parsed_reaction["reactants"]:
        compound = reactant["compound"]
        molar_mass = molar_masses[compound]
        
        # Create a container for the reactant that will hold the input form and potentially the 3D model
        compound_inputs.append(html.Div([
            # Main compound info and input fields
            html.Div([
                html.Div([
                    html.Span([*create_formula_display(compound)]),
                    html.Span([
                        f" ({molar_mass:.2f} g/mol)" if molar_mass else "",
                        " ",
                        html.Span(id={"type": "limiting-indicator", "compound": compound}, 
                                children="", 
                                style={"color": "red", "fontWeight": "bold", "visibility": "hidden"})
                    ], style={"whiteSpace": "nowrap"})
                ], style={"fontSize": "1.2em", "marginBottom": "10px", "display": "flex", "alignItems": "center", "gap": "4px"}),
                html.Div([
                    # Input boxes with results
                    html.Div([
                        html.Div(style={"width": "60px"}, children=[
                            dcc.Input(
                                id={"type": "moles-input", "compound": compound},
                                type="number",
                                placeholder="moles",
                                style={"width": "60px"},
                                min=0  # Add minimum value
                            ),
                        ]),
                        html.Div(style={"width": "200px", "marginLeft": "10px"}, children=[
                            html.Span(" → Used: ", id={"type": "used-text-moles", "compound": compound}, style={"visibility": "hidden"}),
                            html.Span(id={"type": "used-moles", "compound": compound}, children="", style={"visibility": "hidden"}),
                        ]),
                        html.Div(style={"width": "200px"}, children=[
                            html.Span(" Excess: ", id={"type": "excess-text-moles", "compound": compound}, style={"visibility": "hidden"}),
                            html.Span(id={"type": "excess-moles", "compound": compound}, children="", style={"visibility": "hidden"}),
                        ])
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
                    
                    # Grams row
                    html.Div([
                        html.Div(style={"width": "60px"}, children=[
                            dcc.Input(
                                id={"type": "grams-input", "compound": compound},
                                type="number",
                                placeholder="grams",
                                style={"width": "60px"},
                                min=0  # Add minimum value
                            ),
                        ]),
                        html.Div(style={"width": "200px", "marginLeft": "10px"}, children=[
                            html.Span(" → Used: ", id={"type": "used-text-grams", "compound": compound}, style={"visibility": "hidden"}),
                            html.Span(id={"type": "used-grams", "compound": compound}, children="", style={"visibility": "hidden"}),
                        ]),
                        html.Div(style={"width": "200px"}, children=[
                            html.Span(" Excess: ", id={"type": "excess-text-grams", "compound": compound}, style={"visibility": "hidden"}),
                            html.Span(id={"type": "excess-grams", "compound": compound}, children="", style={"visibility": "hidden"})
                        ])
                    ], style={"display": "flex", "alignItems": "center"})
                ])
            ], style={"flex": "1"}),
            
            # Container for 3D model (initially hidden)
            html.Div(
                id={"type": "3d-model-container", "compound": compound},
                style={"display": "none", "flex": "1", "minWidth": "150px"},
                children=[]
            )
        ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px", "display": "flex", "flexWrap": "wrap", "gap": "10px", "alignItems": "center"}))
    
    products_display = []
    for product in parsed_reaction["products"]:
        compound = product["compound"]
        molar_mass = molar_masses[compound]
        
        # Create a container for the product that will hold the result and potentially the 3D model
        compound_inputs.append(html.Div([
            # Main compound info and results
            html.Div([
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
            ], style={"flex": "1"}),
            
            # Container for 3D model (initially hidden)
            html.Div(
                id={"type": "3d-model-container", "compound": compound},
                style={"display": "none", "flex": "1", "minWidth": "150px"},
                children=[]
            )
        ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px", "display": "flex", "flexWrap": "wrap", "gap": "10px", "alignItems": "center"}))
    
    # Store data for later use
    inputs_container = html.Div([
        html.Div(compound_inputs)
    ])
    
    # Return the parsed reaction as JSON for the clientside callback
    import json
    reaction_data_json = json.dumps(parsed_reaction)
    
    # Show the checkbox containers after parsing and enable them
    checkbox_style = {"display": "inline-block"}
    
    return parsed_output, {"display": "block", "marginTop": "20px"}, inputs_container, {"display": "block", "marginTop": "20px"}, slider_style, checkbox_style, reaction_data_json, molar_masses, checkbox_style, molecule_models

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

# Add a callback to show/hide the conversion slider based on checkbox
@callback(
    [
        Output("conversion-slider-container", "style", allow_duplicate=True),
        Output("conversion-toggle", "options", allow_duplicate=True),
    ],
    Input("conversion-toggle", "value"),
    State("reaction-data-json", "children"),
    prevent_initial_call=True
)
def toggle_conversion_slider(values, reaction_data):
    # Check if calculation has been performed
    if (reaction_data is not None):
        return (
            {"display": "inline-block", "width": "300px", "verticalAlign": "middle"} if "show" in values else {"display": "none"},
            [{"label": "Specify Conversion", "value": "show"}]
        )
    else:
        return {"display": "none"}, [{"label": "Specify Conversion", "value": "show"}]

# Replace the Python callback with a clientside callback for calculations
clientside_callback(
    """
    function(n_clicks, conversion_value, reaction_data_json, molar_masses, moles_values, grams_values, 
             moles_ids, grams_ids, conversion_toggle) {
        // Parse inputs
        if (!reaction_data_json || n_clicks === 0) {
            return makeEmptyOutputs(moles_ids, reaction_data_json);
        }
        
        const reaction_data = JSON.parse(reaction_data_json);
        const conversion_percentage = conversion_toggle.includes("show") ? conversion_value : 100;
        
        // Prepare input data
        const input_data = {};
        
        // Process moles inputs
        for (let i = 0; i < moles_values.length; i++) {
            const moles = moles_values[i];
            if (moles !== null && !isNaN(moles)) {
                const compound = moles_ids[i].compound;
                if (!input_data[compound]) {
                    input_data[compound] = {};
                }
                input_data[compound].moles = parseFloat(moles);
            }
        }
        
        // Process grams inputs
        for (let i = 0; i < grams_values.length; i++) {
            const grams = grams_values[i];
            if (grams !== null && !isNaN(grams)) {
                const compound = grams_ids[i].compound;
                if (!input_data[compound]) {
                    input_data[compound] = {};
                }
                input_data[compound].grams = parseFloat(grams);
            }
        }
        
        // Add molar mass data
        for (const compound in molar_masses) {
            if (!input_data[compound]) {
                input_data[compound] = {};
            }
            input_data[compound].molar_mass = molar_masses[compound];
        }
        
        // Calculate stoichiometry
        const results = calculateStoichiometry(reaction_data, input_data, conversion_percentage);
        if (!results) {
            return makeEmptyOutputs(moles_ids, reaction_data_json);
        }
        
        // Process results for reactants and products
        const used_moles_values = [];
        const excess_moles_values = [];
        const used_grams_values = [];
        const excess_grams_values = [];
        const produced_moles_values = [];
        const produced_grams_values = [];
        const limiting_indicators = [];
        
        // Map compounds to their results
        const compound_results = {};
        
        // Process reactant results
        for (const compound in results.reactants) {
            const data = results.reactants[compound];
            compound_results[compound] = {
                used_moles: data.used_moles.toFixed(3) + " mol",
                excess_moles: data.excess_moles.toFixed(3) + " mol",
                used_grams: data.used_grams ? data.used_grams.toFixed(3) + " g" : "0 g",
                excess_grams: data.excess_grams !== undefined ? data.excess_grams.toFixed(3) + " g" : "0 g"
            };
        }
        
        // Extract values in the correct order for each output
        for (const cid of moles_ids) {
            const compound = cid.compound;
            const data = compound_results[compound] || {};
            used_moles_values.push(data.used_moles || "");
            excess_moles_values.push(data.excess_moles || "");
        }
        
        for (const cid of moles_ids) {
            const compound = cid.compound;
            const data = compound_results[compound] || {};
            used_grams_values.push(data.used_grams || "");
            excess_grams_values.push(data.excess_grams || "");
            
            // Determine if this is the limiting reactant
            const is_limiting = compound === results.limiting_reactant;
            limiting_indicators.push(is_limiting ? "(Limiting Reactant)" : "");
        }
        
        // Process product results
        for (const compound in results.products) {
            const data = results.products[compound];
            compound_results[compound] = {
                produced_moles: data.produced_moles.toFixed(3) + " mol",
                produced_grams: data.produced_grams.toFixed(3) + " g"
            };
        }
        
        // Get the produced values in order
        const product_compounds = reaction_data.products.map(p => p.compound);
        for (const compound of product_compounds) {
            const data = compound_results[compound] || {};
            produced_moles_values.push(data.produced_moles || "");
            produced_grams_values.push(data.produced_grams || "");
        }
        
        // Create visibility styles
        const visible_style = {visibility: "visible"};
        const n_reactants = moles_ids.length;
        const n_products = product_compounds.length;
        
        const used_moles_styles = Array(n_reactants).fill(visible_style);
        const excess_moles_styles = Array(n_reactants).fill(visible_style);
        const used_grams_styles = Array(n_reactants).fill(visible_style);
        const excess_grams_styles = Array(n_reactants).fill(visible_style);
        const limiting_indicator_styles = Array(n_reactants).fill({visibility: "visible", color: "red", fontWeight: "bold"});
        
        const produced_moles_styles = Array(n_products).fill(visible_style);
        const produced_grams_styles = Array(n_products).fill(visible_style);
        
        // Text element styles
        const used_text_moles_styles = Array(n_reactants).fill({visibility: "visible", marginLeft: "10px"});
        const used_text_grams_styles = Array(n_reactants).fill({visibility: "visible", marginLeft: "10px"});
        const excess_text_moles_styles = Array(n_reactants).fill({visibility: "visible", marginLeft: "10px"});
        const excess_text_grams_styles = Array(n_reactants).fill({visibility: "visible", marginLeft: "10px"});
        
        const produced_text_styles = Array(n_products).fill({visibility: "visible", marginRight: "5px"});
        const produced_moles_text_styles = Array(n_products).fill({visibility: "visible", marginRight: "5px"});
        const produced_paren1_styles = Array(n_products).fill({visibility: "visible"});
        const produced_paren2_styles = Array(n_products).fill({visibility: "visible"});
        
        return [
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
            null,  // For calculation-results
            used_text_moles_styles,
            used_text_grams_styles,
            excess_text_moles_styles,
            excess_text_grams_styles,
            produced_text_styles,
            produced_moles_text_styles,
            produced_paren1_styles,
            produced_paren2_styles
        ];
        
        // Helper function to create empty outputs - modified to accept reaction_data_json parameter
        function makeEmptyOutputs(moles_ids, reaction_data_json) {
            const n_reactants = moles_ids.length;
            // Only parse reaction data if it exists
            let n_products = 0;
            if (reaction_data_json) {
                try {
                    const reaction_data = JSON.parse(reaction_data_json);
                    n_products = reaction_data.products.length;
                } catch (e) {
                    // If parsing fails, default to 0 products
                    n_products = 0;
                }
            }
            
            const empty_strings = Array(n_reactants).fill("");
            const empty_styles = Array(n_reactants).fill({visibility: "hidden"});
            const empty_product_strings = Array(n_products).fill("");
            const empty_product_styles = Array(n_products).fill({visibility: "hidden"});
            
            return [
                empty_strings,
                empty_strings,
                empty_strings,
                empty_strings,
                empty_product_strings,
                empty_product_strings,
                empty_strings,
                empty_styles,
                empty_styles,
                empty_styles,
                empty_styles,
                empty_product_styles,
                empty_product_styles,
                empty_styles,
                null,
                empty_styles,
                empty_styles,
                empty_styles,
                empty_styles,
                empty_product_styles,
                empty_product_styles,
                empty_product_styles,
                empty_product_styles
            ];
        }
        
        // JavaScript implementation of calculate_stoichiometry
        function calculateStoichiometry(reaction_data, input_data, conversion_percentage = 100) {
            // Extract reactants and products data
            const reactants = reaction_data.reactants;
            const products = reaction_data.products;
            
            // Get input amounts
            const reactant_amounts = {};
            
            for (const reactant of reactants) {
                const compound = reactant.compound;
                if (compound in input_data) {
                    let moles = input_data[compound].moles;
                    const grams = input_data[compound].grams;
                    const molar_mass = input_data[compound].molar_mass;
                    
                    // Convert grams to moles if needed
                    if (moles === undefined && grams !== undefined && molar_mass !== undefined && molar_mass > 0) {
                        moles = grams / molar_mass;
                    }
                    
                    if (moles !== undefined) {
                        reactant_amounts[compound] = {
                            moles: moles,
                            coefficient: reactant.coefficient,
                            moles_per_coefficient: moles / reactant.coefficient
                        };
                    }
                }
            }
            
            // If no reactants have amounts, return an error
            if (Object.keys(reactant_amounts).length < 1) {
                return null;
            }
            
            // Find limiting reactant
            let limiting_compound = null;
            let limiting_data = null;
            let min_moles_per_coef = Infinity;
            
            for (const compound in reactant_amounts) {
                const data = reactant_amounts[compound];
                if (data.moles_per_coefficient < min_moles_per_coef) {
                    min_moles_per_coef = data.moles_per_coefficient;
                    limiting_compound = compound;
                    limiting_data = data;
                }
            }
            
            // Apply conversion percentage to limit how much of the limiting reactant is consumed
            const conversion_factor = conversion_percentage / 100.0;
            
            // Calculate product amounts
            const results = {
                limiting_reactant: limiting_compound,
                reactants: {},
                products: {},
                conversion_percentage: conversion_percentage
            };
            
            // Calculate amounts for all reactants
            for (const reactant of reactants) {
                const compound = reactant.compound;
                const coef = reactant.coefficient;
                const molar_mass = input_data[compound]?.molar_mass;
                
                if (compound in reactant_amounts) {
                    const moles = reactant_amounts[compound].moles;
                    // Apply conversion factor to used moles
                    const used_moles = limiting_data.moles_per_coefficient * coef * conversion_factor;
                    const excess_moles = moles > used_moles ? moles - used_moles : 0;
                    
                    results.reactants[compound] = {
                        initial_moles: moles,
                        used_moles: used_moles,
                        excess_moles: excess_moles
                    };
                    
                    if (molar_mass) {
                        results.reactants[compound].initial_grams = moles * molar_mass;
                        results.reactants[compound].used_grams = used_moles * molar_mass;
                        results.reactants[compound].excess_grams = excess_moles * molar_mass;
                    } else {
                        // Provide zero values instead of undefined
                        results.reactants[compound].initial_grams = 0;
                        results.reactants[compound].used_grams = 0;
                        results.reactants[compound].excess_grams = 0;
                    }
                }
            }
            
            // Calculate product amounts
            for (const product of products) {
                const compound = product.compound;
                const coef = product.coefficient;
                const molar_mass = input_data[compound]?.molar_mass;
                
                // Apply conversion factor to produced moles
                const produced_moles = limiting_data.moles_per_coefficient * coef * conversion_factor;
                
                results.products[compound] = {
                    produced_moles: produced_moles
                };
                
                // Always calculate produced grams using molar mass from molar_masses object
                if (molar_mass) {
                    results.products[compound].produced_grams = produced_moles * molar_mass;
                } else {
                    // Default to zero if molar mass is not available (should not happen)
                    results.products[compound].produced_grams = 0;
                }
            }
            
            return results;
        }
    }
    """,
    [
        Output({"type": "used-moles", "compound": dash.ALL}, "children"),
        Output({"type": "excess-moles", "compound": dash.ALL}, "children"),
        Output({"type": "used-grams", "compound": dash.ALL}, "children"),
        Output({"type": "excess-grams", "compound": dash.ALL}, "children"),
        Output({"type": "produced-moles", "compound": dash.ALL}, "children"),
        Output({"type": "produced-grams", "compound": dash.ALL}, "children"),
        Output({"type": "limiting-indicator", "compound": dash.ALL}, "children"),
        Output({"type": "used-moles", "compound": dash.ALL}, "style"),
        Output({"type": "excess-moles", "compound": dash.ALL}, "style"),
        Output({"type": "used-grams", "compound": dash.ALL}, "style"),
        Output({"type": "excess-grams", "compound": dash.ALL}, "style"),
        Output({"type": "produced-moles", "compound": dash.ALL}, "style"),
        Output({"type": "produced-grams", "compound": dash.ALL}, "style"),
        Output({"type": "limiting-indicator", "compound": dash.ALL}, "style"),
        Output("calculation-results", "children"),
        Output({"type": "used-text-moles", "compound": dash.ALL}, "style"),
        Output({"type": "used-text-grams", "compound": dash.ALL}, "style"),
        Output({"type": "excess-text-moles", "compound": dash.ALL}, "style"),
        Output({"type": "excess-text-grams", "compound": dash.ALL}, "style"),
        Output({"type": "produced-text", "compound": dash.ALL}, "style"),
        Output({"type": "produced-moles-text", "compound": dash.ALL}, "style"),
        Output({"type": "produced-paren1", "compound": dash.ALL}, "style"),
        Output({"type": "produced-paren2", "compound": dash.ALL}, "style")
    ],
    [Input("calculate-button", "n_clicks"), Input("conversion-slider", "value")],
    [
        State("reaction-data-json", "children"),
        State("molar-masses-store", "data"),
        State({"type": "moles-input", "compound": dash.ALL}, "value"),
        State({"type": "grams-input", "compound": dash.ALL}, "value"),
        State({"type": "moles-input", "compound": dash.ALL}, "id"),
        State({"type": "grams-input", "compound": dash.ALL}, "id"),
        State("conversion-toggle", "value")
    ]
)

@callback(
    [Output('molecule-viewer', 'children'),
     Output('error-message', 'children'),
     Output('chemical-name', 'children'),
     Output('loading-output', 'children')],
    [Input('submit-button', 'n_clicks'),
     Input('chemical-input', 'n_submit')],
    [State('chemical-input', 'value')]
)
def update_molecule(n_clicks, n_submit, chemical_name):
    # Function is triggered by either button click or Enter key
    if not chemical_name:
        return [], "Please enter a chemical name", "", []
    
    smiles, name_or_error = get_smiles_from_name(chemical_name)
    if smiles is None:
        return [], name_or_error, "", []
    
    mol, error = create_molecule_from_smiles(smiles)
    if error:
        return [], f"Error creating 3D model: {error}", "", []
    
    # Use appropriate styling for iframe - ensure 100% height with no scrollbar
    viewer = html.Iframe(
        srcDoc=create_viewer_html(mol),
        style={
            'width': '100%', 
            'height': '70vh', 
            'border': 'none',
            'overflow': 'hidden',
            'display': 'block'
        }
    )
    
    # Display the chemical name
    name_display = html.H4(name_or_error or chemical_name.capitalize())
    
    return viewer, "", name_display, []

# New callback to load molecule models asynchronously after the reaction has been parsed
# This callback was redundant and can be removed since we're using preload_molecule_models instead
# Delete this callback entirely

# Add a new callback for preloading 3D models right after reaction parsing
@callback(
    Output("molecule-models-store", "data", allow_duplicate=True),
    [Input("reaction-data-json", "children")],
    prevent_initial_call=True
)
def preload_molecule_models(reaction_data_json):
    if not reaction_data_json:
        return {}
        
    import json
    molecule_models = {}
    
    try:
        # Parse the reaction data
        parsed_reaction = json.loads(reaction_data_json)
        
        # Get all compounds from reactants and products
        all_compounds = []
        for reactant in parsed_reaction["reactants"]:
            all_compounds.append(reactant["compound"])
            
        for product in parsed_reaction["products"]:
            all_compounds.append(product["compound"])
        
        print(f"Preloading models for compounds: {all_compounds}")
            
        # Try to get SMILES and preload all models at once
        for compound in all_compounds:
            try:
                smiles, name = get_smiles_from_name(compound)
                if smiles:
                    # Also create the molecule in advance to have it ready
                    mol, error = create_molecule_from_smiles(smiles)
                    molecule_models[compound] = {
                        "smiles": smiles,
                        "iupac_name": name if name else compound,
                        "loaded": True if mol else False
                    }
                    print(f"Successfully preloaded model for {compound}: loaded={mol is not None}")
                else:
                    print(f"Failed to get SMILES for {compound}")
            except Exception as e:
                print(f"Error preloading model for {compound}: {str(e)}")
                # If there's an error getting this compound, just continue to next one
                continue
                
    except Exception as e:
        print(f"Error preloading models: {str(e)}")
        # If there's any error parsing the reaction data, return empty dict
        pass
        
    print(f"Final preloaded models: {list(molecule_models.keys())}")
    return molecule_models

# Add a callback to handle 3D model toggle and display models when Calculate is clicked
@callback(
    Output({"type": "3d-model-container", "compound": dash.ALL}, "style"),
    Output({"type": "3d-model-container", "compound": dash.ALL}, "children"),
    [Input("calculate-button", "n_clicks"),
     Input("3d-model-toggle", "value")],
    [State("molecule-models-store", "data"),
     State({"type": "3d-model-container", "compound": dash.ALL}, "id")]
)
def update_3d_models(n_clicks, toggle_value, molecule_models, model_ids):
    # Print debugging information
    print(f"3D toggle value: {toggle_value}, n_clicks: {n_clicks}")
    print(f"Available model IDs: {[m['compound'] for m in model_ids]}")
    print(f"Available models in store: {list(molecule_models.keys()) if molecule_models else 'None'}")
    
    # Don't show models if toggle is not checked or Calculate hasn't been clicked
    show_models = n_clicks > 0 and "show" in (toggle_value or [])
    
    # If we shouldn't show models, just hide all containers
    if not show_models or not molecule_models:
        return [{"display": "none"} for _ in model_ids], [[] for _ in model_ids]
    
    styles = []
    children = []
    
    # For each model container
    for container_id in model_ids:
        compound = container_id["compound"]
        
        # Show container if we have SMILES data for this compound
        if compound in molecule_models and molecule_models[compound].get("smiles"):
            print(f"Showing 3D model for {compound}")
            styles.append({
                "display": "block", 
                "flex": "1", 
                "minWidth": "150px",
                "margin": "10px 0"
            })
            
            try:
                # Create molecule from SMILES
                smiles = molecule_models[compound]["smiles"]
                mol, error = create_molecule_from_smiles(smiles)
                
                if mol:
                    # Create model without the title
                    viewer_components = [
                        html.Iframe(
                            srcDoc=create_viewer_html(mol),
                            style={
                                'width': '100%',
                                'height': '200px',
                                'border': 'none',
                                'overflow': 'hidden'
                            }
                        )
                    ]
                    children.append(viewer_components)
                else:
                    print(f"Failed to create molecule for {compound}: {error}")
                    children.append([html.Div(f"Could not generate 3D model for {compound}")])
            except Exception as e:
                print(f"Exception generating model for {compound}: {str(e)}")
                children.append([html.Div(f"Error: {str(e)}")])
        else:
            print(f"No model data for {compound}")
            styles.append({"display": "none"})
            children.append([])
    
    return styles, children

# Let's also add JavaScript debug logs to the clientside callback
@callback(
    Output("molecule-models-store", "data", allow_duplicate=True),  # Add allow_duplicate=True here
    [Input("3d-model-toggle", "value")],
    [State("molecule-models-store", "data")],
    prevent_initial_call=True
)
def log_toggle_change(toggle_value, current_models):
    """Log whenever the toggle is changed to help debugging"""
    print(f"3D model toggle changed to: {toggle_value}")
    print(f"Current models: {list(current_models.keys()) if current_models else 'None'}")
    # Return the current data unchanged
    return current_models

# Add "Enter" key support for Calculate button
clientside_callback(
    """
    function(n_clicks, reactant_values, reactant_ids) {
        // This callback triggers when Enter key is pressed in any input
        // Check if we have at least one reactant with a value
        let hasValue = false;
        for (const value of reactant_values) {
            if (value !== null && value !== "") {
                hasValue = true;
                break;
            }
        }
        
        // If there's a value, trigger the calculate button
        if (hasValue) {
            return n_clicks + 1;
        }
        
        // Otherwise, don't trigger
        return n_clicks;
    }
    """,
    Output("calculate-button", "n_clicks"),
    [
        Input("calculate-button", "n_clicks"),
        Input({"type": "moles-input", "compound": dash.ALL}, "n_submit"),
        Input({"type": "grams-input", "compound": dash.ALL}, "n_submit")
    ],
    [
        State({"type": "moles-input", "compound": dash.ALL}, "value"),
        State({"type": "grams-input", "compound": dash.ALL}, "value"),
        State({"type": "moles-input", "compound": dash.ALL}, "id")
    ],
    prevent_initial_call=True
)