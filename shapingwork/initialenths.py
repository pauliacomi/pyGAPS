#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%%
batches =[]
henrys = []
gasnames = []
gasvalues = []

for index, isotherm in enumerate(final_isotherms):
    henry = adsutils.calc_initial_henry_virial(isotherm, verbose=True)
    gas = adsutils.db_get_gas(db_path, name=isotherm.gas)
    print(index, gas.name, henry, isotherm.name, isotherm.batch)

    henrys.append(henry)
    gasnames.append(gas.name)
    gasvalues.append(gas.polarizability)
    batches.append(isotherm.batch)


#%%
dfrm = pd.DataFrame({"Gas" : gasnames, "Henry C" : henrys, "values" : gasvalues, "Batch" : batches})
dfrm["Batch"].value_counts()

#%%

order = ['N2', 'CO', 'CO2', 'CH4', 'C2H6', 'C3H6', 'C3H8', 'C4H10']
fig = dfrm.pivot('Gas','Batch','Henry C').loc[order].plot(kind='bar', logy=True, colormap='viridis', title="Initial Henry's constant comparison")


plt.savefig(filename="henry distribution", dpi=800, transparent=True)