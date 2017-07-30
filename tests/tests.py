# %%
import os
import adsutils


#################################################################################
#       Excel import | dataimport/excelinterface.py
#################################################################################
#
# %% Get test folder
xl_folder = os.getcwd() + r'\tests\excel'
# %% Find files
xl_paths = adsutils.xl_experiment_parser_paths(
    xl_folder)
print(xl_paths)
# %% Import them
isotherms = []

for path in xl_paths:
    data, info = adsutils.xl_experiment_parser(path)
    isotherm = adsutils.PointIsotherm(data, info,
                                      pressure_key="Pressure (bar)",
                                      loading_key="Loading (mmol/g)",
                                      enthalpy_key="Enthalpy (kJ/mol)")
    isotherms.append(isotherm)

#################################################################################
#       Database import | dataimport/sqlinterface.py
#################################################################################
#
# %%
db_path = os.path.expanduser(
    r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")

# %%
isotherms = []
criteria = {
    'sname':        "UiO-66(Zr)",
    # 'sbatch':       "",
    # 'user':         "",
    't_exp':        303,
    # 't_act':        "",
    # 'machine':      "",
    'gas':          "N2",
    # 'exp_type':     "",
}
isotherms = adsutils.db_get_experiments(db_path, criteria)

# %%
samples = adsutils.db_get_samples(db_path)
adsutils.SAMPLE_LIST = samples


#################################################################################
#       Isotherm class | classes/pointisotherm.py
#################################################################################
#
# %%
isotherm = isotherms[0]
isotherm.print_info()
# %%
print(isotherm.adsdata())
print(isotherm.desdata())
print(isotherm.has_ads())
print(isotherm.has_des())
print(isotherm.pressure_ads())
print(isotherm.loading_ads())
print(isotherm.enthalpy_ads())
print(isotherm.pressure_des())
print(isotherm.loading_des())
print(isotherm.enthalpy_des())
print(isotherm.pressure_all())
print(isotherm.loading_all())
print(isotherm.enthalpy_all())

for isotherm in isotherms:
    isotherm.convert_adsorbent_mode("mass")

for isotherm in isotherms:
    isotherm.convert_adsorbent_mode("mass")


#################################################################################
# Isotherm plotting and comparison
#################################################################################
#
# %%
legend_list = ['name']

enthalpy_max = None
loading_max = None
pressure_max = None


fig_title = "Regular isotherms colour"
adsutils.plot_iso(isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular isotherms colour"
adsutils.plot_iso(isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular isotherms colour"
adsutils.plot_iso(isotherms, plot_type='enthalpy', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular isotherms colour"
adsutils.plot_iso(isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular isotherms colour"
adsutils.plot_iso(isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)


#################################################################################
# PyIAST isotherm modelling
#################################################################################
#
# %%
isotherm = isotherms[8]
modelH = isotherm.get_model_isotherm("Henry")
modelH.name = "Henry"
modelL = isotherm.get_model_isotherm("Langmuir")
modelL.name = "Langmuir"
modelDL = isotherm.get_model_isotherm("DSLangmuir")
modelDL.name = "DS Langmuir"

adsutils.plot_iso({isotherm, modelH, modelL, modelDL},
                  plot_type='isotherm', branch='ads', logarithmic=False, color=True)


#################################################################################
# Henrys constant calculations
#################################################################################
#
