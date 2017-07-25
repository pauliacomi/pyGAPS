#%%
from os.path import expanduser
import adsutils
from shapingwork.comparisonfunctions import plot_all_selected

# All samples from database
db_path = expanduser(r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")
save_folder = expanduser(r"~\OneDrive\Documents\PhD Documents\Collated Results\Shaping\MIL-127(Fe) Shaping\img")
save_data = False
volumetric = False

# Get samples into memory
samples = adsutils.db_get_samples(db_path)
adsutils.SAMPLE_LIST = samples

# Get isotherms into memory
isotherms = []
criteria = {
    'sname':        "MIL-100(Fe)",
    't_exp':        303,
    't_act':        150,
    'comment':      ""
    }
isotherms = adsutils.db_get_experiments(db_path, criteria)

# Filter samples on batches

sel_isotherms = []
req_batch = ["KRICT AlO Pellets", "KRICT01", "KRICT noF PVA Pellets"]
for batch in req_batch:
    sel_isotherms += list(filter(lambda x: x.batch == batch, isotherms))

isotherms = sel_isotherms
print("Selected", len(isotherms), "isotherms")



# Filter samples on calorimetry

sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.enthalpy_key in x.data.columns, isotherms))
isotherms = sel_isotherms
print("Selected", len(isotherms), "isotherms")

if volumetric == True:
    for isotherm in isotherms:
        isotherm.convert_adsorbent_mode("volume")

# Rename any isotherms for better visibility
for index, isotherm in enumerate(isotherms):
    if isotherm.batch == "KRICT01":
        isotherm.batch = "KRICT Powder"
    if isotherm.batch == "KRICT noF PVA Pellets":
        isotherm.batch = "KRICT PVA Pellets"

final_isotherms = []

# Filter samples on gas then plot
req_gas = 'N2'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, 50, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'CO'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)


plot_all_selected(sel_isotherms, save_data, None, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'CO2'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, None, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'CH4'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, 40, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'C2H6'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, 70, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'C3H6'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, 70, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'C3H8'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, 70, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms

###################

req_gas = 'C4H10'
sel_isotherms = []
sel_isotherms = list(filter(lambda x: x.gas == req_gas, isotherms))
print("Selected", len(sel_isotherms), "isotherms for gas", req_gas)

sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)

plot_all_selected(sel_isotherms, save_data, None, None, None, save_folder=save_folder)

final_isotherms += sel_isotherms
