# %%

import pygaps
import pandas

isotherm_param = {
    'sample_name': 'Carbon',
    'sample_batch': 'X1',
    'adsorbate': 'N2',
    't_exp': 77,
}

isotherm_data = pandas.DataFrame({
    'pressure': [0.1, 0.2, 0.3, 0.4, 0.5, 0.45, 0.35, 0.25, 0.15, 0.05],
    'loading': [0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0.15, 0.05]
})

isotherm = pygaps.PointIsotherm(
    isotherm_data,
    loading_key='loading',
    pressure_key='pressure',
    **isotherm_param
)

result_dict = pygaps.area_BET(isotherm, verbose=True)

plt.show()
# %%

import matplotlib.pyplot as plt

result_dict = pygaps.t_plot(isotherm, verbose=True)

plt.show()

with open(r'files/isotherm.json') as f:
    isotherm = pygaps.PointIsotherm.from_json(
        f.read()
    )
