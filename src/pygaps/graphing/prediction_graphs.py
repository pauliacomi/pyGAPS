"""functions for plotting graphs of isotherm prediction"""

import pandas as pd
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

from pygaps.core.pointisotherm import PointIsotherm
from pygaps.graphing.mpl_styles import BASE_STYLE
import pygaps.graphing as pgg

def same_orders_of_maximum(vals: list[list[float]]):
    """
    Determines if the maximum of two lists are within one order of magnitude.

    Parameters
    ----------
    vals: list of list of floats
        The lists to compare

    Returns
    ------
    True:
        If within one order of magnitude
    False:
        If not
    """
    orders = [np.log10(max(v)) for v in vals]
    if abs(orders[0]-orders[1])>1:
        return True
    return False


@mpl.rc_context(BASE_STYLE)
def plot_enthalpy_prediction(
    original_isotherm: PointIsotherm,
    predicted_isotherm: PointIsotherm,
    branch: str,
    loading: list[float],
    enthalpy: list[float],
    enthalpy_stderr: list[float] = None,
    axs: list[mpl.axes.Axes] = None,
):
    if axs is None:
        fig = plt.figure(figsize=(8, 4), layout='tight')
        enthalpy_ax = fig.add_subplot(121)
        isos_ax = fig.add_subplot(122)
    else:
        enthalpy_ax = axs[0]
        isos_ax = axs[1]

    if enthalpy_stderr is None:
        enthalpy_stderr = [0 for n in loading]

    pgg.calc_graphs.isosteric_enthalpy_plot(
        loading, enthalpy,
        std_err=enthalpy_stderr,
        units=predicted_isotherm.units,
        ax=enthalpy_ax,
    )

    pgg.plot_iso(
        [original_isotherm, predicted_isotherm],
        branch=branch,
        ax=isos_ax,
        logx=same_orders_of_maximum( # uses log axis if needed
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
    original_temperature: float = None,
    cmap: str = 'YlGn',
    units: dict = {
        'pressure': 'kPa',
        'temperature': 'K',
        'loading': 'mmol',
        'material': 'kg',
    },
    ax=None,
    **kwargs,
):
    """
    Makes 2D-heatmap with colorbar of loading as a function of pressure and
    temperature.

    Parameters
    ---------
    grid: pd.DataFrame
        The data to use, loading are values. Index is temperature, columns are
        pressure. Values should be evenly spaced.
    original_temperature: float, optional
        Original temperature of isotherm measurement. If present will plot a
        horizontal line to indicate the original isotherm.
        Defaults to None.
    cmap: str, optional
        The cmap to use for the loading values in the heatmap.
        Defaults to 'YlGn'
    units: dict, optional
        The units to display on the axes and colorbar
    ax: optional
        The axis to use, if any

    """
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

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
