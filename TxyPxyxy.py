#%%
from thermo import *
from thermo.unifac import DOUFSG, DOUFIP2016
import matplotlib.pyplot as plt
import numpy as np

def Txy(comp1, comp2, P = 1): # assume standard temp if none is given
    # Load constants and properties
    constants, properties = ChemicalConstantsPackage.from_IDs([comp1, comp2])
    # Objects are initialized at a particular condition
    P = P*1e5 # bar to Pa
    T = 273.15 # Assume an initial temperature guess
    zs = [.5, .5] # initital mole fraction of comp1 and comp2

    # Use Peng-Robinson for the vapor phase
    eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas} 
    gas = CEOSGas(PRMIX, HeatCapacityGases=properties.HeatCapacityGases, eos_kwargs=eos_kwargs) # available: 'PRMIX', 'VDWMIX', 'SRKMIX', 'RKMIX'

    # Configure the activity model
    GE = UNIFAC.from_subgroups(chemgroups=constants.UNIFAC_Dortmund_groups, version=1, T=T, xs=zs,
                            interaction_data=DOUFIP2016, subgroups=DOUFSG)
    # Configure the liquid model with activity coefficients
    liquid = GibbsExcessLiquid(
        VaporPressures=properties.VaporPressures,
        HeatCapacityGases=properties.HeatCapacityGases,
        VolumeLiquids=properties.VolumeLiquids,
        GibbsExcessModel=GE,
        equilibrium_basis='Psat', caloric_basis='Psat',
        T=T, P=P, zs=zs)

    # Create a flasher instance, assuming only vapor-liquid behavior
    flasher = FlashVL(constants, properties, liquid=liquid, gas=gas)
    z1, z2, Ts_dew, Ts_bubble = flasher.plot_Txy(P, pts=100, show = True, values = True)
    P = P/1e5
    plt.title(f'Txy diagram at %.2f bar' %P, fontsize = 16)
    plt.plot(z1, Ts_dew, label='Dew temperature, K')
    plt.plot(z1, Ts_bubble, label='Bubble temperature, K')
    plt.xlabel(f'Mole fraction {comp1}', fontsize = 16)
    plt.ylabel('Temperature, T(K)', fontsize = 16)
    plt.legend(loc='best', fontsize = 12)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.show()

def Pxy(comp1, comp2, T = 273.15): # assume standard temp if none is given
    # Load constants and properties
    constants, properties = ChemicalConstantsPackage.from_IDs([comp1, comp2])
    # Objects are initialized at a particular condition
    P = 1e5 # Assume a initial pressure guess in Pa
    zs = [.5, .5] # initital mole fraction of comp1 and comp2

    # Use Peng-Robinson for the vapor phase
    eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas} 
    gas = CEOSGas(PRMIX, HeatCapacityGases=properties.HeatCapacityGases, eos_kwargs=eos_kwargs) # available: 'PRMIX', 'VDWMIX', 'SRKMIX', 'RKMIX'

    # Configure the activity model
    GE = UNIFAC.from_subgroups(chemgroups=constants.UNIFAC_Dortmund_groups, version=1, T=T, xs=zs,
                            interaction_data=DOUFIP2016, subgroups=DOUFSG)
    # Configure the liquid model with activity coefficients
    liquid = GibbsExcessLiquid(
        VaporPressures=properties.VaporPressures,
        HeatCapacityGases=properties.HeatCapacityGases,
        VolumeLiquids=properties.VolumeLiquids,
        GibbsExcessModel=GE,
        equilibrium_basis='Psat', caloric_basis='Psat',
        T=T, P=P, zs=zs)

    # Create a flasher instance, assuming only vapor-liquid behavior
    flasher = FlashVL(constants, properties, liquid=liquid, gas=gas)
    z1, z2, Ps_dew, Ps_bubble = flasher.plot_Pxy(T, pts=100, show = True, values = True)
    Ps_dew = [Ps/1e5 for Ps in Ps_dew] # converting Pa to bar
    Ps_bubble = [Ps/1e5 for Ps in Ps_bubble] # converting Pa to bar
    plt.title(f'Pxy diagram at %s K' %T, fontsize = 16)
    plt.plot(z1, Ps_dew, label='Dew pressure, P (bar)')
    plt.plot(z1, Ps_bubble, label='Bubble pressure, P (bar)')
    plt.xlabel(f'Mole fraction {comp1}', fontsize = 16)
    plt.ylabel('Pressure, P(bar)', fontsize = 16)
    plt.legend(loc='best', fontsize = 12)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.show()

def xy(comp1, comp2, T = None, P = None, values = False, show = True):
    # Load constants and properties
    constants, properties = ChemicalConstantsPackage.from_IDs([comp1, comp2])
    if P is not None:
        T = 273.15 # K
        P = P*1e5 # bar to Pa
        Pgiven = True
    elif T is not None: # elif is necessary here since T is define right before this
        P = 1e5 # Pa
        Pgiven = False
    zs = [.5, .5] # initital mole fraction of comp1 and comp2

    # Use Peng-Robinson for the vapor phase
    eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas} 
    gas = CEOSGas(PRMIX, HeatCapacityGases=properties.HeatCapacityGases, eos_kwargs=eos_kwargs) # available: 'PRMIX', 'VDWMIX', 'SRKMIX', 'RKMIX'

    # Configure the activity model
    GE = UNIFAC.from_subgroups(chemgroups=constants.UNIFAC_Dortmund_groups, version=1, T=T, xs=zs,
                            interaction_data=DOUFIP2016, subgroups=DOUFSG)
    # Configure the liquid model with activity coefficients
    liquid = GibbsExcessLiquid(
        VaporPressures=properties.VaporPressures,
        HeatCapacityGases=properties.HeatCapacityGases,
        VolumeLiquids=properties.VolumeLiquids,
        GibbsExcessModel=GE,
        equilibrium_basis='Psat', caloric_basis='Psat',
        T=T, P=P, zs=zs)

    # Create a flasher instance, assuming only vapor-liquid behavior
    flasher = FlashVL(constants, properties, liquid=liquid, gas=gas)
    if Pgiven == False:
        z1, z2, x1_bubble, y1_bubble = flasher.plot_xy(T=T, pts=100, values = True, show = show)
    elif P:
        z1, z2, x1_bubble, y1_bubble = flasher.plot_xy(P=P, pts=100, values = True, show = show)
    if show:
        if Pgiven == False:
            plt.title(f'xy diagram at %s K'%T, fontsize = 16)
        elif Pgiven:
            plt.title(f'xy diagram at %.2f bar'%(P/1e5), fontsize = 16, visible = False)
        plt.plot(x1_bubble, y1_bubble, '-', label='liquid vs vapor composition')
        plt.plot([0, 1], [0, 1], '--')
        plt.axis((0,1,0,1))
        plt.xlabel(f'Liquid mole fraction {comp1}', fontsize = 16)
        plt.ylabel(f'Vapor mole fraction {comp1}', fontsize = 16)
        plt.legend(loc='best', fontsize = 12)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.show()
    if values:
        return x1_bubble, y1_bubble
    
# %% Examples
# Txy('acetic acid', 'acetone', P = 1e5)
# Pxy('methanol', 'acetone', T = 298)
# xy('methanol', 'water', T = 298, show = True) 
# x1, y1 = xy('p-xylene', 'methanol', T = 298, values = True) # use values = True to get the values of x and y
# %%
