"""Functions for plotting graphs related to IAST calculations."""

import matplotlib as mpl
import matplotlib.pyplot as plt

from pygaps.graphing.mpl_styles import BASE_STYLE
from pygaps.utilities.string_utilities import convert_chemformula


@mpl.rc_context(BASE_STYLE)
def plot_iast(
    p_data: list,
    l_data: list,
    ads: list,
    p_label: str,
    l_label: str,
    ax=None,
):
    """
    Plot uptake-vs-pressure graph from IAST data.

    Parameters
    ----------
    p_data : array or list
        The pressures at which uptakes are calculated.
    l_data : 2D array or list of lists
        Uptake for each component a function of pressure.
    ads : list[str]
        Names of the adsorbates.
    p_unit : str
        Unit of pressure, for axis labelling.
    l_unit : str
        Unit of loading, for axis labelling.
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
        fig = plt.figure()
        ax = fig.add_subplot(111)

    ads = map(convert_chemformula, ads)

    title_graph = "IAST uptake"

    # graph title
    ax.set_title(title_graph)

    # labels for the axes
    ax.set_xlabel(p_label)
    ax.set_ylabel(l_label)
    ax.tick_params(axis='both', which='major')

    # Regular data
    for lo, ads in zip(l_data.T, ads):
        ax.plot(
            p_data,
            lo,
            label=ads,
            marker=".",
        )

    ax.legend(loc='best')

    return ax


@mpl.rc_context(BASE_STYLE)
def plot_iast_vle(
    x_data: list,
    y_data: list,
    ads1: str,
    ads2: str,
    pressure: float,
    p_unit: str,
    ax=None,
):
    """
    Plot a vapour-adsorbed equilibrium graph from IAST data.

    Parameters
    ----------
    x_data : array or list
        The molar fraction in the adsorbed phase.
    y_data : array or list
        The molar fraction in the gas phase.
    ads1 : str
        Name of the adsorbate which is regarded as the main component.
    ads2 : str
        Name of the adsorbate which is regarded as the secondary component.
    pressure : float
        Pressure at which the vle is plotted.
    p_unit : str
        Pressure unit, for labelling.
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
        fig = plt.figure()
        ax = fig.add_subplot(111)

    ads1 = convert_chemformula(ads1)
    ads2 = convert_chemformula(ads2)

    text_x = f"Bulk fraction {ads1}"
    text_y = f"Adsorbed fraction {ads1}"
    title_graph = f"{ads1} in {ads2}"
    label = f"{pressure:.2g} {p_unit}"

    # graph title
    ax.set_title(title_graph)

    # labels for the axes
    ax.set_xlabel(text_x)
    ax.set_ylabel(text_y)
    ax.tick_params(axis='both', which='major')

    # Regular data
    ax.plot(
        y_data,
        x_data,
        label=label,
        marker=".",
    )

    # Straight line
    line = [0, 1]
    ax.plot(line, line, color='black')

    ax.legend(loc='best')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    return ax


@mpl.rc_context(BASE_STYLE)
def plot_iast_svp(
    p_data: list,
    s_data: list,
    ads1: str,
    ads2: str,
    fraction: float,
    p_unit: str,
    ax=None,
):
    """
    Plot a selectivity-vs-pressure graph from IAST data.

    Parameters
    ----------
    p_data : array or list
        The pressures at which selectivity is calculated.
    s_data : array or list
        The selectivity towards the main component as a function of pressure.
    ads1 : str
        Name of the adsorbate which is regarded as the main component.
    ads2 : str
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
        fig = plt.figure()
        ax = fig.add_subplot(111)

    ads1 = convert_chemformula(ads1)
    ads2 = convert_chemformula(ads2)

    text_x = f"Pressure [{p_unit}]"
    text_y = f"Selectivity, {ads1}"
    title_graph = f"{ads1} in {ads2}"
    label = f"{fraction:.2%} {ads1}"

    # graph title
    ax.set_title(title_graph)

    # labels for the axes
    ax.set_xlabel(text_x)
    ax.set_ylabel(text_y)
    ax.tick_params(axis='both', which='major')

    # Regular data
    ax.plot(
        p_data,
        s_data,
        label=label,
        marker=".",
    )

    ax.legend(loc='best')

    ax.set_ylim(bottom=0)

    return ax
