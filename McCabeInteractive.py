#%%
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.widgets import Slider, Button
from McCabe import mccabe  # Assuming the function is defined in McCabe.py

matplotlib.rcParams.update({'font.size': 13, 'lines.linewidth': 2.5})

# Initial parameters
comp1 = 'acetone'
comp2 = 'benzene'
xd_init = 0.95
xb_init = 0.05
xf_init = 0.5
R_init = 1.5
q_init = 1.0
P = 1  # Assuming pressure is given

# Create the figure and the axis
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.4, bottom=0.4)

# Initial plot
mccabe(comp1, comp2, xd_init, xb_init, xf=xf_init, P=P, R=R_init, q=q_init, showplot=False)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Add sliders for parameters
axcolor = 'lightgoldenrodyellow'
ax_xd = plt.axes([0.1, 0.3, 0.2, 0.02], facecolor=axcolor)
ax_xb = plt.axes([0.1, 0.25, 0.2, 0.02], facecolor=axcolor)
ax_xf = plt.axes([0.1, 0.2, 0.2, 0.02], facecolor=axcolor)
ax_R = plt.axes([0.1, 0.15, 0.2, 0.02], facecolor=axcolor)
ax_q = plt.axes([0.1, 0.1, 0.2, 0.02], facecolor=axcolor)

s_xd = Slider(ax_xd, r'$x_d$', 0.5, 1.0, valinit=xd_init, valfmt='%1.2f')
s_xb = Slider(ax_xb, r'$x_b$', 0.0, 0.5, valinit=xb_init, valfmt='%1.2f')
s_xf = Slider(ax_xf, r'$x_f$', 0.0, 1.0, valinit=xf_init, valfmt='%1.2f')
s_R = Slider(ax_R, r'$R$', 1.0, 5.0, valinit=R_init, valfmt='%1.2f')
s_q = Slider(ax_q, r'$q$', 0.0, 2.0, valinit=q_init, valfmt='%1.2f')

# Update function to refresh the plot
def update_plot(val):
    xd = s_xd.val
    xb = s_xb.val
    xf = s_xf.val
    R = s_R.val
    q = s_q.val
    ax.clear()
    mccabe(comp1, comp2, xd, xb, xf=xf, P=P, R=R, q=q, showplot=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.canvas.draw_idle()

# Attach update function to sliders
s_xd.on_changed(update_plot)
s_xb.on_changed(update_plot)
s_xf.on_changed(update_plot)
s_R.on_changed(update_plot)
s_q.on_changed(update_plot)

# Add reset button
resetax = plt.axes([0.17, 0.35, 0.09, 0.05])
button = Button(resetax, 'Reset', color='cornflowerblue', hovercolor='0.975')

def reset(event):
    s_xd.reset()
    s_xb.reset()
    s_xf.reset()
    s_R.reset()
    s_q.reset()

button.on_clicked(reset)

# Initial plot
update_plot(None)

plt.show()
# %%
