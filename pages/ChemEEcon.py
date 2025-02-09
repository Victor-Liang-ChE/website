# I want to create a chemical engineering page for calculating simple interest rates, compounding interest, 
# EAR (with a maximum EAR comparison), NPV, cashflow visualization (with and without annuity, perpetuity), inflationary effects, 
# and depreciation

import dash
from dash import dcc, html, Input, Output, clientside_callback
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/chemeecon', name="Chemical Engineering Economics")

layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='dropdown-menu',
            options=[
                {'label': 'Compounding Interest', 'value': 'compounding_interest'},
                {'label': 'EAR and max EAR', 'value': 'ear'},
                {'label': 'NPV', 'value': 'npv'},
                {'label': 'Inflationary Effects', 'value': 'inflation'},
                {'label': 'Annuity', 'value': 'annuity'},
                {'label': 'Perpetuity', 'value': 'perpetuity'},
                {'label': 'Depreciation', 'value': 'depreciation'},
                {'label': 'Cashflow Visualization', 'value': 'cashflow'}  # New Perpetuity option
            ],
            value='compounding_interest',
            style={'width': '300px', 'color': 'black'}  # Set text color to black
        )
    ], style={'margin-bottom': '20px'}),
    html.Div(id='content', style={'margin-left': '0px', 'margin-right': '15px', 'margin-top': '15px', 'margin-bottom': '15px'})
])

@dash.callback(
    Output('content', 'children'),
    [Input('dropdown-menu', 'value')]
)
def display_content(selected_value):
    if selected_value == 'compounding_interest':
        return html.Div([
            html.Div([
                html.Div([
                    html.Label("Present Value:"),
                    dcc.Input(id='present-value-compound', type='number', value=1000, step=0.01, style={'margin-bottom': '10px'}),
                    html.Label("Number of Years:"),
                    dcc.Input(id='num-years-compound', type='number', value=1, min=1, max=1000000, step=1, style={'margin-bottom': '10px'}),
                    html.Label("Compounds per Year:"),
                    dcc.Input(id='compounds-per-year', type='number', value=1, min=1, max = 365, step=1, style={'margin-bottom': '10px'}),
                    html.Div([
                        html.Label("Interest Rate:"),
                        html.Span(id='interest-rate-display-compound', style={'margin-left': '10px'})
                    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'}),
                    html.Div([
                        dcc.Slider(
                            id='interest-rate-compound',
                            min=0,
                            max=100,
                            step=0.1,
                            value=5,
                            marks={i: f'{i}%' for i in range(0, 101, 10)},
                            updatemode='drag'
                        )
                    ], style={'margin-bottom': '10px'}),
                    dcc.Checklist(
                        id='compare-checkbox-compound',
                        options=[{'label': 'Compare with Simple Interest', 'value': 'compare'}],
                        value=[],
                        style={'margin-bottom': '10px'}
                    ),
                    html.Div(id='future-value-output-compound', style={'font-weight': 'bold', 'font-size': '24px'}),
                    html.Div(id='future-value-simple-output-compound', style={'font-weight': 'bold', 'font-size': '24px'}),
                    html.Div(id='difference-output-compound', style={'font-weight': 'bold', 'font-size': '24px'})
                ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
                dcc.Graph(id='future-value-graph-compound', style={'flex': '1', 'height': '600px', 'width': '600px'})
            ], style={'display': 'flex'})
        ])

    elif selected_value == 'ear':
        return html.Div([
            html.Div([
                html.Div([
                    html.Label("Number of Compounds:"),
                    dcc.Input(id='num-compounds', type='number', value=1, max=1000000, step=1, style={'margin-bottom': '10px'}),
                    html.Div([
                        html.Label("Annual Interest Rate:"),
                        html.Span(id='interest-rate-display-ear', style={'margin-left': '10px'})
                    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'}),

                    html.Div([
                        dcc.Slider(
                            id='interest-rate-ear',
                            min=0,
                            max=100,
                            step=0.1,
                            value=5,
                            marks={i: f'{i}%' for i in range(0, 101, 10)},
                            updatemode='drag'
                        )
                    ], style={'margin-bottom': '10px'}),

                    dcc.Checklist(
                        id='compare-checkbox-ear',
                        options=[{'label': 'Compare with Maximum EAR', 'value': 'compare'}],
                        value=[],
                        style={'margin-bottom': '10px'}
                    ),
                    html.Div(id='ear-output', style={'font-weight': 'bold', 'font-size': '24px'}),
                    html.Div(id='max-ear-output', style={'font-weight': 'bold', 'font-size': '24px'}),
                    html.Div(id='difference-output-ear', style={'font-weight': 'bold', 'font-size': '24px'})
                ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
                dcc.Graph(id='ear-graph', style={'flex': '1', 'height': '600px', 'width': '600px'})
            ], style={'display': 'flex'})
        ])
    
        # Update the NPV section in the display_content function to include a graph
    
    elif selected_value == 'npv':
        return html.Div([
        html.Div([
            html.Div([
                html.Label("Present Value:"),
                dcc.Input(id='npv-present-value', type='number', value=1000, min=0, step=0.01, style={'margin-bottom': '10px'}),

                html.Label("Number of Years:"),
                dcc.Input(id='npv-years', type='number', value=1, min=1, step=1, style={'margin-bottom': '10px'}),

                html.Label("Discount Rate:"),
                html.Span(id='npv-discount-rate-display', style={'margin-left': '10px'}),

                # Wrap the Slider in a Div to apply styling
                html.Div([
                    dcc.Slider(
                        id='npv-discount-rate',
                        min=0,
                        max=100,
                        step=0.1,
                        value=5,
                        marks={i: f'{i}%' for i in range(0, 101, 10)},
                        updatemode='drag'
                    )
                ], style={'margin-bottom': '10px'}),

                html.Div(id='npv-future-value', style={'font-weight': 'bold', 'font-size': '24px'})
            ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
            dcc.Graph(id='npv-graph', style={'flex': '1', 'height': '600px', 'width': '600px'})
        ], style={'display': 'flex'})
    ])

    elif selected_value == 'annuity':
        return html.Div([
        html.Div([
            html.Div([
                html.Label("Present Value:"),
                dcc.Input(id='annuity-present-value', type='number', value=1000, min=0, step=0.01, style={'margin-bottom': '10px'}),

                html.Label("Number of Years:"),
                dcc.Input(id='annuity-years', type='number', value=10, min=1, step=1, style={'margin-bottom': '10px'}),

                html.Label("Annual Interest Rate:"),
                html.Span(id='annuity-interest-rate-display', style={'margin-left': '10px'}),

                html.Div([
                    dcc.Slider(
                        id='annuity-interest-rate',
                        min=0,
                        max=100,
                        step=0.1,
                        value=5,
                        marks={i: f'{i}%' for i in range(0, 101, 10)},
                        updatemode='drag'
                    )
                ], style={'margin-bottom': '10px'}),

                html.Div(id='annuity-payment', style={'font-weight': 'bold', 'font-size': '24px'})
            ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
            dcc.Graph(id='annuity-graph', style={'flex': '1', 'height': '600px', 'width': '600px'})
        ], style={'display': 'flex'})
    ])

    elif selected_value == 'perpetuity':
        return html.Div([
        html.Div([
            html.Div([
                html.Label("Uniform Cash Flow:"),
                dcc.Input(id='perpetuity-cash-flow', type='number', value=1000, min=0, step=0.01, style={'margin-bottom': '10px'}),

                html.Label("Annual Interest Rate:"),
                html.Span(id='perpetuity-interest-rate-display', style={'margin-left': '10px'}),

                html.Div([
                    dcc.Slider(
                        id='perpetuity-interest-rate',
                        min=0.1,
                        max=100,
                        step=0.1,
                        value=5,
                        marks={i: f'{i}%' for i in range(0, 101, 10)},
                        updatemode='drag'
                    )
                ], style={'margin-bottom': '10px'}),

                html.Div(id='perpetuity-present-value', style={'font-weight': 'bold', 'font-size': '24px'})
            ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
            dcc.Graph(id='perpetuity-graph', style={'flex': '1', 'height': '600px', 'width': '600px'})
        ], style={'display': 'flex'})
    ])
    
    elif selected_value == 'inflation':
        return html.Div([
            html.Div([
                html.Div([
                    html.Label("Present Value:"),
                    dcc.Input(id='inflation-pv', type='number', value=1000, min=0, step=0.01, style={'margin-bottom': '10px'}),
    
                    html.Label("Number of Years:"),
                    dcc.Input(id='inflation-years', type='number', value=10, min=1, step=1, style={'margin-bottom': '10px'}),
    
                    html.Label("Annual Interest Rate:"),
                    html.Span(id='inflation-interest-rate-display', style={'margin-left': '10px'}),
                    
                    html.Div([
                        dcc.Slider(
                            id='inflation-interest-rate',
                            min=0,
                            max=100,
                            step=0.1,
                            value=5,
                            marks={i: f'{i}%' for i in range(0, 101, 10)},
                            updatemode='drag'
                        )
                    ], style={'margin-bottom': '10px'}),

                    html.Label("Inflation Rate:"),
                    html.Span(id='inflation-display', style={'margin-left': '10px'}),
    
                    html.Div([
                        dcc.Slider(
                            id='inflation-rate',
                            min=0,
                            max=100,
                            step=0.1,
                            value=2,
                            marks={i: f'{i}%' for i in range(0, 101, 10)},
                            updatemode='drag'
                        )
                    ], style={'margin-bottom': '10px'}),
    
                    html.Div(id='future-purchasing-power', style={'font-weight': 'bold', 'font-size': '24px'})
                ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
                dcc.Graph(id='inflationary-effects-graph', style={'flex': '1', 'height': '600px', 'width': '600px'})
            ], style={'display': 'flex'})
        ])
    
    elif selected_value == 'depreciation':
        return html.Div([
            html.Div([
                html.Label("FCI:"),
                dcc.Input(id='depreciation-fci', type='number', value=10000, min=0, step=0.01, style={'margin-bottom': '10px'}),
                html.Label("Equipment Life (years):"),
                dcc.Input(id='depreciation-life', type='number', value=10, min=1, step=1, style={'margin-bottom': '10px'}),
                html.Div([
                    html.Label("Salvage Value:"),
                    dcc.Input(id='depreciation-salvage', type='number', value=1000, min=0, step=0.01, style={'margin-bottom': '10px'})
                ]),
                html.Label("Depreciation Method:"),
                dcc.RadioItems(
                    id='depreciation-method',
                    options=[
                        {'label': 'Straight Line', 'value': 'straight'},
                        {'label': 'MACRS', 'value': 'macrs'}
                    ],
                    value='straight',
                    inline=True,
                    style={'margin-bottom': '10px'}
                ),
                dcc.Checklist(
                    id='compare-checkbox-depreciation',
                    options=[{'label': 'Overlay both methods for comparison', 'value': 'compare'}],
                    value=[],
                    style={'margin-bottom': '10px'}
                ),
                html.Div(id='depreciation-output', style={'font-weight': 'bold', 'font-size': '24px'}),
                html.Div(id='macrs-depreciation-output', style={'font-weight': 'bold', 'font-size': '24px'})  # Add this line
            ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column', 'gap': '10px'}),
            dcc.Graph(id='depreciation-graph', style={'flex': '1', 'height': '600px', 'width': '600px'})
        ], style={'display': 'flex'})
    
########################### EAR ###########################

clientside_callback(
    """
    function(num_compounds, interest_rate, compare) {
        if (num_compounds === null || interest_rate === null) {
            return ["", "", "", {}];
        }

        var ear = Math.pow(1 + (interest_rate / 100) / num_compounds, num_compounds) - 1;
        var max_ear = Math.exp(interest_rate / 100) - 1;

        if (isNaN(ear) || isNaN(max_ear)) {
            return ["", "", "", {}];
        }

        var ear_text =
            "Effective Annual Rate (EAR): " +
            (ear * 100).toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }) + "%";
        var max_ear_text = compare.includes("compare")
            ? "Maximum EAR: " +
              (max_ear * 100).toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
              }) + "%"
            : "";
        var difference_text = compare.includes("compare")
            ? "Difference: " +
              ((max_ear - ear) * 100).toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
              }) + "%"
            : "";

        var compounds = Array.from({ length: num_compounds + 1 }, (_, i) => i);
        var ears = compounds.map(
            (compound) => Math.pow(1 + (interest_rate / 100) / compound, compound) - 1
        );

        var graph_data = {
            data: [
                {
                    x: compounds,
                    y: ears,
                    type: "line",
                    name: "Effective Annual Rate (EAR)",
                    line: { color: "yellow" }
                }
            ],
            layout: {
                title: {
                    text: "Effective Annual Rate vs. Number of Compounds",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: {
                        text: "Number of Compounds",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,  // Increased tick length
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: {
                        text: "Effective Annual Rate (EAR) (%)",  // Updated title to indicate percentage
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,  // Increased tick length
                    tickwidth: 2,
                    tickcolor: "white",
                    tickformat: ",.0%"  // Format ticks as percentages
                },
                legend: {
                    x: 0.10,
                    y: 0.95,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                margin: { l: 90, r: 10, t: 40, b: 50 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131",
                shapes: compare.includes("compare")
                    ? [
                          {
                              type: "line",
                              x0: 0,
                              y0: max_ear,
                              x1: num_compounds,
                              y1: max_ear,
                              line: {
                                  color: "red",
                                  width: 2,
                                  dash: "dash"
                              }
                          }
                      ]
                    : []
            }
        };

        return [
            ear_text,
            max_ear_text,
            difference_text,
            graph_data
        ];
    }
    """,
    [
        Output("ear-output", "children"),
        Output("max-ear-output", "children"),
        Output("difference-output-ear", "children"),
        Output("ear-graph", "figure")
    ],
    [
        Input("num-compounds", "value"),
        Input("interest-rate-ear", "value"),
        Input("compare-checkbox-ear", "value")
    ]
)

clientside_callback(
    """
    function(interest_rate) {
        if (interest_rate === null) {
            return "";
        }
        return `${interest_rate.toFixed(1)}%`;
    }
    """,
    Output('interest-rate-display-ear', 'children'),
    [Input('interest-rate-ear', 'value')]
)

########################### Compounding and Simple ###########################

# Update clientside_callback for Compounding and Simple Interest to include compounds per year
clientside_callback(
    """
    function(present_value, num_years, compounds_per_year, interest_rate, compare) {
        if (present_value === null || num_years === null || compounds_per_year === null || interest_rate === null) {
            return ["", "", "", {}];
        }
        if (num_years <= 0 || compounds_per_year <= 0) {
            return ["", "", "", {}];
        }

        var total_periods = num_years * compounds_per_year;
        var period_rate = (interest_rate / 100) / compounds_per_year;
        var future_value_compound = present_value * Math.pow(1 + period_rate, total_periods);
        var future_value_simple = present_value * (1 + num_years * (interest_rate / 100));

        // Helper function to abbreviate numbers and format with commas
        function abbreviateNumber(num) {
            if (num >= 1e93) return '∞';
            const suffixes = [
                { value: 1e93, symbol: 'Tg' },
                { value: 1e90, symbol: 'Nvg' },
                { value: 1e87, symbol: 'Ovg' },
                { value: 1e84, symbol: 'Spvg' },
                { value: 1e81, symbol: 'Sxvg' },
                { value: 1e78, symbol: 'Qvg' },
                { value: 1e75, symbol: 'Qavg' },
                { value: 1e72, symbol: 'Qav' },
                { value: 1e69, symbol: 'Dvg' },
                { value: 1e66, symbol: 'Uvg' },
                { value: 1e63, symbol: 'Vg' },
                { value: 1e60, symbol: 'Nvg' },
                { value: 1e57, symbol: 'Ocdc' },
                { value: 1e54, symbol: 'Spvg' },
                { value: 1e51, symbol: 'Sxdc' },
                { value: 1e48, symbol: 'Qidc' },
                { value: 1e45, symbol: 'Qadc' },
                { value: 1e42, symbol: 'Tdc' },
                { value: 1e39, symbol: 'Ddc' },
                { value: 1e36, symbol: 'Udc' },
                { value: 1e33, symbol: 'Dc' },
                { value: 1e30, symbol: 'Nm' },
                { value: 1e27, symbol: 'Oc' },
                { value: 1e24, symbol: 'Sp' },
                { value: 1e21, symbol: 'Sx' },
                { value: 1e18, symbol: 'Qi' },
                { value: 1e15, symbol: 'Qa' },
                { value: 1e12, symbol: 'T' },
                { value: 1e9, symbol: 'B' },
                { value: 1e6, symbol: 'M' },
                { value: 1e3, symbol: 'K' }
            ];

            for (let i = 0; i < suffixes.length; i++) {
                if (num >= suffixes[i].value && num < 1e93) {
                    return (num / suffixes[i].value).toFixed(2) + suffixes[i].symbol;
                }
            }
            return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        var future_value_compound_text = "Future Value: $" + abbreviateNumber(future_value_compound);
        var future_value_simple_text = compare.includes("compare")
            ? "Future Value (Simple): $" + abbreviateNumber(future_value_simple)
            : "";
        var difference_text = compare.includes("compare")
            ? "Difference: $" + abbreviateNumber(future_value_compound - future_value_simple)
            : "";

        // Generate x-axis values in years (each period corresponds to 1/compounds_per_year year)
        var x_values = Array.from({ length: total_periods + 1 }, (_, x) => x / compounds_per_year);
        var future_values_compound = Array.from({ length: total_periods + 1 }, (_, x) => present_value * Math.pow(1 + period_rate, x));
        var future_values_simple = x_values.map(function(t) {
            return present_value * (1 + (interest_rate / 100) * t);
        });

        var graph_data = {
            data: [
                {
                    x: x_values,
                    y: future_values_compound,
                    type: "line",
                    name: "Future Value (Compound)",
                    line: { color: "yellow" }
                }
            ],
            layout: {
                title: {
                    text: "Future Value vs. Number of Years",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: {
                        text: "Years",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: {
                        text: "Future Value ($)",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                legend: {
                    x: 0.10,
                    y: 0.95,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                margin: { l: 70, r: 10, t: 40, b: 50 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131"
            }
        };

        if (compare.includes("compare")) {
            graph_data.data.push({
                x: x_values,
                y: future_values_simple,
                type: "line",
                name: "Future Value (Simple)",
                line: { color: "red" }
            });
        }

        return [
            future_value_compound_text,
            future_value_simple_text,
            difference_text,
            graph_data
        ];
    }
    """,
    [
        Output("future-value-output-compound", "children"),
        Output("future-value-simple-output-compound", "children"),
        Output("difference-output-compound", "children"),
        Output("future-value-graph-compound", "figure")
    ],
    [
        Input("present-value-compound", "value"),
        Input("num-years-compound", "value"),
        Input("compounds-per-year", "value"), 
        Input("interest-rate-compound", "value"),
        Input("compare-checkbox-compound", "value")
    ]
)

clientside_callback(
    """
    function(interest_rate) {
        if (interest_rate === null) {
            return "";
        }
        return `${interest_rate.toFixed(1)}%`;
    }
    """,
    Output('interest-rate-display-compound', 'children'),
    [Input('interest-rate-compound', 'value')]
)

########################### NPV ###########################

clientside_callback(
    """
    function(presentValue, years, discountRate) {
        if(!presentValue || !years || discountRate === null) {
            return {};
        }

        var yearList = Array.from({ length: years + 1 }, (_, i) => i);
        var futureValues = yearList.map(
            (year) => presentValue / Math.pow(1 + (discountRate / 100), year)
        );

        var graph_data = {
            data: [
                {
                    x: yearList,
                    y: futureValues,
                    type: "line",
                    name: "Future Value",
                    line: { color: "yellow" }
                }
            ],
            layout: {
                title: {
                    text: "Future Value vs. Number of Years",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: {
                        text: "Number of Years",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,          // Increased tick length
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: {
                        text: "Future Value, F ($)",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,          // Increased tick length
                    tickwidth: 2,
                    tickcolor: "white",
                    tickformat: ",.2f"    // Format y-axis as dollars with two decimals
                },
                legend: {
                    x: 0.10,
                    y: 0.95,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                margin: { l: 70, r: 10, t: 40, b: 50 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131"
            }
        };

        return graph_data;
    }
    """,
    Output('npv-graph', 'figure'),
    [
        Input('npv-present-value', 'value'),
        Input('npv-years', 'value'),
        Input('npv-discount-rate', 'value')
    ]
)

clientside_callback(
    """
    function(presentValue, years, discountRate) {
        if(!presentValue || !years || discountRate === null) {
            return "";
        }
        var F = presentValue / Math.pow(1 + (discountRate / 100), years);
        return "Future Value: $" + F.toFixed(2);
    }
    """,
    Output('npv-future-value', 'children'),
    [
        Input('npv-present-value', 'value'),
        Input('npv-years', 'value'),
        Input('npv-discount-rate', 'value')
    ]
)

clientside_callback(
    """
    function(rate) {
        if(rate === null) {
            return "";
        }
        return rate.toFixed(1) + "%";
    }
    """,
    Output('npv-discount-rate-display', 'children'),
    Input('npv-discount-rate', 'value')
)

########################### Annuity ###########################
# change it to solve for annuity, not the present value
# include a compounds per year input box since the full equation is P = A*()


clientside_callback(
    """
    function(pv_input, max_years, interest_rate) {
        if (!pv_input || !max_years || interest_rate === null) {
            return ["", {}];
        }
        var r = interest_rate / 100;
        // Create an array of years from 1 to max_years
        var years_range = Array.from({ length: max_years }, (_, i) => i + 1);
        // Compute required annuity payment for each year in the range
        var annuity_payments = years_range.map(function(n) {
            if (r === 0) {
                return pv_input / n;
            } else {
                return pv_input * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
            }
        });
        // Get the payment corresponding to the selected max_years value
        var selected_annuity = annuity_payments[annuity_payments.length - 1];
        var result_text = "Required Annuity Payment: $" + selected_annuity.toFixed(2);
        var graph_data = {
            data: [
                {
                    x: years_range,
                    y: annuity_payments,
                    type: "line",
                    name: "Annuity Payment",
                    line: { color: "yellow" }
                },
                {
                    x: [max_years],
                    y: [selected_annuity],
                    type: "markers",
                    marker: { color: "red", size: 10 },
                    name: "Selected Number of Years"
                }
            ],
            layout: {
                title: {
                    text: "Required Annuity Payment vs. Number of Years",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: {
                        text: "Number of Years",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: {
                        text: "Required Annuity Payment ($)",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white",
                    tickformat: ",.2f"
                },
                legend: {
                    x: 0.10,
                    y: 0.95,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                margin: { l: 100, r: 10, t: 40, b: 50 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131"
            }
        };
        return [
            result_text,
            graph_data
        ];
    }
    """,
    [
        Output("annuity-payment", "children"),
        Output("annuity-graph", "figure")
    ],
    [
        Input("annuity-present-value", "value"),
        Input("annuity-years", "value"),
        Input("annuity-interest-rate", "value")
    ]
)


clientside_callback(
    """
    function(interest_rate) {
        if(interest_rate === null) {
            return "";
        }
        return interest_rate.toFixed(1) + "%";
    }
    """,
    Output('annuity-interest-rate-display', 'children'),
    Input('annuity-interest-rate', 'value')
)

########################### Perpetuity ###########################

clientside_callback(
    """
    function(cash_flow, interest_rate) {
        if(!cash_flow || interest_rate === null || interest_rate === 0) {
            return ["", {}];
        }

        var r = interest_rate / 100;
        var pv = cash_flow / r;

        var cash_flow_values = Array.from({ length: 100 }, (_, i) => (i + 1) * (cash_flow / 10));
        var pv_values = cash_flow_values.map(cf => cf / r);

        var graph_data = {
            data: [
                {
                    x: cash_flow_values,
                    y: pv_values,
                    type: "line",
                    name: "Present Value",
                    line: { color: "yellow" }
                }
            ],
            layout: {
                title: {
                    text: "Present Value vs. Uniform Cash Flow",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: {
                        text: "Uniform Cash Flow ($)",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: {
                        text: "Present Value, PV ($)",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white",
                    tickformat: ",.2f"
                },
                legend: {
                    x: 0.10,
                    y: 0.95,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                margin: { l: 120, r: 10, t: 40, b: 50 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131"
            }
        };

        return [
            "Present Value: $" + pv.toFixed(2),
            graph_data
        ];
    }
    """,
    [
        Output("perpetuity-present-value", "children"),
        Output("perpetuity-graph", "figure")
    ],
    [
        Input("perpetuity-cash-flow", "value"),
        Input("perpetuity-interest-rate", "value")
    ]
)

clientside_callback(
    """
    function(interest_rate) {
        if(interest_rate === null) {
            return "";
        }
        return interest_rate.toFixed(1) + "%";
    }
    """,
    Output('perpetuity-interest-rate-display', 'children'),
    Input('perpetuity-interest-rate', 'value')
)

########################### Inflation ###########################
clientside_callback(
    """
    function(pv, years, interest_rate, inflation_rate) {
        if(!pv || !years || interest_rate === null || inflation_rate === null || inflation_rate == -interest_rate) {
            return ["", {}];
        }

        var r = interest_rate / 100;
        var inf = inflation_rate / 100;

        var future_purchasing_power = pv * Math.pow(1 + (r - inf) / (1 + inf), years);

        var years_list = Array.from({ length: years + 1 }, (_, y) => y);
        var fpp_list = years_list.map(y => pv * Math.pow(1 + (r - inf) / (1 + inf), y));

        var graph_data = {
            data: [
                {
                    x: years_list,
                    y: fpp_list,
                    type: "line",
                    name: "Future Purchasing Power",
                    line: { color: "yellow" }
                }
            ],
            layout: {
                title: {
                    text: "Future Purchasing Power vs. Number of Years",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: {
                        text: "Number of Years",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: {
                        text: "Future Purchasing Power ($)",
                        font: { size: 18, color: "white", family: "Merriweather Sans" }
                    },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white",
                    tickformat: ",.2f"
                },
                legend: {
                    x: 0.10,
                    y: 0.95,
                    xanchor: "left",
                    yanchor: "top",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                margin: { l: 140, r: 10, t: 40, b: 60 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131"
            }
        };

        return [
            "Future Purchasing Power: $" + future_purchasing_power.toFixed(2),
            graph_data
        ];
    }
    """,
    [
        Output("future-purchasing-power", "children"),
        Output("inflationary-effects-graph", "figure")
    ],
    [
        Input("inflation-pv", "value"),
        Input("inflation-years", "value"),
        Input("inflation-interest-rate", "value"),
        Input("inflation-rate", "value")
    ]
)

clientside_callback(
    """
    function(interest_rate) {
        if(interest_rate === null) {
            return "";
        }
        return interest_rate.toFixed(1) + "%";
    }
    """,
    Output('inflation-interest-rate-display', 'children'),
    Input('inflation-interest-rate', 'value')
)

clientside_callback(
    """
    function(inflation_rate) {
        if(inflation_rate === null) {
            return "";
        }
        return inflation_rate.toFixed(1) + "%";
    }
    """,
    Output('inflation-display', 'children'),
    Input('inflation-rate', 'value')
)

########################### Depreciation ###########################
clientside_callback(
    """
    function(fci, life, salvage, method, compare) {
        if (fci == null || life == null || life <= 0) {
            return ["", "", {}];
        }
        // Total periods = equipment life + 1 (to account for the half-year convention)
        var totalPeriods = life + 1;
        // Array of period numbers for x-axis (1 to totalPeriods)
        var years = [];
        for (var i = 1; i <= totalPeriods; i++) {
            years.push(i);
        }
        // Compute straight-line annual depreciation (for the straight-line curve)
        var straight = [];
        var straight_val = (fci - salvage) / life;
        // For each full year, add the equal depreciation amount...
        for (var i = 0; i < life; i++) {
            straight.push(straight_val);
        }
        // ...and add a final period (zero depreciation) so that the arrays line up.
        straight.push(straight_val);

        // Compute MACRS using dynamic switching from double-declining to straight-line.
        var macrs = [];
        var bookValue = fci;
        var r = 2 / life; // double-declining rate
        var switched = false;
        var fullYearDep = 0;
        // Period 1: half-year of double-declining
        var d = bookValue * r * 0.5;
        macrs.push(d);
        bookValue -= d;
        // For periods 2 to totalPeriods
        for (var period = 2; period <= totalPeriods; period++) {
            if (!switched) {
                var dblDecline = bookValue * r;
                // Remaining periods (including the final half-year)
                var remainingPeriods = (totalPeriods - period) + 0.5;
                var straightLine_est = bookValue / remainingPeriods;
                if (dblDecline > straightLine_est) {
                    d = dblDecline;
                    macrs.push(d);
                    bookValue -= d;
                } else {
                    // Switch to straight-line depreciation.
                    switched = true;
                    fullYearDep = straightLine_est;
                    // For the remaining full periods (except the final half-year period)
                    for (var j = period; j < totalPeriods; j++) {
                        macrs.push(fullYearDep);
                        bookValue -= fullYearDep;
                    }
                    // Final period: half of the full-year depreciation
                    macrs.push(fullYearDep * 0.5);
                    bookValue -= fullYearDep * 0.5;
                    break;
                }
            }
        }
        // (Optional) If no switch occurred, the loop completes naturally

        // Build output text summarizing total depreciation.
        // Compute totals based on the full arrays.
        var total_straight = straight.reduce((a, b) => a + b, 0);
        var total_macrs = macrs.reduce((a, b) => a + b, 0);
        var straight_summary = "";
        var macrs_summary = "";
        if (compare.includes("compare")) {
            straight_summary = "Total Depreciation (Straight Line): $" + total_straight.toFixed(2);
            macrs_summary = "Total Depreciation (MACRS): $" + total_macrs.toFixed(2);
        } else {
            if (method === "straight") {
                straight_summary = "Total Depreciation (Straight Line): $" + total_straight.toFixed(2);
            } else {
                macrs_summary = "Total Depreciation (MACRS): $" + total_macrs.toFixed(2);
            }
        }
        // Build graph data.
        var graph_data = {
            data: [],
            layout: {
                title: {
                    text: "Depreciation vs. Equipment Life",
                    x: 0.5,
                    xanchor: "center",
                    font: { color: "white", family: "Merriweather Sans" }
                },
                xaxis: {
                    title: { text: "Year", font: { size: 18, color: "white", family: "Merriweather Sans" } },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                yaxis: {
                    title: { text: "Annual Depreciation ($)", font: { size: 18, color: "white", family: "Merriweather Sans" } },
                    tickfont: { size: 14, color: "white", family: "Merriweather Sans" },
                    ticks: "outside",
                    ticklen: 10,
                    tickwidth: 2,
                    tickcolor: "white"
                },
                margin: { l: 70, r: 10, t: 40, b: 50 },
                plot_bgcolor: "#010131",
                paper_bgcolor: "#010131",
                legend: { font: { color: "white", family: "Merriweather Sans" } }
            }
        };
        if (compare.includes("compare")) {
            graph_data.data.push({
                x: years,
                y: straight,
                type: "line",
                name: "Straight Line",
                line: { color: "red" }
            });
            graph_data.data.push({
                x: years,
                y: macrs,
                type: "line",
                name: "MACRS",
                line: { color: "yellow" }
            });
        } else {
            if (method === "straight") {
                graph_data.data.push({
                    x: years,
                    y: straight,
                    type: "line",
                    name: "Straight Line",
                    line: { color: "red" }
                });
            } else {
                graph_data.data.push({
                    x: years,
                    y: macrs,
                    type: "line",
                    name: "MACRS",
                    line: { color: "yellow" }
                });
            }
        }
        return [straight_summary, macrs_summary, graph_data];
    }
    """,
    [
        Output("depreciation-output", "children"),
        Output("macrs-depreciation-output", "children"),   
        Output("depreciation-graph", "figure")
    ],
    [
        Input("depreciation-fci", "value"),
        Input("depreciation-life", "value"),
        Input("depreciation-salvage", "value"),
        Input("depreciation-method", "value"),
        Input("compare-checkbox-depreciation", "value")
    ]
)