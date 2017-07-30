# %%
from os.path import expanduser
import adsutils
from .samplecomparisons import plot_all_selected, plot_individual_selected

# %%
# Reload all imports from adsutils
#


def reload_imports():
    "reload everything"

    import importlib
    importlib.reload(adsutils)
    importlib.reload(adsutils.classes.sample)
    importlib.reload(adsutils.classes.gas)
    importlib.reload(adsutils.classes.user)
    importlib.reload(adsutils.classes.pointisotherm)
    importlib.reload(adsutils.calculations.initial_henry)
    importlib.reload(adsutils.calculations.initial_enthalpy)
    importlib.reload(adsutils.calculations.bet)
    importlib.reload(adsutils.dataimport.csvinterface)
    importlib.reload(adsutils.dataimport.excelinterface)
    importlib.reload(adsutils.dataimport.sqliteinterface)
    importlib.reload(adsutils.graphing.isothermgraphs)

    return


reload_imports()

#################################################################################
#       Database import
#
# %%
db_path = expanduser(
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
# %%
sel_samples = []
sel_isotherms = []

# %%
for sample in sel_samples:
    adsutils.db_upload_sample(db_path, sample, overwrite=True)

#################################################################################
#################################################################################

# %%
# SEVERAL BATCHES
s2_isotherms = []
req_batch = ["KRICT AlO Pellets", "KRICT01"]
for batch in req_batch:
    s2_isotherms += list(filter(lambda x: x.batch == batch, isotherms))
isotherms = s2_isotherms
print("Selected:", len(isotherms))


# %%
sample = [sample for sample in adsutils.SAMPLE_LIST
          if "MIL-100(Fe)" == sample.name and "KRICT01" == sample.batch]

print(sample[0].name)
print(sample[0].batch)
print(sample[0].properties)
# %%
sample[0].properties["density"] = 0.412
print(sample[0].properties)
sel_samples.append(sample[0])

# %%
for sample in sel_samples:
    print(sample.name, sample.batch, sample.properties)

#################################################################################
#################################################################################
# Common plots for the selected isotherms
#   isotherm
#   enthalpy
#   iso-enthalpy
#
# %%

legend_list = ['batch', 'user', 't_act']
enthalpy_max = None
loading_max = None
pressure_max = None

fig_title = "Regular isotherms colour"
adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Log isotherms colour"
adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Log isotherms B/W"
adsutils.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads', 'des'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=False, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular enthalpy colour"
adsutils.plot_iso(sel_isotherms, plot_type='enthalpy', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular isotherms colour"
adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)

fig_title = "Regular isotherms colour"
adsutils.plot_iso(sel_isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)


#################################################################################
#################################################################################
# PyIAST isotherm modelling
#
# %%
orig = isotherms[2]
model = orig.get_model_isotherm("Henry")

adsutils.plot_iso({orig, model}, plot_type='isotherm',
                  branch='ads', logarithmic=False, color=True)

# %%
#################################################################################
#################################################################################
#       Selections
# %%
sel_isotherms = isotherms
print("Selected:", len(sel_isotherms))
# %%
req_gas = ['C3H4']
sel_isotherms = []
for gas in req_gas:
    sel_isotherms = list(filter(lambda x: x.gas == gas, isotherms))
print("Selected:", len(sel_isotherms))
# %%
req_batch = []
sel_isotherms = []
for batch in req_batch:
    sel_isotherms += list(filter(lambda x: x.batch in batch, isotherms))

print("Selected:", len(sel_isotherms))

# %%
req_user = ["CH52"]
sel_isotherms = list(filter(lambda x: x.user in req_user, isotherms))
print("Selected:", len(sel_isotherms))


# %%
req_gas = ["N2", "CO2", "CO", "CH4", "C2H6", "C3H6", "C3H8", "C4H10"]
for gas in req_gas:
    s2_isotherms = list(filter(lambda x: x.gas in gas, sel_isotherms))
    plot_all_selected(s2_isotherms)

# %%
s2_isotherms = []
req_batch = ["KRICT AlO Pellets", "KRICT01", "KRICT noF PVA Pellets"]
for batch in req_batch:
    s2_isotherms += list(filter(lambda x: x.batch in batch, isotherms))
sel_isotherms = s2_isotherms
print("Selected:", len(sel_isotherms))

# %%
req_iso = [0, 1, 3, 4]
sel_isotherms = [sel_isotherms[i] for i in req_iso]
print("Selected:", len(sel_isotherms))

# %%
save_folder = expanduser(r"~")
plot_individual_selected(sel_isotherms)

# %%
save_folder = expanduser(r"~")
sel_isotherms.sort(key=lambda isotherm: isotherm.user, reverse=True)
plot_all_selected(sel_isotherms, False, None, None,
                  None, save_folder=save_folder)

#################################################################################
#################################################################################

# %%
for isotherm in isotherms:
    isotherm.convert_pressure_mode("relative")
    print(isotherm.name)
    adsutils.area_BET(isotherm, verbose=True)
    isotherm.convert_pressure_mode("absolute")
