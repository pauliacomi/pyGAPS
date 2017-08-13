# %%
from os.path import expanduser

import pandas

import adsutils

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
    importlib.reload(adsutils.calculations.bet)
    importlib.reload(adsutils.parsing.csvinterface)
    importlib.reload(adsutils.parsing.excelinterface)
    importlib.reload(adsutils.parsing.sqliteinterface)
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
    # 'sample_name':        "MIL-100(Fe)",
    # 'sample_batch':       "KRICT01",
    # 'user':         "",
    # 't_exp':        303,
    # 't_act':        "",
    # 'machine':      "",
    # 'gas':          "C3H8",
    # 'exp_type':     "",
}
isotherms = adsutils.db_get_experiments(db_path, criteria)

# %%
adsutils.data.SAMPLE_LIST = adsutils.db_get_samples(db_path)
adsutils.data.GAS_LIST = adsutils.db_get_gasses(db_path)

#################################################################################
# BET calcs
#################################################################################

# %%
bet_areas = {}
errors = []
complete = []
for index, isotherm in enumerate(isotherms):
    try:
        isotherm.convert_pressure_mode("relative")
    except Exception as identifier:
        continue
    complete.append(index)
    try:
        result = adsutils.area_BET(isotherm)
        result.update({'sample': isotherm.sample_name + isotherm.sample_batch,
                       'gas': isotherm.gas})
        bet_areas.update({index: result})
    except:
        errors.append(index)
    isotherm.convert_pressure_mode("absolute")

# %%
isotherm = isotherms[34]
isotherm.print_info()
isotherm.data()

# %%

for index, isotherm in enumerate(isotherms):
    asd = isotherm.sample_name + isotherm.sample_batch
    print(asd)

# %%
print(len(errors))
print(len(complete))
print(len(bet_areas))
print(errors)

# %%

df = pandas.DataFrame.from_dict(bet_areas, orient='index')
df
# df.set_index('sample', inplace=True)

# %%
isotherm.convert_pressure_mode("relative")
adsutils.area_BET(isotherms[1], verbose=True)
isotherm.convert_pressure_mode("absolute")


#################################################################################
# Save json
#################################################################################

# %%
# Save as json
for isotherm in isotherms:
    with open(isotherm.sample_name + ' ' + isotherm.sample_batch + '.json', "w") as text_file:
        text_file.write(adsutils.isotherm_to_json(isotherm))
