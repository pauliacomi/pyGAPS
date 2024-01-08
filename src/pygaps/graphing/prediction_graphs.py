import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from pygaps.core.pointisotherm import PointIsotherm
from pygaps.graphing.mpl_styles import BASE_STYLE
import pygaps.graphing as pgg

def same_orders_of_maximum(vals):
    orders = [np.log10(max(v)) for v in vals]
    if abs(orders[0]-orders[1])>1:
        return True
    return False


@mpl.rc_context(BASE_STYLE)
def plot_enthalpy_prediction(
    original_isotherm: PointIsotherm,
    predicted_isotherm: PointIsotherm,
    loading: list[float],
    enthalpy: list[float],
    branch: str,
):
    fig = plt.figure(figsize=(8, 4), layout='tight')
    enthalpy_ax = fig.add_subplot(121)
    isos_ax = fig.add_subplot(122)

    pgg.calc_graphs.isosteric_enthalpy_plot(
        loading, enthalpy,
        std_err=[0 for n in loading],
        units=predicted_isotherm.units,
        ax=enthalpy_ax,
    )

    pgg.plot_iso(
        [original_isotherm, predicted_isotherm],
        branch=branch,
        ax=isos_ax,
        logx=same_orders_of_maximum(
        [original_isotherm.pressure(), predicted_isotherm.pressure()]
        ),
    )
    isos_ax.legend(
        [
            f'Original at {original_isotherm.temperature} K',
            f'Predicted at {predicted_isotherm.temperature} K',
        ],
        frameon=False
    )

    plt.show()

    return enthalpy_ax, isos_ax


@mpl.rc_context(BASE_STYLE)
def plot_adsorption_heatmap(
    grid: pd.DataFrame,
    original_temperature: float,
    units: dict = {
        'pressure': 'kPa',
        'temperature': 'K',
        'loading': 'mmol',
        'material': 'kg',
    },
    ax=None,
    **kwargs,
):
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

    cmap = kwargs.get('cmap', 'YlGn')
    im = ax.imshow(
        grid,
        cmap=cmap,
        extent=[
            min(grid.columns), max(grid.columns),
            min(grid.index), max(grid.index),
        ],
    )
    if not original_temperature is None:
        ax.axhline(y=original_temperature, color='r', linestyle='-')

    ax.set_xlabel(f"P [{units['pressure']}]")
    ax.set_ylabel(f"T [{units['temperature']}]")

    cm = plt.colorbar(im)
    cm.set_label(f"n [{units['loading']}/{units['material']}]")
