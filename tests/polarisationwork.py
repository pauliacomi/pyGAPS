#%%
from os.path import expanduser
import adsutils
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import pandas as pd
import numpy

#################################################################################
#       Database import
#
#%%
db_path = expanduser(r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")

isotherms = []
criteria = dict(
    sname="MIL-53(Al)",
    #sbatch="VG862",
    #user="ADW",
    #t_exp=303,
    #t_act="",
    #machine="RG",
    #gas="C4H10",
    #exp_type="",
    comment=""
    )
isotherms = adsutils.db_get_experiments(db_path, criteria)

#%%
# Get all samples and generate a list of isotherms
samples = adsutils.db_get_samples(db_path)
names =[]
for index, sample in enumerate(samples):
    names.append(sample.name)

data = pd.DataFrame(dict(name=names))
data.drop_duplicates(inplace=True)
data.reset_index(inplace=True)
print(data)


#%%
# Build all isotherms
isotherms = []
for sample in data["name"]:
    criteria = dict(
        sname=sample,
        #sbatch="",
        #user="",
        #t_exp=303,
        #t_act="",
        #machine="",
        #gas="C3H8",
        #exp_type="",
        comment=""
    )
    print(sample)
    isotherms += adsutils.db_get_experiments(db_path, criteria)

#%%
print(len(isotherms))

machines = []
for isotherm in isotherms:
    machines.append(isotherm.t_exp)

names_df = pd.DataFrame({"one":machines})
names_df["one"].value_counts()

#%%
gas = adsutils.db_get_gas(db_path, name="He")
gas.print_info()

#%%
orig = isotherms[4]
#orig.print_info()
adsutils.calc_initial_henry(orig, max_adjrms=0.01, verbose=True)

#%%

henrys = []
gasnames = []
gasvalues = []
t_acts =[]

for index, isotherm in enumerate(isotherms):
    henry = adsutils.calc_initial_henry_virial(isotherm, verbose=True)
    gas = adsutils.db_get_gas(db_path, name=isotherm.gas)
    print(index, gas.name, henry, isotherm.name, isotherm.batch)

    henrys.append(henry)
    gasnames.append(gas.name)
    gasvalues.append(gas.polarizability)
    t_acts.append(isotherm.t_act)



#%%
req_numbers = [12, 28, 31, 93, 146, 280, 308, 312, 315, 317, 365, 373, 377, 379, 408]
req_numbers = [14, 12]
for number in req_numbers:
    isotherms.remove(isotherms[number])
    #isotherm = isotherms[number]
    #print(number, isotherm.name, isotherm.batch, isotherm.user, isotherm.machine, isotherm.t_act)
    #isotherm.data.drop(isotherm.data.index[0], inplace=True)
    #isotherm.data.reset_index(drop=True, inplace=True)
    #adsutils.db_upload_experiment(db_path, isotherm, overwrite=True)
    #adsutils.calc_initial_henry_virial(isotherms[number], verbose=True)
    #isotherms[number].print_info(logarithmic=True)
    #print(isotherms[number].data)


#%%
dfrm = pd.DataFrame({"gas" : gasnames, "henry" : henrys, "values" : gasvalues, "t_acts" : t_acts})
dfrm["t_acts"].value_counts()
#dfrm[dfrm["gas"] == "CO2"]


#%%
from adjustText import adjust_text

dfrm = pd.DataFrame({"gas" : gasnames, "henry" : henrys, "values" : gasvalues, "t_acts" : t_acts})

colors = {150:'blue', 250:'black', 200:'red'}

fig, axes = plt.subplots(1, 1, figsize=(8, 8))
axes.scatter(gasvalues, henrys, marker='o', c=dfrm['t_acts'].apply(lambda x: colors[x]))


texts = []

for label, x, y in zip(gasvalues, henrys, gasnames):
    texts.append(plt.text(label, x, y))
    # axes.annotate(label,
    #     xy=(x, y), xytext=(30, 0),
    #     textcoords='offset points', ha='right', va='bottom',
    #     bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.3),
    #     arrowprops=dict(arrowstyle = '->', connectionstyle='arc3,rad=0'))

axes.set_yscale('log')
axes.set_xlabel("Polarizability")
axes.set_ylabel("$log_{10}(k_h)$")
adjust_text(texts, arrowprops=dict(arrowstyle = '->', connectionstyle='arc3,rad=0'))


plt.show()

#%%
colors = {150:'blue', 250:'red'}

red_means = []
blue_means = []
red_std = []
blue_std = []
for gas in dfrm["gas"].value_counts().keys():
    dfrm_a = dfrm[dfrm["gas"] == gas]
    
    blue_means.append(numpy.average(dfrm_a[dfrm_a["t_acts"] == 150]["henry"]))
    blue_std.append(numpy.std(dfrm_a[dfrm_a["t_acts"] == 150]["henry"]))
    red_means.append(numpy.average(dfrm_a[dfrm_a["t_acts"] == 250]["henry"]))
    red_std.append(numpy.std(dfrm_a[dfrm_a["t_acts"] == 250]["henry"]))

fig, axes = plt.subplots(1, 1, figsize=(5.5, 4))

Xuniques, X = np.unique(dfrm['gas'], return_inverse=True)
ind = np.arange(len(dfrm["gas"].value_counts().keys()))  # the x locations for the groups
width = 0.35       # the width of the bars

rects1 = axes.bar(ind, red_means, width, color='r')
rects2 = axes.bar(ind + width, blue_means, width, color='b')

axes.set_yscale('log')
axes.set_xlabel("Gasses")
axes.set_ylabel("$log_{10}(k_h)$")
axes.legend((rects1[0], rects2[0]), ('250°C', '150°C'))

axes.set(xticks=range(len(dfrm["gas"].value_counts().keys())), xticklabels=dfrm["gas"].value_counts().keys())

plt.savefig(filename="henry distribution", dpi=800, transparent=True)
plt.show()
#%%
fig, axes = plt.subplots(1, 1, figsize=(5, 5))

Xuniques, X = np.unique(dfrm['gas'], return_inverse=True)

axes.scatter(X, dfrm['henry'], marker='o', c=dfrm['t_acts'].apply(lambda x: colors[x]))

axes.set(xticks=range(len(Xuniques)), xticklabels=Xuniques)

axes.annotate('Red: 250°C', xy=(0,0), xycoords='axes fraction', xytext=(0.77, 0.95))
axes.annotate('Blue: 150°C', xy=(0,0), xycoords='axes fraction', xytext=(0.77, 0.87))

axes.set_yscale('log')
axes.set_xlabel("Gasses")
axes.set_ylabel("$log_{10}(k_h)$")

#plt.savefig(filename="henry distribution", dpi=800)


#%%
fig, ax = plt.subplots()

hist_data = numpy.array(dfrm[dfrm["gas"] == "CO"]["henry"])
mu = numpy.average(hist_data)
sigma = numpy.std(hist_data)

num_bins = 50
n, bins, patches = ax.hist(hist_data, num_bins, normed=1)
y = mlab.normpdf(bins, mu, sigma)
ax.plot(bins, y, '--')
fig.tight_layout()
plt.show()

