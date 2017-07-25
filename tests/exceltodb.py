#%%
from os.path import expanduser
import adsutils
import pandas

#################################################################################
#################################################################################
#       Excel import
#
#%%
xl_folder = r'C:\Users\PC-Etu1-Phil\Desktop\Paul\UiO-66(Zr) - KRICT AlO Pellets'
xl_paths = adsutils.xl_experiment_parser_paths(xl_folder)

isotherms = []

for path in xl_paths:
    data, info = adsutils.xl_experiment_parser(path)
    isotherm = adsutils.PointIsotherm(data, info,
                                      pressure_key="Pressure (bar)",
                                      loading_key="Loading (mmol/g)",
                                      enthalpy_key="Enthalpy (kJ/mol)")
    isotherms.append(isotherm)


#%%
db_path = expanduser(r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")

#%%
isotherms[0].id = ""
for isotherm in isotherms:
    adsutils.db_upload_experiment(db_path, isotherm, overwrite=False)


#################################################################################
#################################################################################
#       Database sanitisation
#
#%% Get all samples and generate a list of isotherms
samples = adsutils.db_get_samples(db_path)
names =[]
for index, sample in enumerate(samples):
    names.append(sample.name)

data = pandas.DataFrame(dict(name=names))
data = data.drop_duplicates()
print(data)

#%% Build all isotherms
isotherms = []
for sample in data["name"]:
    criteria = dict(
        sname=sample
    )
    print(sample)
    isotherms += adsutils.db_get_experiments(db_path, criteria)


#%% Sanitising database of 0 initial points for loading
for index, isotherm in enumerate(isotherms):
    data = isotherm.data
    if data[isotherm.loading_key][0] == 0:
        isotherm.data.drop(isotherm.data.index[0], inplace=True)
        isotherm.data.reset_index(drop=True, inplace=True)
        adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)

print("finished")

#%% Sanitising database of negative initial points for loading
for index, isotherm in enumerate(isotherms):
    data = isotherm.data
    if data[isotherm.loading_key][0] < 0:
        print(index)
        data.loc[:, isotherm.loading_key] = data[isotherm.loading_key] - data[isotherm.loading_key][0]
        isotherm.data.drop(isotherm.data.index[0], inplace=True)
        isotherm.data.reset_index(drop=True, inplace=True)
        adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)

#%% Sanitising database of negative initial points for pressure
for index, isotherm in enumerate(isotherms):
    data = isotherm.data
    if data[isotherm.pressure_key][0] < 0:
        print(index)
        data.loc[:, isotherm.pressure_key] = data[isotherm.pressure_key] - data[isotherm.pressure_key][0] + 0.001
        adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)
#%%
isotherms[319].print_info(logarithmic=True)
isotherms[319].data

#################################################################################
#################################################################################
#       !WARNING! Database creation and reinitialisation
#
#%%
adsutils.db_create_table_samples(db_path)
#%%
adsutils.db_create_table_experiment_data(db_path)
#%%
adsutils.db_create_table_experiments(db_path)
#%%
smp_path = r'C:\Users\pauli\OneDrive\Documents\PhD Documents\Data processing\Database\Sample Overview.csv'
samples = adsutils.samples_parser(smp_path)
for sample in samples:
    adsutils.db_upload_sample(db_path, sample)
#%%
db_path = r'C:\Users\pauli\OneDrive\Documents\PhD Documents\Data processing\Database\local.db'
for isotherm in isotherms:
    adsutils.db_upload_experiment(db_path, isotherm)
