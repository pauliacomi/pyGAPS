#%%
from os.path import expanduser
import adsutils

#################################################################################
#################################################################################
#       Excel import
#
#%%
xl_folder =  expanduser(r"~\OneDrive\Documents\PhD Documents\Python\python adsorption\tests\isotherms\n2 phys 77")
xl_paths = adsutils.xl_experiment_parser_paths(xl_folder)

isotherms = []

for path in xl_paths:
    data, info = adsutils.xl_experiment_parser(path)
    isotherm = adsutils.PointIsotherm(data, info,
                                      pressure_key="Pressure (bar)",
                                      loading_key="Loading (mmol/g)",
                                      enthalpy_key="Enthalpy (kJ/mol)")
    isotherms.append(isotherm)


#################################################################################
#################################################################################
#       Isotherm display
#
#%%

isotherm = isotherms[0]
isotherm.print_info()
#%%
isotherm.adsdata
#%%
isotherm.desdata


#################################################################################
#################################################################################
#       Database
#
#%%
db_path = expanduser(r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")
#%%
for isotherm in isotherms:
    adsutils.db_upload_experiment(db_path, isotherm)

#%%
isotherms = []
criteria = {
    'sname':        "MIL-100(Fe)",
    #'sbatch':       "",
    #'user':         "PI",
    't_exp':        303,
    #'t_act':        "",
    #'machine':      "",
    #'gas':          "C3H8",
    #'exp_type':     "",
    }
isotherms = adsutils.db_get_experiments(db_path, criteria)


#################################################################################
#################################################################################
# Isotherm plotting and comparison

#%%
#sel_isotherms = isotherms
sel_isotherms = list(filter(lambda x: x.gas == "CO", isotherms))

fig_title = sel_isotherms[0].name
legend_list = ['batch', 'user', 't_act']

enthalpy_max = 60
loading_max = None
pressure_max = None

adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)
adsutils.plot_iso(sel_isotherms, plot_type='enthalpy', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)



#%%
def plot_all_selected(s_isotherms, save, enthalpy_max, loading_max, pressure_max):
    """
    ## All selected isotherms on one isotherm graph, optional saving
    """
    save_folder = r'C:\Users\pauli\Desktop\Test'
    save = save

    title = s_isotherms[0].gas + " comparison"
    legend_list = ["batch", "t_act"]
    enthalpy_max = enthalpy_max
    loading_max = loading_max
    pressure_max = pressure_max

    fig_title = title
    img_title = save_folder + "\\" + title + ' isotherms.png'

    adsutils.plot_iso(s_isotherms, plot_type='iso-enth', branch='ads', path=img_title,
                      logarithmic=False, color=True, save=save,
                      y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                      fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

    fig_title = title + " log"
    img_title = save_folder + "\\" + title + ' log isotherms.png'

    adsutils.plot_iso(s_isotherms, plot_type='iso-enth', branch='ads', path=img_title,
                      logarithmic=True, color=True, save=save,
                      y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                      fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

    fig_title = title + " enthalpy"
    img_title = save_folder + "\\" + title + ' enthalpy.png'

    adsutils.plot_iso(s_isotherms, plot_type='enthalpy', branch='ads', path=img_title,
                      logarithmic=False, color=True, save=save,
                      y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=loading_max,
                      fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

########################

#%%
sel_isotherms = []
req_gas = ["CH4"]
for gas in req_gas:
    sel_isotherms = list(filter(lambda x: x.gas in gas, isotherms))
    plot_all_selected(sel_isotherms, False, None, None, None)


#%%
sel_isotherms = []
req_gas = ["CO2", "CO", "C2H6", "C3H6", "C3H8"]
for gas in req_gas:
    sel_isotherms = list(filter(lambda x: x.gas in gas, isotherms))
    plot_all_selected(sel_isotherms, False, None, None, None)


#%%
sel_isotherms = []
req_gas = ["KRICT01", "KRICT AlO Pellets"]
for gas in req_gas:
    sel_isotherms += list(filter(lambda x: x.batch == gas, isotherms))

print(len(sel_isotherms))

#%%
legend_list = ['batch', 'gas']

enthalpy_max = 100
loading_max = None
pressure_max = None

adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch='ads',
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)

#################################################################################
#################################################################################
# PyIAST isotherm modelling
#
#%%
isotherm = isotherms[8]
modelH = isotherm.get_model_isotherm("Henry")
modelH.name = "Henry"
modelL = isotherm.get_model_isotherm("Langmuir")
modelL.name = "Langmuir"
modelDL = isotherm.get_model_isotherm("DSLangmuir")
modelDL.name = "DS Langmuir"

adsutils.plot_iso({isotherm,modelH, modelL, modelDL}, plot_type='isotherm', branch='ads', logarithmic=False, color=True)


#################################################################################
#################################################################################
# Henrys constant calculations
#
#%%

isotherm = isotherms[2]
adsutils.calc_initial_henry(isotherm, max_adjrms=0.01, verbose=True)

#%%

import importlib
importlib.reload(adsutils)
importlib.reload(adsutils.isotherms.initial_henry)

isotherm = isotherms[48]
print(isotherm.adsdata)
adsutils.calc_initial_henry_virial(isotherm, verbose=True)

#%%
henrys = []
henrys_v = []
gasnames = []
gasvalues = []
t_acts =[]

for index, isotherm in enumerate(sel_isotherms):
    henry = adsutils.calc_initial_henry(isotherm, max_adjrms=0.01)
    henry_v = adsutils.calc_initial_henry_virial(isotherm)
    gas = adsutils.db_get_gas(db_path, name=isotherm.gas)

    henrys.append(henry)
    henrys_v.append(henry_v)
    gasnames.append(gas.name)
    gasvalues.append(gas.polarizability)
    t_acts.append(isotherm.t_act)
    print(index, gas.name, henry, henry_v)



#%%
import pandas as pd
import matplotlib.pyplot as plt

dfrm = pd.DataFrame({"gas" : gasnames, "henry" : henrys_v, "values" : gasvalues, "t_acts" : t_acts})
dfrm["t_acts"].value_counts()
dfrm[dfrm["gas"] == "CO"]

#%%
isotherms[62].print_info()

#%%

dfrm = pd.DataFrame({"gas" : gasnames, "henry" : henrys, "values" : gasvalues, "t_acts" : t_acts})
colors = {250:'red', 150:'blue'}

fig, axes = plt.subplots(1, 1, figsize=(8, 8))
axes.scatter(dfrm["values"], dfrm["henry"], marker='o', c=dfrm['t_acts'].apply(lambda x: colors[x]))

for label, x, y in zip(dfrm["gas"], dfrm["values"], dfrm["henry"]):
    axes.annotate(label,
                  xy=(x, y), xytext=(30, 0),
                  textcoords='offset points', ha='right', va='bottom',
                  bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.3),
                  arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

axes.set_yscale('log')

plt.show()
