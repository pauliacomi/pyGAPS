# %%
import os
import adsutils

xl_path = os.path.join(os.getcwd(), 'tests', 'data', 'isotherms')
json_path = os.path.join(os.getcwd(), 'tests', 'data', 'isotherms_json')

db_path = os.path.expanduser(
    r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")

#################################################################################
#       Excel import | dataimport/excelinterface.py
#################################################################################
#
# %% See test folder
print(xl_path)

# Find files
xl_file_paths = adsutils.util_get_file_paths(xl_path, '.xlsx')
print(xl_file_paths)

# Import them
isotherms = [adsutils.isotherm_from_xl(path) for path in xl_file_paths]


#################################################################################
#       Database import | dataimport/sqlinterface.py
#################################################################################
#
# %%
# Experiments
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
# Samples
adsutils.data.SAMPLE_LIST = adsutils.db_get_samples(db_path)

# %%
# Gasses
adsutils.data.GAS_LIST = adsutils.db_get_gasses(db_path)

#################################################################################
#       Json import | dataimport/jsoninterface.py
#################################################################################

# %% See test folder
print(json_path)

# Find files
json_file_paths = adsutils.util_get_file_paths(json_path, '.json')
print(json_file_paths)

# Import them
isotherms = []
for filepath in json_file_paths:
    with open(filepath, 'r') as text_file:
        isotherms.append(adsutils.isotherm_from_json(text_file.read()))


#################################################################################
#       Example Selections and filtering
#################################################################################
# %%
# Select all
sel_isotherms = isotherms
print("Selected:", len(sel_isotherms))

# %%
# Select by gas
req_gas = ['C3H4']
sel_isotherms = []
for gas in req_gas:
    sel_isotherms = list(filter(lambda x: x.gas == gas, isotherms))
print("Selected:", len(sel_isotherms))

# %%
# Select multiple gasses
req_gas = ["N2", "CO2", "CO", "CH4", "C2H6", "C3H6", "C3H8", "C4H10"]
for gas in req_gas:
    s2_isotherms = list(filter(lambda x: x.gas in gas, sel_isotherms))

print("Selected:", len(sel_isotherms))

# %%
# Select by batch
req_batch = []
sel_isotherms = []
for batch in req_batch:
    sel_isotherms += list(filter(lambda x: x.batch in batch, isotherms))

print("Selected:", len(sel_isotherms))

# %%
# Select multiple batches
s2_isotherms = []
req_batch = ["KRICT AlO Pellets", "KRICT01", "KRICT noF PVA Pellets"]
for batch in req_batch:
    s2_isotherms += list(filter(lambda x: x.batch in batch, isotherms))
sel_isotherms = s2_isotherms
print("Selected:", len(sel_isotherms))


# %%
# Select by user
req_user = ["TU"]
sel_isotherms = list(filter(lambda x: x.user in req_user, isotherms))
print("Selected:", len(sel_isotherms))
