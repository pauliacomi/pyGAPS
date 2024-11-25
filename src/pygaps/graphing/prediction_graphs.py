"""functions for plotting graphs of isotherm prediction"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pygaps.graphing as pgg
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.graphing.mpl_styles import BASE_STYLE
from pygaps.utilities.math_utilities import same_orders_of_maximum


@mpl.rc_context(BASE_STYLE)
def plot_predict_isotherm_from_enthalpy(
    original_isotherm: PointIsotherm,
    predicted_isotherm: PointIsotherm,
    loading: list[float],
    enthalpy: list[float],
    branch: str = 'ads',
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
        loading,
        enthalpy,
        std_err=enthalpy_stderr,
        units=predicted_isotherm.units,
        ax=enthalpy_ax,
    )

    logx = same_orders_of_maximum(
        [original_isotherm.pressure(), predicted_isotherm.pressure()]
    )

    pgg.plot_iso(
        [original_isotherm, predicted_isotherm],
        branch=branch,
        ax=isos_ax,
        logx=logx,
    )
    lgd_keys = [
        f'Original at {original_isotherm.temperature} K',
        f'Predicted at {predicted_isotherm.temperature} K'
    ]
    isos_ax.legend(lgd_keys, frameon=False)

    plt.show()

    return enthalpy_ax, isos_ax


@mpl.rc_context(BASE_STYLE)
def plot_predict_isosurface_from_enthalpy(
    grid: pd.DataFrame,
    original_temperature: float = None,
    cmap: str = 'YlGn',
    units: dict = None,
    ax=None,
    **kwargs,
):
    """
    Makes a 2D-heatmap with colorbar of loading as a function of pressure and
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

    if units is None:
        units = {
            'pressure': 'kPa',
            'temperature': 'K',
            'loading': 'mol',
            'material': 'kg',
        }

    pressures = grid.columns
    temperatures = grid.index
    unit_pressure = iter(['kPa', 'MPa', 'GPa', 'TPa'])
    while np.log10(max(pressures)) > 4:
        pressures = [p / 1000 for p in pressures]
        units['pressure'] = next(unit_pressure)
    grid.columns = pressures

    aspect = ((max(pressures) - min(pressures)) / (max(temperatures) - min(temperatures)))
    im = ax.imshow(
        grid,
        aspect=aspect,
        cmap=cmap,
        extent=[
            min(pressures),
            max(pressures),
            min(temperatures),
            max(temperatures),
        ],
    )
    if original_temperature is not None:
        ax.axhline(y=original_temperature, color='r', linestyle='-')

    ax.set_xlabel(f"P [{units['pressure']}]")
    ax.set_ylabel(f"T [{units['temperature']}]")

    cm = plt.colorbar(im)
    cm.set_label(f"n [{units['loading']}/{units['material']}]")


@mpl.rc_context(BASE_STYLE)
def plot_predict_isotherm_from_enthalpy_fit(
    original_isotherm: PointIsotherm,
    model_isotherm: ModelIsotherm,
    predicted_isotherm: PointIsotherm,
    loading: list[float],
    enthalpy: list[float],
    branch: str = 'ads',
    enthalpy_stderr: list[float] = None,
    axs: list[mpl.axes.Axes] = None,
):
    if axs is None:
        fig = plt.figure(figsize=(12, 4), layout='tight')
        isofit_ax = fig.add_subplot(131)
        enthalpy_ax = fig.add_subplot(132)
        isos_ax = fig.add_subplot(133)
    else:
        isofit_ax = axs[0]
        enthalpy_ax = axs[1]
        isos_ax = axs[2]

    if loading is None:
        loading = original_isotherm.loading(branch=branch)

    if enthalpy_stderr is None:
        enthalpy_stderr = [0 for n in loading]

    pgg.model_graphs.plot_model_guesses(
        attempts=[model_isotherm],
        pressure=original_isotherm.pressure(
            branch=branch, pressure_unit='Pa', pressure_mode='absolute'
        ),
        loading=original_isotherm.loading(
            branch=branch,
            loading_unit='mol',
            loading_basis='molar',
            material_unit='kg',
            material_basis='mass',
        ),
        ax=isofit_ax
    )

    plot_predict_isotherm_from_enthalpy(
        original_isotherm,
        predicted_isotherm,
        loading,
        enthalpy,
        branch=branch,
        enthalpy_stderr=enthalpy_stderr,
        axs=[enthalpy_ax, isos_ax]
    )
