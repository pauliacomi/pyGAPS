# %%
import os

import adsutils
import adsutils.calculations

#################################################################################
#       Excel import | dataimport/excelinterface.py
#################################################################################
#
# %% Get test folder
xl_folder = os.getcwd() + r'\tests\data\isotherms'
print(xl_folder)
# %% Find files
xl_paths = adsutils.xl_experiment_parser_paths(
    xl_folder)
print(xl_paths)
# %% Import them
isotherms = []

for path in xl_paths:
    isotherms.append(adsutils.xl_experiment_parser(path))

# %%
for isotherm in isotherms:
    with open(isotherm.sample_name + ' ' + isotherm.sample_batch + '.json', "w") as text_file:
        text_file.write(adsutils.isotherm_to_json(isotherm))


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

# %%


HERE = os.getcwd() + r'\tests'


def test_BET(file):

    filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

    with open(filepath, 'r') as text_file:
        isotherm = adsutils.isotherm_from_json(text_file.read())

    isotherm.convert_pressure_mode("relative")
    bet_area = adsutils.calculations.area_BET(isotherm, verbose=True)

    return


test_BET('MCM-41 N2 77.json')
test_BET('NaY N2 77.json')
test_BET('SiO2 N2 77.json'),
test_BET('Takeda 5A N2 77.json')
test_BET('UiO-66(Zr) N2 77.json')


# %%
import pandas
import os
import adsutils
import adsutils.calculations

pressure_key = "pressure"
loading_key = "loading"

other_key = "enthalpy_key"
other_keys = {other_key: "enthalpy"}

isotherm_df = pandas.DataFrame({
    pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
    loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
    other_keys[other_key]: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
})
