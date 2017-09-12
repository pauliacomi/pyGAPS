# %%
import os
import pandas
import scipy
import numpy
import pygaps
import importlib
import matplotlib.pyplot as plt

json_path = os.path.join(os.getcwd(), 'tests',
                         'calculations', 'data', 'isotherms_json')
json_file_paths = pygaps.util_get_file_paths(json_path, '.json')
isotherms = []
for filepath in json_file_paths:
    print(filepath)
    with open(filepath, 'r') as text_file:
        isotherms.append(pygaps.isotherm_from_json(
            text_file.read()))

# %%
isotherm = isotherms[0]

p_int = numpy.arange(0.3, 24, 0.4)
l_int = isotherm.loading_at(p_int, interpolation_type='linear')
pressure = isotherm.pressure()
loading = isotherm.loading()
fig, ax = plt.subplots(1, 1, figsize=(12, 12))
ax.plot(pressure, loading)
ax.plot(p_int, l_int,
        marker='x', linestyle='', color='r', label='chosen points')

plt.show()
