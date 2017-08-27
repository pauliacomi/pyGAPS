# %%
import os
import pandas
import scipy
import numpy
import adsutils
import importlib
import matplotlib.pyplot as plt

# %%
gas_data = {
    'nick': 'N2',
    'formula': 'N2',

    'properties': {
        'common_name': 'nitrogen',
        'molar_mass': 28.01348,
        'cross_sectional_area': 0.162,
        'polarizability': 17.4,
        'dipole_moment': 0.0,
        'quadrupole_moment': 1.52,
        'criticalp_temperature': 77.355,
        'criticalp_pressure': 34.0,
        'criticalp_density': 11.2,
        'triplep_temperature': 63.1,
        # properties for 1atm/77k
        'liquid_density': 0.806,
        'surface_tension': 8.8796,
        'saturation_pressure': 101325,
    }
}

gas = adsutils.Gas(gas_data)
adsutils.data.GAS_LIST.append(gas)
filepath = os.path.join(
    'tests', 'data', 'isotherms_json', 'UiO-66(Zr) N2 77.355.json')

with open(filepath, 'r') as text_file:
    isotherm = adsutils.isotherm_from_json(
        text_file.read())
isotherm.convert_pressure_mode('relative')

loading = isotherm.loading_ads(unit='mmol')
pressure = isotherm.pressure_ads()
maximum_adsorbed = max(loading)

# %%
loading = numpy.array([0.019, 0.039, 0.079, 0.108, 0.222, 0.301, 0.550,
                       0.658, 0.814, 0.880, 0.907, 0.942, 0.963, 0.986, 0.992, 0.999])

pressure = numpy.array([3.03e-7, 5.00e-7, 1.07e-6, 1.45e-6, 2.76e-6, 4.61e-6, 1.33e-5,
                        5.66e-4, 2.11e-3, 1.32e-2, 6.18e-2, 1.08e-1, 2.17e-1, 5.13e-1,
                        7.04e-1, 8.42e-1])
maximum_adsorbed = 1

# %%
adsorbate_properties = dict(
    molecular_diameter=0.3,
    polarizability=1.76E-30,
    magnetic_susceptibility=3.6E-35,
    surface_density=6.7E18,            # molecules/m2
)

adsorbent_properties = dict(
    molecular_diameter=0.34,            # nm
    polarizability=1.02E-30,            # m3
    magnetic_susceptibility=1.35E-34,   # m3
    surface_density=3.845E19,           # molecules/m2
)

# dictionary unpacking
d_adsorbate = adsorbate_properties.get('molecular_diameter')
d_adsorbent = adsorbent_properties.get('molecular_diameter')
p_adsorbate = adsorbate_properties.get('polarizability')
p_adsorbent = adsorbent_properties.get('polarizability')
m_adsorbate = adsorbate_properties.get('magnetic_susceptibility')
m_adsorbent = adsorbent_properties.get('magnetic_susceptibility')
n_adsorbate = adsorbate_properties.get('surface_density')
n_adsorbent = adsorbent_properties.get('surface_density')

# calculation of constants and terms
e_m = scipy.constants.electron_mass
c = scipy.constants.speed_of_light
effective_diameter = d_adsorbate + d_adsorbent
sigma = (2 / 5)**(1 / 6) * effective_diameter / 2
sigma_si = sigma * 1e-9

a_adsorbent = 6 * e_m * c ** 2 * p_adsorbate * p_adsorbent /\
    (p_adsorbate / m_adsorbate + p_adsorbent / m_adsorbent)
a_adsorbate = 3 * e_m * c**2 * p_adsorbate * m_adsorbate / 2

constant_interaction_term = - \
    ((sigma**4) / (3 * (effective_diameter / 2)**3) -
        (sigma**10) / (9 * (effective_diameter / 2)**9))

constant_coefficient = scipy.constants.Avogadro / \
    (scipy.constants.gas_constant * isotherm.t_exp) * \
    (n_adsorbate * a_adsorbate + n_adsorbent * a_adsorbent) / \
    (sigma_si**4)


def h_k_pressure(l_pore):
    pressure = numpy.exp(constant_coefficient / (l_pore - effective_diameter) *
                         ((sigma**4) / (3 * (l_pore - effective_diameter / 2)**3) -
                          (sigma**10) / (9 * (l_pore - effective_diameter / 2)**9) +
                          constant_interaction_term))

    return pressure


p_w = []

for index, p_point in enumerate(pressure):
    # minimise to find pore length
    def h_k_minimization(l_pore):
        return numpy.abs(h_k_pressure(l_pore) - p_point)
    res = scipy.optimize.minimize_scalar(h_k_minimization)
    p_w.append(res.x - d_adsorbent)

# get loading for each point
pore_widths = numpy.array(p_w)
pore_adsorbed = loading / maximum_adsorbed

avg_pore_widths = numpy.add(pore_widths[:-1], pore_widths[1:]) / 2
d_pore_cum = numpy.diff(loading / maximum_adsorbed) / numpy.diff(pore_widths)

# %%
h_k_pressure(0.4143 + d_adsorbent)

# %%
p_point = 3.03e-7


def h_k_minimization(l_pore):
    return numpy.abs(h_k_pressure(l_pore) - p_point)


res = scipy.optimize.minimize_scalar(h_k_minimization)
print(res.x - d_adsorbent)
# %%

fig = plt.figure()
"""Draws the pore size distribution plot"""
ax1 = fig.add_subplot(111)
ax1.plot(pore_widths * 10, pore_adsorbed,
         marker='', color='b', label='cumulative')
ax1.plot(avg_pore_widths * 10, d_pore_cum,
         marker='', color='g', label='distribution')
ax1.set_title("PSD plot")
ax1.set_xlabel('Pore width (A)')
ax1.set_ylabel('Pore size')
ax1.legend(loc='best')
ax1.set_ylim(ymin=0)
ax1.set_xlim(xmin=0, xmax=20)
ax1.grid(True)
plt.show()

# %%
print(pore_widths)
