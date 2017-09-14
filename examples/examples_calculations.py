# %%
import os

import pygaps

json_path = os.path.join(os.getcwd(), 'tests',
                         'calculations', 'data', 'isotherms_json')
json_file_paths = pygaps.util_get_file_paths(json_path, '.json')
isotherms = []
for filepath in json_file_paths:
    print(filepath)
    with open(filepath, 'r') as text_file:
        isotherms.append(pygaps.isotherm_from_json(
            text_file.read()))

#################################################################################
# Henrys constant calculations
#################################################################################
#
# %%
# Regular method

for isotherm in isotherms:
    pygaps.calc_initial_henry(isotherm, max_adjrms=0.01, verbose=True)

# %%
# Virial method
for isotherm in isotherms:
    pygaps.calc_initial_henry_virial(isotherm, verbose=True)

#################################################################################
# BET surface area calculations
#################################################################################
#
# %%
# Calculate BET
for isotherm in isotherms:
    print(isotherm.sample_name)
    print(isotherm.adsorbate)
    isotherm.convert_mode_pressure("relative")
    pygaps.area_BET(isotherm, verbose=True)
    isotherm.convert_mode_pressure("absolute")

# %%
for isotherm in isotherms:
    print(isotherm.sample_name)
    print(isotherm.gas)

#################################################################################
# t-plot calculations
#################################################################################
#

# %%
# Calculate t-plot
for isotherm in isotherms:
    print(isotherm.sample_name)
    print(isotherm.gas)
    isotherm.convert_mode_pressure("relative")
    pygaps.t_plot(isotherm, 'Halsey', verbose=True)
    isotherm.convert_mode_pressure("absolute")

# Pore size distribution
#################################################################################
# %%
# Mesoporous pore size distribution
for isotherm in isotherms:
    isotherm.convert_mode_pressure('relative')
    result_dict = pygaps.mesopore_size_distribution(
        isotherm,
        psd_model='BJH',
        branch='desorption',
        verbose=True)

# %%
# Microporous pore size distribution
for isotherm in isotherms:
    if isotherm.adsorbate != 'CO2':
        isotherm.convert_mode_pressure('relative')
        result_dict = pygaps.micropore_size_distribution(
            isotherm,
            psd_model='HK',
            pore_geometry='slit',
            verbose=True)

# %%
for x in result_dict['pore_widths']:
    print(x)
print('x')
for x in result_dict['pore_distribution']:
    print(x)

# %%

for isotherm in isotherms:
    print(isotherm.sample_name)
    print(isotherm.gas)
    isotherm.convert_mode_pressure("relative")
    pygaps.dft_size_distribution(isotherm, 'internal', verbose=True)


#################################################################################
#################################################################################
# PyIAST isotherm modelling
#
# %%
# Attempt to guess the best model
for isotherm in isotherms:
    model = pygaps.ModelIsotherm.from_pointisotherm(
        isotherm, model='guess', verbose=True)
    pygaps.plot_iso([isotherm, model])

# %%
# For a particular model
model = pygaps.ModelIsotherm.from_pointisotherm(
    isotherms[3], model='BET', verbose=True)
