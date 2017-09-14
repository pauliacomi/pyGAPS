# %%
from os.path import expanduser

import pandas

import pygaps

# %%
# Reload all imports from pygaps
#


def reload_imports():
    "reload everything"

    import importlib
    importlib.reload(pygaps)
    importlib.reload(pygaps.classes.sample)
    importlib.reload(pygaps.classes.gas)
    importlib.reload(pygaps.classes.isotherm)
    importlib.reload(pygaps.classes.pointisotherm)
    importlib.reload(pygaps.classes.modelisotherm)
    importlib.reload(pygaps.classes.interpolatorisotherm)
    importlib.reload(pygaps.calculations.initial_henry)
    importlib.reload(pygaps.calculations.bet)
    importlib.reload(pygaps.parsing.csvinterface)
    importlib.reload(pygaps.parsing.excelinterface)
    importlib.reload(pygaps.parsing.sqliteinterface)
    importlib.reload(pygaps.graphing.isothermgraphs)

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
isotherms = pygaps.db_get_experiments(db_path, criteria)

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
        result = pygaps.area_BET(isotherm)
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
pygaps.area_BET(isotherms[1], verbose=True)
isotherm.convert_pressure_mode("absolute")


#################################################################################
# Save json
#################################################################################

# %%
# Save as json
for isotherm in isotherms:
    with open(isotherm.sample_name + ' ' + isotherm.sample_batch + '.json', "w") as text_file:
        text_file.write(pygaps.isotherm_to_json(isotherm))

# %%
for isotherm in isotherms:
    if isotherm.other_keys:
        pygaps.plot_iso([isotherm], plot_type='enthalpy', branch=['ads'])
