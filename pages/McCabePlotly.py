#%%
import numpy as np
import plotly.graph_objects as go
import dash
from scipy.optimize import fsolve
from dash import dcc, html, Input, Output, callback
from TxyPxyxy import xy

dash.register_page(__name__, path='/', name="McCabe-Thiele Plot")

def mccabeint(comp1, comp2, P=None, T=None, xd=0.9, xb=0.1, xf=0.5, q=0.5, R=2):

    if P is None and T is None:
        print('Please provide either a temperature or a pressure')
        return None
    if P is not None:
        T = 273.15
        Pgiven = True
    elif T is not None:
        P = 1e5
        Pgiven = False

    if q is not None and R is not None:
        if q == 1:
            feedslope = 1e10
        else:
            feedslope = q/(q-1)

        if R == -1:
            rectifyslope = 1e10
        else:
            rectifyslope = R/(R + 1)

    xi, yi = xy(comp1, comp2, T=T, values=True, show=False)
    z = np.polyfit(xi, yi, 10)
    p = np.poly1d(z)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=xi, y=p(xi), mode='lines', name='Equilibrium Line', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=xi, y=xi, mode='lines', name='y=x Line', line=dict(color='black')))

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

        fig.add_trace(go.Scatter(x=xdisttofeed, y=ydisttofeed, mode='lines', name='Rectifying Section', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=xfeedtorect, y=yfeedtorect, mode='lines', name='Feed Section', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=xbottofeed, y=ybottofeed, mode='lines', name='Stripping Section', line=dict(color='green')))

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

    fig.add_trace(go.Scatter(x=xhorzsegmentlist, y=yhorzsegmentlist, mode='lines', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=xrectvertsegmentlist, y=yrectvertsegmentlist, mode='lines', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=xstripvertsegmentlist, y=ystripvertsegmentlist, mode='lines', line=dict(color='black')))

    fig.add_trace(go.Scatter(x=[xd, xb, xf], y=[xd, xb, xf], mode='markers', marker=dict(color='red')))

    fig.update_layout(title=f"McCabe-Thiele Method for {comp1} + {comp2}",
                      xaxis_title=f'Liquid mole fraction {comp1}',
                      yaxis_title=f'Vapor mole fraction {comp1}',
                      xaxis=dict(range=[0, 1], constrain='domain'),
                      yaxis=dict(range=[0, 1], scaleanchor='x', scaleratio=1))

    return fig

layout = html.Div([
    html.H1("McCabe-Thiele Method Plot"),
    dcc.Graph(id='mccabe-plot'),
    html.Label('Distillate composition (xd):'),
    dcc.Slider(id='xd-slider', 
               min=0, 
               max=1, 
               step=0.01, 
               value=0.9, 
               marks={i: str(round(i, 1)) for i in np.arange(0, 1.1, 0.1)}, 
               updatemode='drag'),
    html.Label('Bottoms composition (xb):'),
    dcc.Slider(id='xb-slider', 
               min=0, 
               max=1, 
               step=0.01, 
               value=0.1, 
               marks={i: str(round(i, 1)) for i in np.arange(0, 1.1, 0.1)}, 
               updatemode='drag'),
    html.Label('Feed composition (xf):'),
    dcc.Slider(id='xf-slider', 
               min=0, 
               max=1, 
               step=0.01, 
               value=0.5, 
               marks={i: str(round(i, 1)) for i in np.arange(0, 1.1, 0.1)}, 
               updatemode='drag'),
    html.Label('Feed quality (q):'),
    dcc.Slider(id='q-slider', 
               min=-2, 
               max=2, 
               step=0.1, 
               value=0.5, 
               marks={i: str(round(i, 1)) for i in np.arange(-2, 2.1, 0.2)}, 
               updatemode='drag'),
    html.Label('Reflux ratio (R):'),
    dcc.Slider(id='R-slider', 
               min=0, 
               max=10, 
               step=0.1, 
               value=2, 
               marks={i: str(round(i, 1)) for i in np.arange(0, 10.1, 0.5)}, 
               updatemode='drag')
])

@callback(
    Output('mccabe-plot', 'figure'),
    Input('xd-slider', 'value'),
    Input('xb-slider', 'value'),
    Input('xf-slider', 'value'),
    Input('q-slider', 'value'),
    Input('R-slider', 'value')
)
def update_plot(xd, xb, xf, q, R):
    return mccabeint(comp1='methanol', comp2='water', T=300, xd=xd, xb=xb, xf=xf, q=q, R=R)
