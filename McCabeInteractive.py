#%%
from TxyPxyxy import xy
import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.widgets import Slider, Button
import warnings
from numpy import RankWarning, VisibleDeprecationWarning

matplotlib.rcParams.update({'font.size': 13, 'lines.linewidth': 2.5})

def mccabeint(comp1, comp2, xd, xb, xf, P=None, T=None, R=None, q=None, ME=None):
    r"""
    Generate a interactive McCabe-Thiele plot for a binary mixture of two components.
    """
    # Suppress Errors
    warnings.simplefilter('ignore', RankWarning)
    warnings.simplefilter('ignore', VisibleDeprecationWarning)
    warnings.simplefilter('ignore', RuntimeWarning)

    # Check if P or T is given
    if P is None and T is None:
        print('Please provide either a temperature or a pressure')
        return None
    if P is not None:
        T = 273.15 # K
        Pgiven = True
    elif T is not None: # elif is necessary here since T is define right before this
        P = 1e5 # Pa
        Pgiven = False

    #Check for q and R value condition
    if q is not None and R is None:
        print('Please provide a R value')
        return None
    if R is not None and q is None:
        print('Please provide a q value')
        return None
    if q is not None and R is not None:
        if q == 1: # this will make the slopes infinity
            feedslope = 1e10
        else:
            feedslope = q/(q-1)
        if R == -1: # this will make the slopes infinity
            rectifyslope = 1e10
        else:
            rectifyslope = R/(R + 1)
        if feedslope == rectifyslope:
            print('Please provide valid q and R values')
            return None

    # Get the equilibrium data
    if Pgiven:
        xi, yi = xy(comp1, comp2, P = P, values = True, show = False)
    else:
        xi, yi = xy(comp1, comp2, T = T, values = True, show = False)

    # Fit a curve to the data
    z = np.polyfit(xi, yi, 30)
    p = np.poly1d(z)

    # Initialize the plot
    fig, ax1 = plt.subplots()
    fig.suptitle(f"""McCabe-Thiele Method for {comp1} + {comp2}""", fontweight='bold')
    plt.subplots_adjust(left  = 0.4)
    ax1.plot(xi, p(xi), xi, xi)
    ax1.set_ylim(0, 1)
    ax1.set_xlim(0, 1)
    ax1.set_xlabel(f'Liquid mole fraction {comp1}', fontsize = 16)
    ax1.set_ylabel(f'Vapor mole fraction {comp1}', fontsize = 16)
    #ax1.legend([r'$X_{e}$',r'$X_{EB}$'], loc='upper right')
    if ME is not None:
        ax1.plot(xi, p(xi), ls = '--', color = 'purple', label = 'Murphree Efficiency Curve')
    
    # Define and plot the feed, rectifying, and stripping lines and intersection
    if q is not None and R is not None:
        def rectifying(xval):
            return R/(R+1)*xval + xd/(R+1)
        def feed(xval):
            return q/(q-1)*xval - xf/(q-1)
        def feedrectintersection(xval):
            return q/(q-1)*xval - xf/(q-1) - R/(R+1)*xval - xd/(R+1)
        xguess = xf*q # q>1 means xsol > xf, and q<1 means xsol < xf
        if R == -1:
            xsol = xd
            ysol = feed(xsol)
        elif q == 1:
            xsol = xf
            ysol = rectifying(xsol)
        else:
            xsol = fsolve(feedrectintersection, xguess)  # fsolve returns an array, get the first element
            ysol = rectifying(xsol)

        # Ensure xsol and ysol are single values
        if isinstance(xsol, np.ndarray):
            xsol = xsol[0]
        if isinstance(ysol, np.ndarray):
            ysol = ysol[0]

        # Define the stripping line as the line from xb to the intersection of the rectifying line and the feed line
        def stripping(xval):
            return (ysol-xb)*(xval-xb)/(xsol-xb)+xb
        
        # Generate points for the lines using linspace
        xfeedtorect = np.linspace(xf, xsol, 100)
        yfeedtorect = (ysol-xf)*(xfeedtorect-xf)/(xsol-xf)+xf
        xdisttofeed = np.linspace(xd, xsol, 100)
        ydisttofeed = (ysol-xd)*(xdisttofeed-xd)/(xsol-xd)+xd
        xbottofeed = np.linspace(xb, xsol, 100)
        ybottofeed = (ysol-xb)*(xbottofeed-xb)/(xsol-xb)+xb

        # Plot the lines using the generated points with shortened variable names
        p1, = ax1.plot(xfeedtorect, yfeedtorect, color='red', label='Feed to Rectifying Line')
        p2, = ax1.plot(xdisttofeed, ydisttofeed, color='pink', label='Distillate to Feed Line')
        p3, = ax1.plot(xbottofeed, ybottofeed, color='green', label='Bottom to Feed Line')

    # Create sliders
    axcolor = 'lightgoldenrodyellow'
    ax_xd = plt.axes([0.1, 0.8, 0.2, 0.02], facecolor=axcolor)
    ax_xb = plt.axes([0.1, 0.75, 0.2, 0.02], facecolor=axcolor)
    ax_xf = plt.axes([0.1, 0.7, 0.2, 0.02], facecolor=axcolor)
    ax_q = plt.axes([0.1, 0.65, 0.2, 0.02], facecolor=axcolor)
    ax_R = plt.axes([0.1, 0.6, 0.2, 0.02], facecolor=axcolor)

    s_xd = Slider(ax_xd, 'xd', 0, 1, valinit=xd)
    s_xb = Slider(ax_xb, 'xb', 0, 1, valinit=xb)
    s_xf = Slider(ax_xf, 'xf', 0, 1, valinit=xf)
    s_q = Slider(ax_q, 'q', -2, 2, valinit=q)
    s_R = Slider(ax_R, 'R', 0, 10, valinit=R)

    # Update function
    def update(val):

        xd = s_xd.val
        xb = s_xb.val
        xf = s_xf.val
        q = s_q.val
        R = s_R.val

        if q is not None and R is not None:
            def rectifying(xval):
                return R/(R+1)*xval + xd/(R+1)
            def feed(xval):
                return q/(q-1)*xval - xf/(q-1)
            def feedrectintersection(xval):
                return q/(q-1)*xval - xf/(q-1) - R/(R+1)*xval - xd/(R+1)
            xguess = xf*q # q>1 means xsol > xf, and q<1 means xsol < xf
            if R == -1:
                xsol = xd
                ysol = feed(xsol)
            elif q == 1:
                xsol = xf
                ysol = rectifying(xsol)
            else:
                xsol = fsolve(feedrectintersection, xguess)  # fsolve returns an array, get the first element
                ysol = rectifying(xsol)

        # Update the data of the plot lines
        yfeedtorect = (ysol-xf)*(xfeedtorect-xf)/(xsol-xf)+xf
        ydisttofeed = (ysol-xd)*(xdisttofeed-xd)/(xsol-xd)+xd
        ybottofeed = (ysol-xb)*(xbottofeed-xb)/(xsol-xb)+xb
        p1.set_ydata(yfeedtorect)
        p2.set_ydata(ydisttofeed)
        p3.set_ydata(ybottofeed)
        fig.canvas.draw_idle()

    s_xd.on_changed(update)
    s_xb.on_changed(update)
    s_xf.on_changed(update)
    s_q.on_changed(update)
    s_R.on_changed(update)

    resetax = plt.axes([0.17, 0.85, 0.09, 0.05])
    button = Button(resetax, 'Reset variables', color='cornflowerblue', hovercolor='0.975')

    def reset(event):
        s_xd.reset()
        s_xb.reset()
        s_xf.reset()
        s_q.reset()
        s_R.reset()
        
    button.on_clicked(reset)    
    plt.show()

#%%
mccabeint('methanol', 'water', xd = 0.9, xb = 0.01, xf = 0.5, T = 300, q = 1.1, R = 1)
# divide by 0 at q=1 must fix
# %%
