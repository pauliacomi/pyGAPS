# %%
import os
import adsutils

json_path = os.path.join(os.getcwd(), 'tests', 'data', 'isotherms_json')
json_file_paths = adsutils.util_get_file_paths(json_path, '.json')
isotherms = []
for filepath in json_file_paths:
    with open(filepath, 'r') as text_file:
        isotherms.append(adsutils.isotherm_from_json(text_file.read()))

#################################################################################
#################################################################################
#       Isotherm display
#
# %%
isotherm = isotherms[0]
isotherm.print_info()

# %%
print(isotherm.data())
print(isotherm.adsdata())
print(isotherm.desdata())
print(isotherm.has_ads())
print(isotherm.has_des())


#################################################################################
#################################################################################
# Isotherm plotting and comparison

# %%
sel_isotherms = isotherms

fig_title = sel_isotherms[0].sample_name
legend_list = ['sample_batch', 'user', 't_act']

enthalpy_max = None
loading_max = None
pressure_max = None

adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=False, fig_title=fig_title, legend_list=legend_list)

adsutils.plot_iso(sel_isotherms, plot_type='enthalpy', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)


#################################################################################
#################################################################################
# PyIAST isotherm modelling
#
# %%
isotherm = isotherms[1]
modelH = isotherm.get_model_isotherm("Henry")
modelH.name = "Henry"
modelL = isotherm.get_model_isotherm("Langmuir")
modelL.name = "Langmuir"
modelDL = isotherm.get_model_isotherm("DSLangmuir")
modelDL.name = "DS Langmuir"

adsutils.plot_iso([isotherm, modelH, modelL, modelDL],
                  plot_type='isotherm', branch=['ads'], logarithmic=False, color=True)

# %%
modelH.print_info()
