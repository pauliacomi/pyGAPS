"""Functions for plotting graphs related to IAST calculations."""

import matplotlib.pyplot as plt

from ..utilities.string_utilities import convert_chemformula
from .mpl_styles import IAST_STYLES


def plot_iast_vle(
        x_data, y_data,
        adsorbate1, adsorbate2,
        pressure, p_unit,
        ax=None):
    """
    Plot a vapour-adsorbed equilibrium graph from IAST data.

    Parameters
    ----------
    x_data : array or list
        The molar fraction in the adsorbed phase.
    y_data : array or list
        The molar fraction in the gas phase.
    adsorbate1 : str
        Name of the adsorbate which is regarded as the main component.
    adsorbate2 : str
        Name of the adsorbate which is regarded as the secondary component.
    pressure : float
        Pressure at which the vle is plotted.
    p_unit : str
        Unit of the pressure, for axis labelling.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    ax : matplotlib ax
        The ax object.
    """
    # Generate the figure if needed
    if ax is None:
        fig = plt.figure(**IAST_STYLES['fig_style'])
        ax = fig.add_subplot(111)

    text_x = 'Gas fraction ' + convert_chemformula(adsorbate1)
    text_y = 'Adsorbed fraction ' + convert_chemformula(adsorbate1)
    title_graph = convert_chemformula(adsorbate1) + \
        ' in ' + convert_chemformula(adsorbate2)
    label = str(pressure) + ' (' + p_unit + ')'

    # graph title
    ax.set_title(title_graph, **IAST_STYLES['title_style'])

    # labels for the axes
    ax.set_xlabel(text_x, **IAST_STYLES['label_style'])
    ax.set_ylabel(text_y, **IAST_STYLES['label_style'])
    ax.tick_params(axis='both', which='major', **IAST_STYLES['tick_style'])

    # Regular data
    ax.plot(y_data, x_data, label=label)

    # Straight line
    line = [0, 1]
    ax.plot(line, line, color='black')

    ax.legend(loc='best', **IAST_STYLES['legend_style'])

    ax.grid(True, zorder=5)
    ax.set_xlim(left=0, right=1)
    ax.set_ylim(bottom=0, top=1)
    ax.set_xscale('linear')

    return ax


def plot_iast_svp(
        p_data, s_data,
        adsorbate1, adsorbate2,
        fraction, p_unit,
        ax=None):
    """
    Plot a selectivity-vs-pressure graph from IAST data.

    Parameters
    ----------
    p_data : array or list
        The pressures at which selectivity is calculated.
    s_data : array or list
        The selectivity towards the main component as a function of pressure.
    adsorbate1 : str
        Name of the adsorbate which is regarded as the main component.
    adsorbate2 : str
        Name of the adsorbate which is regarded as the secondary component.
    fraction : float
        Molar fraction of the main component in the mixture.
    p_unit : str
        Unit of the pressure, for axis labelling.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    ax : matplotlib ax
        The ax object.
    """

    # Generate the figure if needed
    if ax is None:
        fig = plt.figure(**IAST_STYLES['fig_style'])
        ax = fig.add_subplot(111)

    text_x = 'Pressure (' + p_unit + ')'
    text_y = 'Selectivity ' + convert_chemformula(adsorbate1)
    title_graph = convert_chemformula(adsorbate1) + \
        ' in ' + convert_chemformula(adsorbate2)
    label = str(round(fraction, 2) * 100) + '% ' + \
        convert_chemformula(adsorbate1)

    # graph title
    ax.set_title(title_graph, **IAST_STYLES['title_style'])

    # labels for the axes
    ax.set_xlabel(text_x, **IAST_STYLES['label_style'])
    ax.set_ylabel(text_y, **IAST_STYLES['label_style'])
    ax.tick_params(axis='both', which='major', **IAST_STYLES['tick_style'])

    # Regular data
    ax.plot(p_data, s_data, label=label)

    ax.legend(loc='best', **IAST_STYLES['legend_style'])

    ax.grid(True, zorder=5)
    ax.set_ylim(bottom=0)
    ax.set_xscale('linear')

    return ax
