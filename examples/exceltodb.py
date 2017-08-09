# %%
from os.path import expanduser
import adsutils
import pandas


#################################################################################
#################################################################################
#       Database sanitisation
#
# %% Get all samples and generate a list of isotherms
samples = adsutils.db_get_samples(db_path)
names = []
for index, sample in enumerate(samples):
    names.append(sample.name)

data = pandas.DataFrame(dict(name=names))
data = data.drop_duplicates()
print(data)

# %% Build all isotherms
isotherms = []
for sample in data["name"]:
    criteria = dict(
        sname=sample
    )
    print(sample)
    isotherms += adsutils.db_get_experiments(db_path, criteria)


# %% Sanitising database of 0 initial points for loading
for index, isotherm in enumerate(isotherms):
    data = isotherm.data
    if data[isotherm.loading_key][0] == 0:
        isotherm.data.drop(isotherm.data.index[0], inplace=True)
        isotherm.data.reset_index(drop=True, inplace=True)
        adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)

print("finished")

# %% Sanitising database of negative initial points for loading
for index, isotherm in enumerate(isotherms):
    data = isotherm.data
    if data[isotherm.loading_key][0] < 0:
        print(index)
        data.loc[:, isotherm.loading_key] = data[isotherm.loading_key] - \
            data[isotherm.loading_key][0]
        isotherm.data.drop(isotherm.data.index[0], inplace=True)
        isotherm.data.reset_index(drop=True, inplace=True)
        adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)

# %% Sanitising database of negative initial points for pressure
for index, isotherm in enumerate(isotherms):
    data = isotherm.data
    if data[isotherm.pressure_key][0] < 0:
        print(index)
        data.loc[:, isotherm.pressure_key] = data[isotherm.pressure_key] - \
            data[isotherm.pressure_key][0] + 0.001
        adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)


#################################################################################
#################################################################################
#       !WARNING! Database creation and reinitialisation
#
# %%
smp_path = r'C:\Users\pauli\OneDrive\Documents\PhD Documents\Data processing\Database\Sample Overview.csv'
samples = adsutils.samples_parser(smp_path)
for sample in samples:
    adsutils.db_upload_sample(db_path, sample)
# %%
db_path = r'C:\Users\pauli\OneDrive\Documents\PhD Documents\Data processing\Database\local.db'
for isotherm in isotherms:
    adsutils.db_upload_experiment(db_path, isotherm)
