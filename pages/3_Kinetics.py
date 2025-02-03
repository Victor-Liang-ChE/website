from dash import dcc, html, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from scipy.integrate import solve_ivp
import re

dash.register_page(__name__, path='/kinetics', name="Kinetics Graph")

def subscript_numbers(species):
    parts = re.split(r'(\d+)', species)
    return [html.Span(part) if not part.isdigit() else html.Sub(part) for part in parts]

# Function to detect unique species in the order they appear
def detect_unique_species_ordered(reactions):
    ordered_species = []
    unique_species = set()
    
    for reaction in reactions:
        # Split the reaction into reactants and products
        reactants, products = reaction.split('->')
        
        # Extract species from reactants and products
        reactant_species = [re.sub(r'^\d*\*?', '', species.strip()) for species in reactants.split('+')]
        product_species = [re.sub(r'^\d*\*?', '', species.strip()) for species in products.split('+')]
        
        # Add species to the ordered list if they are not already in the set
        for species in reactant_species + product_species:
            if species not in unique_species:
                unique_species.add(species)
                ordered_species.append(species)
    
    return ordered_species

# Function to generate the reaction graph
def reactiongraphing(reactions, ks, C0):
    # Check that the number of ks elements matches the number of reactions
    if len(ks) != len(reactions):
        raise ValueError("The number of rate constants does not match the number of reactions.")

    # Function to format species names with subscripted numbers using HTML
    def format_species(species):
        return re.sub(r'(\d+)', r'<sub>\1</sub>', species)

    # Extract unique species from reactions in the order they appear
    ordered_species = detect_unique_species_ordered(reactions)

    # Check that all unique species are present in C0
    if not set(ordered_species).issubset(C0.keys()):
        missing_species = set(ordered_species) - set(C0.keys())
        raise ValueError(f"The following species are missing in C0: {missing_species}")

    # Define the system of ODEs
    def odes(t, y):
        dydt = np.zeros(len(ordered_species))
        concentrations = {species: y[i] for i, species in enumerate(ordered_species)}
        for i, reaction in enumerate(reactions):
            reactants, products = reaction.split('->')
            reactant_species = []
            for species in reactants.split('+'):
                coeff, sp = re.match(r'(\d*)(\w+)', species).groups()
                coeff = int(coeff) if coeff else 1
                reactant_species.append((sp, coeff))
            
            # Calculate the reaction rate
            rate = ks[i] * np.prod([concentrations[sp]**coeff for sp, coeff in reactant_species])
            
            # Update differential forms
            for sp, coeff in reactant_species:
                dydt[ordered_species.index(sp)] -= rate * coeff
            
            for product in products.split('+'):
                coeff, sp = re.match(r'(\d*)(\w+)', product).groups()
                coeff = int(coeff) if coeff else 1
                dydt[ordered_species.index(sp)] += rate * coeff
        
        return dydt

    # Initial concentrations
    y0 = [C0[species] for species in ordered_species]

    # Time span for the simulation
    t_span = (0, 10)
    t_eval = np.linspace(t_span[0], t_span[1], 1000)

    # Solve the ODEs
    solution = solve_ivp(odes, t_span, y0, t_eval=t_eval, method='RK45')

    # Determine the steady state time
    max_concentration = np.max(solution.y)
    print(f"Max concentration: {max_concentration}")
    
    relative_tolerance = max_concentration * 1e-4  # Relative tolerance based on the maximum concentration
    print(f"Relative tolerance: {relative_tolerance}")
    
    steady_state_time = t_span[1]
    print(f"Initial steady state time: {steady_state_time}")
    
    for i in range(1, len(solution.t)):
        concentration_diff = np.abs(solution.y[:, i] - solution.y[:, i-1])
        print(f"Time: {solution.t[i]}, Concentration difference: {concentration_diff}")
        
        if np.all(concentration_diff < relative_tolerance):
            steady_state_time = solution.t[i]
            print(f"Steady state reached at time: {steady_state_time}")
            break
    
    print(f"Final steady state time: {steady_state_time}")

    # Create the plotly figure
    fig = go.Figure()
    for i, species in enumerate(ordered_species):
        formatted_species = format_species(species)
        fig.add_trace(go.Scatter(x=solution.t, y=solution.y[i], mode='lines', name=formatted_species))

    fig.update_layout(
        title=dict(
            text='Concentrations vs. Time',
            x=0.5,
            font=dict(size=24, family='Merriweather Sans', color='white')
        ),
        xaxis=dict(
            title='Time',
            title_font=dict(size=24, family='Merriweather Sans', color='white'),
            tickfont=dict(size=18, family='Merriweather Sans', color='white'),  # Increased tick font size
            ticks='outside',
            ticklen=5,
            tickwidth=2,
            tickcolor='white',
            gridcolor='rgba(0,0,0,0)',
            range=[0, steady_state_time]
        ),
        yaxis=dict(
            title='Concentration',
            title_font=dict(size=24, family='Merriweather Sans', color='white'),
            tickfont=dict(size=18, family='Merriweather Sans', color='white'),  # Increased tick font size
            ticks='outside',
            ticklen=5,
            tickwidth=2,
            tickcolor='white',
            gridcolor='rgba(0,0,0,0)',
            range=[0, np.max(solution.y)]
        ),
        template='plotly_dark',
        plot_bgcolor='#010131',  # Set plot background color
        paper_bgcolor='#010131',  # Set paper background color
        autosize=False,
        width=500,
        height=500
    )

    return fig

# Layout of the page
layout = html.Div([
    html.Div(id='reaction-inputs', children=[
        dbc.InputGroup([
            dbc.InputGroupText("Elementary Reaction:", style={'margin-left': '2px'}),
            dbc.Input(id={'type': 'reaction-input', 'index': 0}, placeholder='e.g., 2H2 + O2 -> 2H2O', type='text', style={'margin-right': '10px', 'margin-left': '10px', 'width': '500px'}),
            dbc.InputGroupText("Rate Constant:"),
            dbc.Input(id={'type': 'rate-constant-input', 'index': 0}, type='number', style={'margin-right': '10px', 'margin-left': '10px', 'width': '50px'})
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'})
    ], style={'margin-bottom': '10px'}),
    html.Div([
        dbc.Button("Add Reaction", id='add-reaction', n_clicks=0, style={'margin-right': '10px'}),
        dbc.Button("Remove Reaction", id='remove-reaction', n_clicks=0, style={'margin-right': '10px'}),
        dbc.Button("Confirm Reaction", id='confirm-reaction', n_clicks=0)
    ], style={'margin-bottom': '10px'}),
    html.Div(id='species-list', children=[]),  # Updated to display species
    html.Div(id='concentration-inputs', children=[], style={'margin-bottom': '0px'}),
    dbc.Button("Submit", id='submit-button', n_clicks=0, style={'display': 'none'}),
    html.Div(
        dcc.Graph(id='kinetics-graph', style={'display': 'none', 'width': '500px', 'height': '500px'}),
        style={'display': 'flex', 'justify-content': 'center'}  # Center the graph
    )
], style={'margin-left': '10px', 'margin-top': '10px'})

# Callbacks to handle input and generate the graph
@callback(
    Output('reaction-inputs', 'children'),
    Output('confirm-reaction', 'children'),  # Added output for button text
    Input('add-reaction', 'n_clicks'),
    Input('remove-reaction', 'n_clicks'),
    State('reaction-inputs', 'children')
)
def update_reaction_inputs(add_clicks, remove_clicks, reaction_inputs):
    ctx = dash.callback_context

    if not ctx.triggered:
        return reaction_inputs, "Confirm Reaction"

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-reaction' and add_clicks > 0:
        new_reaction_input = dbc.InputGroup([
            dbc.InputGroupText("Elementary Reaction:", style={'margin-left': '2px'}),
            dbc.Input(id={'type': 'reaction-input', 'index': add_clicks}, placeholder='e.g., 2H2 + O2 -> 2H2O', type='text', style={'margin-right': '10px', 'margin-left': '10px', 'width': '500px'}),
            dbc.InputGroupText("Rate Constant:"),
            dbc.Input(id={'type': 'rate-constant-input', 'index': add_clicks}, type='number', style={'margin-right': '10px', 'margin-left': '10px', 'width': '50px'})
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '5px'})
        reaction_inputs.append(new_reaction_input)

    if button_id == 'remove-reaction' and remove_clicks > 0 and len(reaction_inputs) > 1:
        reaction_inputs.pop()

    # Update button text based on the number of reaction inputs
    button_text = "Confirm Reaction" if len(reaction_inputs) == 1 else "Confirm Reactions"

    return reaction_inputs, button_text

@callback(
    Output('concentration-inputs', 'children'),
    Output('submit-button', 'style'),
    Output('species-list', 'children'),
    Input('confirm-reaction', 'n_clicks'),
    State({'type': 'reaction-input', 'index': dash.ALL}, 'value'),
    State({'type': 'rate-constant-input', 'index': dash.ALL}, 'value'),
    prevent_initial_call=True
)
def detect_species_and_input_concentrations(n_clicks, reactions, rate_constants):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, {'display': 'none'}, dash.no_update

    if n_clicks > 0 and any(reactions):
        valid_reactions = [r for r in reactions if r]
        unique_species = detect_unique_species_ordered(valid_reactions)
        
        concentration_inputs = [
            dbc.Col(
                html.Span("Initial Concentrations: "),
                width="auto",
                style={'display': 'flex', 'alignItems': 'center', 'marginRight': '10px'}
            )
        ]
        
        for species in unique_species:
            subscripted_species = subscript_numbers(species)
            concentration_inputs.append(
                dbc.Col([
                    html.Span(subscripted_species + [":"], style={'marginRight': '5px'}),
                    dbc.Input(
                        id={'type': 'concentration-input', 'index': species},
                        type='number',
                        style={'width': '60px', 'display': 'inline-block'}
                    )
                ], width="auto", style={'display': 'flex', 'alignItems': 'center', 'marginRight': '15px'})
            )
        
        row = dbc.Row(
            concentration_inputs,
            className="g-0",
            style={'display': 'flex', 'flexWrap': 'nowrap', 'overflowX': 'auto', 'marginBottom': '10px'}
        )
        
        return row, {'display': 'inline-block'}, dash.no_update
    return dash.no_update, {'display': 'none'}, dash.no_update

@callback(
    Output('kinetics-graph', 'figure'),
    Output('kinetics-graph', 'style'),  # Add output for graph style
    Input('submit-button', 'n_clicks'),
    State({'type': 'reaction-input', 'index': dash.ALL}, 'value'),
    State({'type': 'rate-constant-input', 'index': dash.ALL}, 'value'),
    State({'type': 'concentration-input', 'index': dash.ALL}, 'value')
)
def generate_graph(n_clicks, reactions, rate_constants, concentrations):
    # Check if all reactions, rate constants, and concentrations are not None
    if n_clicks > 0 and all(reactions) and all(rate_constants) and all(c is not None for c in concentrations):
        ks = list(map(float, rate_constants))
        
        # Convert concentrations list to a dictionary
        C0 = {concentration_id['id']['index']: str(concentration) for concentration_id, concentration in zip(dash.callback_context.states_list[2], concentrations)}
        
        # Strip out HTML tags from species names
        C0 = {re.sub(r'<.*?>', '', key): value for key, value in C0.items()}
        
        fig = reactiongraphing(reactions, ks, C0)
        return fig, {'display': 'block'}  # Show the graph
    return go.Figure(), {'display': 'none'}  # Hide the graph if conditions are not met