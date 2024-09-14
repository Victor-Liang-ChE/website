#%%
import numpy as np
import plotly.graph_objects as go
import dash
from scipy.optimize import fsolve
from dash import dcc, html, Input, Output, callback, Patch, State, callback_context
from TxyPxyxy import xy

dash.register_page(__name__, path='/mccabe', name="McCabe-Thiele Interactive Plot")

fig = go.Figure()
comp1 = "methanol"
comp2 = "water"
T = 300
P = None
xd = 0.9
xb = 0.1
xf = 0.5
q = 0.5
R = 2

if q is not None and R is not None:
    if q == 1:
        feedslope = 1e10
    else:
        feedslope = q/(q-1)

    if R == -1:
        rectifyslope = 1e10
    else:
        rectifyslope = R/(R + 1)

xi, yi = xy(comp1, comp2, T=T, values=True, show=False) # this function lags the app, do not use in the slider callbacks
z = np.polyfit(xi, yi, 20)
p = np.poly1d(z)

fig.add_trace(go.Scatter(x=xi, y=p(xi), mode='lines', name='Equilibrium Line', line=dict(color='yellow'), uid='equilibrium'))
fig.add_trace(go.Scatter(x=xi, y=xi, mode='lines', name='y=x Line', line=dict(color='white'), uid='yx'))

if q is not None and R is not None:
    def rectifying(xval):
        return R/(R+1)*xval + xd/(R+1)
    def feed(xval):
        return q/(q-1)*xval - xf/(q-1)
    def feedrectintersection(xval):
        return q/(q-1)*xval - xf/(q-1) - R/(R+1)*xval - xd/(R+1)
    xguess = xf*q
    if R == -1:
        R = -1 + 1e-10
        xsol = xd
        ysol = feed(xsol)
    elif q == 1:
        q == 1 + 1e-10
        xsol = xf
        ysol = rectifying(xsol)
    else:
        xsol = fsolve(feedrectintersection, xguess)
        ysol = rectifying(xsol)

    if isinstance(xsol, np.ndarray):
        xsol = xsol[0]
    if isinstance(ysol, np.ndarray):
        ysol = ysol[0]

    def stripping(xval):
        return (ysol-xb)*(xval-xb)/(xsol-xb)+xb

    xfeedtorect = np.linspace(xf, xsol, 100)
    yfeedtorect = (ysol-xf)*(xfeedtorect-xf)/(xsol-xf)+xf
    xdisttofeed = np.linspace(xd, xsol, 100)
    ydisttofeed = (ysol-xd)*(xdisttofeed-xd)/(xsol-xd)+xd
    xbottofeed = np.linspace(xb, xsol, 100)
    ybottofeed = (ysol-xb)*(xbottofeed-xb)/(xsol-xb)+xb

    fig.add_trace(go.Scatter(x=xdisttofeed, y=ydisttofeed, mode='lines', name='Rectifying Section', line=dict(color='orange'), uid='rectifying'))
    fig.add_trace(go.Scatter(x=xfeedtorect, y=yfeedtorect, mode='lines', name='Feed Section', line=dict(color='red'), uid='feed'))
    fig.add_trace(go.Scatter(x=xbottofeed, y=ybottofeed, mode='lines', name='Stripping Section', line=dict(color='green'), uid='stripping'))

stages = 0
x = xd
y = xd
xs = [x]
ys = [y]
xhorzsegment = []
yhorzsegment = []
xrectvertsegment = []
yrectvertsegment = []
xstripvertsegment = []
ystripvertsegment = []
feedstage = 1
while x > xb:
    def difference(xval):
        return p(xval) - y
    intersect = fsolve(difference, 0)
    if intersect > x or intersect == x:
        print('Cannot perform McCabe-Thiele Method as equilibrium curve is below y=x at distillation composition')
        break
    if isinstance(x, np.ndarray):
        x = x[0]
    if isinstance(y, np.ndarray):
        y = y[0]
    if isinstance(intersect, np.ndarray):
        intersect = intersect[0]

    xhorzsegment.append(np.linspace(x, intersect, 100))
    yhorzsegment.append(np.linspace(y, y, 100))

    if intersect > xsol:
        xrectvertsegment.append(np.linspace(intersect, intersect, 100))
        yrectvertsegment.append(np.linspace(y, rectifying(intersect), 100))
        x = intersect
        y = rectifying(intersect)
        feedstage += 1
    else:
        xstripvertsegment.append(np.linspace(intersect, intersect, 100))
        ystripvertsegment.append(np.linspace(y, stripping(intersect), 100))
        x = intersect
        y = stripping(intersect)
    stages += 1

xhorzsegmentlist = [x for sublist in xhorzsegment for x in sublist]
yhorzsegmentlist = [y for sublist in yhorzsegment for y in sublist]
xrectvertsegmentlist = [x for sublist in xrectvertsegment for x in sublist]
yrectvertsegmentlist = [y for sublist in yrectvertsegment for y in sublist]
xstripvertsegmentlist = [x for sublist in xstripvertsegment for x in sublist]
ystripvertsegmentlist = [y for sublist in ystripvertsegment for y in sublist]

fig.add_trace(go.Scatter(x=xhorzsegmentlist, y=yhorzsegmentlist, mode='lines', line=dict(color='white'), uid='horzsegment', showlegend=False))
fig.add_trace(go.Scatter(x=xrectvertsegmentlist, y=yrectvertsegmentlist, mode='lines', line=dict(color='white'), uid='rectvertsegment', showlegend=False))
fig.add_trace(go.Scatter(x=xstripvertsegmentlist, y=ystripvertsegmentlist, mode='lines', line=dict(color='white'), uid='stripvertsegment', showlegend=False))

fig.add_trace(go.Scatter(x=[xd, xb, xf], y=[xd, xb, xf], mode='markers', marker=dict(color='red'), uid='markers'))

fig.update_layout(
    title=dict(
        text=f"McCabe-Thiele Method for {comp1} + {comp2} at {T} K",
        x=0.5,  # Center the title
        xanchor='center',
        font=dict(color='white', family='Merriweather')  # Set title text color to white and font to Merriweather
    ),
    xaxis=dict(
        title=f'Liquid mole fraction {comp1}',
        range=[0, 1],
        constrain='domain',
        title_font=dict(size=18, color='white', family='Merriweather'),  # Increase x-axis title font size, set color to white, and font to Merriweather
        showgrid=False,  # Remove x-axis grid
        ticks='outside',  # Add tick marks
        ticklen=5,  # Length of tick marks
        tickwidth=2,  # Width of tick marks
        tickcolor='white',  # Color of tick marks
        tickfont=dict(size=14, color='white', family='Merriweather'),  # Set x-axis tick labels size, color to white, and font to Merriweather
        dtick=0.1  # Set tick increment to 0.1
    ),
    yaxis=dict(
        title=f'Vapor mole fraction {comp1}',
        range=[0, 1],
        scaleanchor='x',
        scaleratio=1,
        title_font=dict(size=18, color='white', family='Merriweather'),  # Increase y-axis title font size, set color to white, and font to Merriweather
        showgrid=False,  # Remove y-axis grid
        ticks='outside',  # Add tick marks
        ticklen=5,  # Length of tick marks
        tickwidth=2,  # Width of tick marks
        tickcolor='white',  # Color of tick marks
        tickfont=dict(size=14, color='white', family='Merriweather'),  # Set y-axis tick labels size, color to white, and font to Merriweather
        dtick=0.1  # Set tick increment to 0.1
    ),
    legend=dict(
        x=0.75,  # Position legend inside the graph
        y=0.1,
        xanchor='left',
        yanchor='bottom',
        font=dict(color='white', family='Merriweather')  # Set legend text color to white and font to Merriweather
    ),
    margin=dict(l=10, r=10, t=40, b=10),  # Reduce margins to remove whitespace
    plot_bgcolor='#010131',  # Set plot background color to dark blue from CSS
    paper_bgcolor='#010131'  # Set paper background color to dark blue from CSS
)

layout = html.Div([
    html.Div([
        html.Div([
            html.Label('Component 1:', style={'display': 'inline-block', 'margin-right': '10px'}),
            dcc.Input(id='comp1-input', type='text', value='methanol', style={'width': '100%', 'margin-bottom': '10px'}),
            html.Label('Component 2:', style={'display': 'inline-block', 'margin-right': '10px'}),
            dcc.Input(id='comp2-input', type='text', value='water', style={'width': '100%', 'margin-bottom': '10px'}),
            html.Label('Temperature (K):', style={'display': 'inline-block', 'margin-right': '10px'}),
            dcc.Input(id='temperature-input', type='number', value=300, style={'width': '100%', 'margin-bottom': '10px'}),
            html.Label('Pressure (Pa):', style={'display': 'inline-block', 'margin-right': '10px'}),
            dcc.Input(id='pressure-input', type='number', style={'width': '100%', 'margin-bottom': '10px'}),
            html.Div([
                html.Button('Submit', id='submit-button', n_clicks=0, style={'margin-bottom': '10px'}),
                dcc.ConfirmDialog(
                    id='confirm-dialog',
                    message='',
                ),
            ], style={'margin-bottom': '10px'}),
            html.Label('Distillate composition (xd):', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Span(id='xd-display', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Div([
                dcc.Slider(id='xd-slider', 
                           min=0, 
                           max=1, 
                           step=0.01, 
                           value=0.9, 
                           marks={i: str(round(i, 1)) for i in np.arange(0, 1, 0.1)}, 
                           updatemode='drag')
            ], style={'margin-bottom': '5px'}),
            html.Label('Bottoms composition (xb):', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Span(id='xb-display', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Div([
                dcc.Slider(id='xb-slider', 
                           min=0, 
                           max=1, 
                           step=0.01, 
                           value=0.1, 
                           marks={i: str(round(i, 1)) for i in np.arange(0, 1, 0.1)}, 
                           updatemode='drag')
            ], style={'margin-bottom': '5px'}),
            html.Label('Feed composition (xf):', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Span(id='xf-display', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Div([
                dcc.Slider(id='xf-slider', 
                           min=0, 
                           max=1, 
                           step=0.01, 
                           value=0.5, 
                           marks={i: str(round(i, 1)) for i in np.arange(0, 1, 0.1)}, 
                           updatemode='drag')
            ], style={'margin-bottom': '5px'}),
            html.Label('Feed quality (q):', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Span(id='q-display', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Div([
                dcc.Slider(id='q-slider', 
                           min=-2, 
                           max=2, 
                           step=0.1, 
                           value=0.5, 
                           marks={i: str(round(i, 1)) for i in np.arange(-2, 2, 0.5)}, 
                           updatemode='drag')
            ], style={'margin-bottom': '5px'}),
            html.Label('Reflux ratio (R):', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Span(id='R-display', style={'display': 'inline-block', 'margin-right': '10px'}),
            html.Div([
                dcc.Slider(id='R-slider', 
                           min=0, 
                           max=10, 
                           step=0.1, 
                           value=2, 
                           marks={i: str(round(i, 1)) for i in np.arange(0, 10, 0.5)}, 
                           updatemode='drag')
            ], style={'margin-bottom': '5px'}),
        ], style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),
        html.Div([
            dcc.Graph(id='mccabe-plot', figure=fig),
            html.Div(id='stages-output', style={'margin-top': '20px'}, children=f"Number of stages: {stages}"),
            html.Div(id='feed-stages-output', style={'margin-top': '20px'}, children=f"Feed stage: {feedstage}"),
        ], style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),
    ], style={'display': 'flex'}),
    dcc.Store(id='xi-store', data=xi), # the data here is the initial value and will be changed by the slider
    dcc.Store(id='yi-store', data=yi),
])

@callback(
    Output('confirm-dialog', 'displayed'),
    Output('confirm-dialog', 'message'),
    Output('xi-store', 'data'),
    Output('yi-store', 'data'),
    Output('mccabe-plot', 'figure'),
    Input('submit-button', 'n_clicks'),
    State('comp1-input', 'value'),
    State('comp2-input', 'value'),
    State('temperature-input', 'value'),
    State('pressure-input', 'value'),
    prevent_initial_call=True
)
def compute_xy(n_clicks, comp1, comp2, T, P):
    fig = go.Figure()
    if n_clicks > 0:
        # Update the layout of the figure with the new title
        if T is not None:
            figtitle = f"McCabe-Thiele Method for {comp1} + {comp2} at {T} K"
        else:
            figtitle = f"McCabe-Thiele Method for {comp1} + {comp2} at {P} Pa"
        fig.update_layout(
            title=figtitle,
            xaxis_title=f'Liquid mole fraction {comp1}',
            yaxis_title=f'Vapor mole fraction {comp1}',
        xaxis=dict(
            title=f'Liquid mole fraction {comp1}',
            range=[0, 1],
            constrain='domain',
            title_font=dict(size=18, color='white', family='Merriweather'),  # Increase x-axis title font size, set color to white, and font to Merriweather
            showgrid=False,  # Remove x-axis grid
            ticks='outside',  # Add tick marks
            ticklen=5,  # Length of tick marks
            tickwidth=2,  # Width of tick marks
            tickcolor='white',  # Color of tick marks
            tickfont=dict(size=14, color='white', family='Merriweather'),  # Set x-axis tick labels size, color to white, and font to Merriweather
            dtick=0.1  # Set tick increment to 0.1
        ),
        yaxis=dict(
            title=f'Vapor mole fraction {comp1}',
            range=[0, 1],
            scaleanchor='x',
            scaleratio=1,
            title_font=dict(size=18, color='white', family='Merriweather'),  # Increase y-axis title font size, set color to white, and font to Merriweather
            showgrid=False,  # Remove y-axis grid
            ticks='outside',  # Add tick marks
            ticklen=5,  # Length of tick marks
            tickwidth=2,  # Width of tick marks
            tickcolor='white',  # Color of tick marks
            tickfont=dict(size=14, color='white', family='Merriweather'),  # Set y-axis tick labels size, color to white, and font to Merriweather
            dtick=0.1  # Set tick increment to 0.1
        ))
        if T is not None and P is not None:
            return True, 'If you input both temperature and pressure, the graphing will not work.', dash.no_update, dash.no_update
        if not comp1 or not comp2 or (T is None and P is None):
            return True, 'You must input both components and at least a temperature or a pressure to graph.', dash.no_update, dash.no_update
        
        if P is None:
            xi, yi = xy(comp1, comp2, T=T, values=True, show=False)
        else:
            xi, yi = xy(comp1, comp2, P=P, values=True, show=False)
        
        return False, '', xi, yi, fig
    return False, '', dash.no_update, dash.no_update, fig

@callback(
    Output('mccabe-plot', 'figure', allow_duplicate=True),
    Output('stages-output', 'children'),
    Output('feed-stages-output', 'children'),
    Input('xd-slider', 'value'),
    Input('xb-slider', 'value'),
    Input('xf-slider', 'value'),
    Input('q-slider', 'value'),
    Input('R-slider', 'value'), # add inputs from text boxes for components?
    Input('xi-store', 'data'),
    Input('yi-store', 'data'),
    State('comp1-input', 'value'),
    State('comp2-input', 'value'),
    State('temperature-input', 'value'),
    State('pressure-input', 'value'),
    prevent_initial_call=True
)
def update_plot(xd, xb, xf, q, R, xi, yi, comp1, comp2, T, P): # use Patch to update the plot
    z = np.polyfit(xi, yi, 20)
    p = np.poly1d(z)

    patched_figure = Patch()
    patched_figure['data'] = []

    patched_figure['data'].extend([
        {'name': 'Equilibrium Line', 'x': xi, 'y': p(xi), 'mode': 'lines', 'line': {'color': 'yellow'}},
        {'name': 'y=x Line', 'x': xi, 'y': xi, 'mode': 'lines', 'line': {'color': 'white'}}
    ])

    if q is not None and R is not None:
        def rectifying(xval):
            return R/(R+1)*xval + xd/(R+1)
        def feed(xval):
            return q/(q-1)*xval - xf/(q-1)
        def feedrectintersection(xval):
            return q/(q-1)*xval - xf/(q-1) - R/(R+1)*xval - xd/(R+1)
        xguess = xf*q
        if R == -1:
            R = -1 + 1e-10
            xsol = xd
            ysol = feed(xsol)
        elif q == 1:
            q == 1 + 1e-10
            xsol = xf
            ysol = rectifying(xsol)
        else:
            xsol = fsolve(feedrectintersection, xguess)
            ysol = rectifying(xsol)

        if isinstance(xsol, np.ndarray):
            xsol = xsol[0]
        if isinstance(ysol, np.ndarray):
            ysol = ysol[0]

        def stripping(xval):
            return (ysol-xb)*(xval-xb)/(xsol-xb)+xb

        xfeedtorect = np.linspace(xf, xsol, 100)
        yfeedtorect = (ysol-xf)*(xfeedtorect-xf)/(xsol-xf)+xf
        xdisttofeed = np.linspace(xd, xsol, 100)
        ydisttofeed = (ysol-xd)*(xdisttofeed-xd)/(xsol-xd)+xd
        xbottofeed = np.linspace(xb, xsol, 100)
        ybottofeed = (ysol-xb)*(xbottofeed-xb)/(xsol-xb)+xb
        patched_figure['data'].extend([
            {
                'name': 'Rectifying Section',
                'x': xdisttofeed,
                'y': ydisttofeed,
                'mode': 'lines',
                'line': {'color': 'orange'}
            },
            {
                'name': 'Feed Section',
                'x': xfeedtorect,
                'y': yfeedtorect,
                'mode': 'lines',
                'line': {'color': 'red'}
            },
            {
                'name': 'Stripping Section',
                'x': xbottofeed,
                'y': ybottofeed,
                'mode': 'lines',
                'line': {'color': 'green'}
            }
        ])
        stages = 0
        x = xd
        y = xd
        xhorzsegment = []
        yhorzsegment = []
        xrectvertsegment = []
        yrectvertsegment = []
        xstripvertsegment = []
        ystripvertsegment = []
        feedstage = 1
        while x > xb:
            def difference(xval):
                return p(xval) - y
            intersect = fsolve(difference, 0)
            if intersect > x or intersect == x:
                print('Cannot perform McCabe-Thiele Method as equilibrium curve is below y=x at distillation composition')
                break
            if isinstance(x, np.ndarray):
                x = x[0]
            if isinstance(y, np.ndarray):
                y = y[0]
            if isinstance(intersect, np.ndarray):
                intersect = intersect[0]

            xhorzsegment.append(np.linspace(x, intersect, 100))
            yhorzsegment.append(np.linspace(y, y, 100))

            if intersect > xsol:
                xrectvertsegment.append(np.linspace(intersect, intersect, 100))
                yrectvertsegment.append(np.linspace(y, rectifying(intersect), 100))
                x = intersect
                y = rectifying(intersect)
                feedstage += 1
            else:
                yend = (ysol-xb)*(intersect-xb)/(xsol-xb)+xb
                xstripvertsegment.append(np.linspace(intersect, intersect, 100))
                if yend < intersect:
                    ystripvertsegment.append(np.linspace(y, intersect, 100))
                else:
                    ystripvertsegment.append(np.linspace(y, (ysol-xb)*(intersect-xb)/(xsol-xb)+xb, 100))
                x = intersect
                y = (ysol-xb)*(x-xb)/(xsol-xb)+xb
            stages += 1

        xhorzsegmentlist = [x for sublist in xhorzsegment for x in sublist]
        yhorzsegmentlist = [y for sublist in yhorzsegment for y in sublist]
        xrectvertsegmentlist = [x for sublist in xrectvertsegment for x in sublist]
        yrectvertsegmentlist = [y for sublist in yrectvertsegment for y in sublist]
        xstripvertsegmentlist = [x for sublist in xstripvertsegment for x in sublist]
        ystripvertsegmentlist = [y for sublist in ystripvertsegment for y in sublist]

    patched_figure['data'].extend([
        {
            'name': 'horzsegment',
            'x': xhorzsegmentlist,
            'y': yhorzsegmentlist,
            'mode': 'lines',
            'line': {'color': 'white'},
            'showlegend': False
        },
        {
            'name': 'rectvertsegment',
            'x': xrectvertsegmentlist,
            'y': yrectvertsegmentlist,
            'mode': 'lines',
            'line': {'color': 'white'},
            'showlegend': False
        },
        {
            'name': 'stripvertsegment',
            'x': xstripvertsegmentlist,
            'y': ystripvertsegmentlist,
            'mode': 'lines',
            'line': {'color': 'white'},
            'showlegend': False
        }
    ])
    if T is not None:
        figtitle = f"McCabe-Thiele Method for {comp1} + {comp2} at {T} K"
    else:
        figtitle = f"McCabe-Thiele Method for {comp1} + {comp2} at {P} Pa"
    patched_figure['layout'].update(
        title=dict(
            text=figtitle,
            x=0.5,  # Center the title
            xanchor='center',
            font=dict(color='white', family='Merriweather')  # Set title text color to white and font to Merriweather
        ),
        legend=dict(
            x=0.75,  # Position legend inside the graph
            y=0.1,
            xanchor='left',
            yanchor='bottom',
            font=dict(color='white', family='Merriweather')  # Set legend text color to white and font to Merriweather
        ),
        margin=dict(l=10, r=10, t=40, b=10),  # Reduce margins to remove whitespace
        plot_bgcolor='#010131',  # Set plot background color to dark blue from CSS
        paper_bgcolor='#010131'  # Set paper background color to dark blue from CSS
    )

    return patched_figure, f"Number of stages: {stages}", f"Feed stage: {feedstage}"

@callback(
    Output('xd-display', 'children'),
    Output('xb-display', 'children'),
    Output('xf-display', 'children'),
    Output('q-display', 'children'),
    Output('R-display', 'children'),
    Input('xd-slider', 'value'),
    Input('xb-slider', 'value'),
    Input('xf-slider', 'value'),
    Input('q-slider', 'value'),
    Input('R-slider', 'value')
)
def update_slider_values(xd, xb, xf, q, R):
    xd_display = f'{xd:.2f}'
    xb_display = f'{xb:.2f}'
    xf_display = f'{xf:.2f}'
    q_display = f'{q:.1f}'
    R_display = f'{R:.1f}'
    return xd_display, xb_display, xf_display, q_display, R_display

@callback(
    Output('xd-slider', 'value'),
    Output('xf-slider', 'value'),
    Output('xb-slider', 'value'),
    Input('xd-slider', 'value'),
    Input('xf-slider', 'value'),
    Input('xb-slider', 'value')
)
def enforce_constraints(xd, xf, xb):
    ctx = callback_context
    if not ctx.triggered:
        return xd, xf, xb

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'xd-slider':
        if xd < xf:
            xd = xf + 0.01
    elif triggered_id == 'xf-slider':
        if xf > xd:
            xf = xd - 0.01
        if xf < xb:
            xf = xb + 0.01
    elif triggered_id == 'xb-slider':
        if xb > xf:
            xb = xf - 0.01

    return xd, xf, xb