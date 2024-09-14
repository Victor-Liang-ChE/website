from dash import dcc, html, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy.integrate import solve_ivp
import re

dash.register_page(__name__, path='/kinetics', name="Kinetics Graph")

# Function to generate the reaction graph
def reactiongraphing(reactions, ks, C0):
    # Check that the number of ks elements matches the number of reactions
    if len(ks) != len(reactions):
        raise ValueError("The number of rate constants does not match the number of reactions.")

    # Function to remove numerical coefficients from species names
    def remove_coefficients(species):
        return re.sub(r'^\d*\*?', '', species)

    # Extract unique species from reactions in the order they appear
    ordered_species = []
    unique_species = set()
    for reaction in reactions:
        reactants, products = reaction.split('=')
        reactant_species = [remove_coefficients(species) for species in reactants.split('+')]
        product_species = [remove_coefficients(species) for species in products.split('+')]
        for species in reactant_species + product_species:
            if species not in unique_species:
                unique_species.add(species)
                ordered_species.append(species)

    # Check that all unique species are present in C0
    if not unique_species.issubset(C0.keys()):
        missing_species = unique_species - set(C0.keys())
        raise ValueError(f"The following species are missing in C0: {missing_species}")

    # Define the system of ODEs
    def odes(t, y):
        dydt = np.zeros(len(ordered_species))
        concentrations = {species: y[i] for i, species in enumerate(ordered_species)}
        for i, reaction in enumerate(reactions):
            reactants, products = reaction.split('=')
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
    tolerance = 1e-4
    steady_state_time = t_span[1]
    for i in range(1, len(solution.t)):
        if np.all(np.abs(solution.y[:, i] - solution.y[:, i-1]) < tolerance):
            steady_state_time = solution.t[i]
            break

    # Create the plotly figure
    fig = go.Figure()
    for i, species in enumerate(ordered_species):
        fig.add_trace(go.Scatter(x=solution.t, y=solution.y[i], mode='lines', name=species))

    fig.update_layout(
        title='Concentration vs. Time',
        xaxis_title='Time',
        yaxis_title='Concentration',
        xaxis=dict(range=[0, steady_state_time]),
        yaxis=dict(range=[0, max(max(solution.y))]),
        template='plotly_dark'
    )

    return fig

# Layout of the page
layout = html.Div([
    html.H1("Kinetics Graph"),
    html.Div([
        dbc.InputGroup([
            dbc.InputGroupText("Reaction"),
            dbc.Input(id='reaction-input', placeholder='e.g., 2H2+O2=2H2O', type='text'),
            dbc.Button("Add Reaction", id='add-reaction', n_clicks=0)
        ]),
        html.Div(id='reaction-list', children=[]),
        dbc.InputGroup([
            dbc.InputGroupText("Rate Constants"),
            dbc.Input(id='rate-constants', placeholder='e.g., 1.5, 0.5', type='text')
        ]),
        dbc.InputGroup([
            dbc.InputGroupText("Initial Concentrations"),
            dbc.Input(id='initial-concentrations', placeholder='e.g., H2:1, O2:1, H2O:0', type='text')
        ]),
        dbc.Button("Submit", id='submit-button', n_clicks=0)
    ]),
    dcc.Graph(id='kinetics-graph')
])

# Callbacks to handle input and generate the graph
@callback(
    Output('reaction-list', 'children'),
    Input('add-reaction', 'n_clicks'),
    State('reaction-input', 'value'),
    State('reaction-list', 'children')
)
def update_reaction_list(n_clicks, reaction, reaction_list):
    if n_clicks > 0 and reaction:
        reaction_list.append(html.Div(reaction))
    return reaction_list

@callback(
    Output('kinetics-graph', 'figure'),
    Input('submit-button', 'n_clicks'),
    State('reaction-list', 'children'),
    State('rate-constants', 'value'),
    State('initial-concentrations', 'value')
)
def generate_graph(n_clicks, reaction_list, rate_constants, initial_concentrations):
    if n_clicks > 0:
        reactions = [reaction.children for reaction in reaction_list]
        ks = list(map(float, rate_constants.split(',')))
        C0 = dict(item.split(':') for item in initial_concentrations.split(','))
        C0 = {k: float(v) for k, v in C0.items()}
        fig = reactiongraphing(reactions, ks, C0)
        return fig
    return go.Figure()