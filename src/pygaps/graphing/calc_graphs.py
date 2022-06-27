"""Functions for plotting calculation-specific graphs."""

import typing as t

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from pygaps.graphing.labels import label_units_iso
from pygaps.graphing.mpl_styles import BASE_STYLE
from pygaps.graphing.mpl_styles import LINE_ERROR
from pygaps.graphing.mpl_styles import LINE_FIT
from pygaps.graphing.mpl_styles import POINTS_HIGHLIGHTED
from pygaps.graphing.mpl_styles import POINTS_IMPORTANT
from pygaps.graphing.mpl_styles import POINTS_MUTED


@mpl.rc_context(BASE_STYLE)
def roq_plot(
    pressure: t.Iterable[float],
    roq_points: t.Iterable[float],
    minimum: int,
    maximum: int,
    p_monolayer: float,
    roq_monolayer: float,
    ax=None,
):
    """
    Draw a Rouquerol plot.

    Parameters
    ----------
    pressure : array
        Pressure points which will make up the x axis.
    roq_points : array
        Rouquerol-transformed points which will make up the y axis.
    minimum : int
        Lower bound of the selected points.
    maximum : int
        Higher bound of the selected points.
    p_monolayer : float
        Pressure at which statistical monolayer is achieved.
    rol_monolayer : float
        Rouquerol transform of the point at which statistical monolayer is achieved.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))

    with mpl.rc_context(POINTS_MUTED):
        ax.plot(
            pressure,
            roq_points,
            label='all points',
        )
    with mpl.rc_context(POINTS_HIGHLIGHTED):
        ax.plot(
            pressure[minimum:maximum + 1],
            roq_points[minimum:maximum + 1],
            label='chosen points',
        )
    with mpl.rc_context(POINTS_IMPORTANT):
        ax.plot(
            p_monolayer,
            roq_monolayer,
            label='monolayer point',
        )
    ax.set_title("Rouquerol plot")
    ax.set_xlabel('p/p°')
    ax.set_ylabel('$n ( 1 - p/p°)$')
    ax.legend(loc='best')

    return ax


@mpl.rc_context(BASE_STYLE)
def bet_plot(
    pressure: t.Iterable[float],
    bet_points: t.Iterable[float],
    minimum: int,
    maximum: int,
    slope: float,
    intercept: float,
    p_monolayer: float,
    bet_monolayer: float,
    ax=None,
):
    """
    Draw a BET plot.

    Parameters
    ----------
    pressure : array
        Pressure points which will make up the x axis.
    bet_points : array
        BET-transformed points which will make up the y axis.
    minimum : int
        Lower bound of the selected points.
    maximum : int
        Higher bound of the selected points.
    slope : float
        Slope of the chosen linear region.
    intercept : float
        Intercept of the chosen linear region.
    p_monolayer : float
        Pressure at which statistical monolayer is achieved.
    rol_monolayer : float
        BET transform of the point at which statistical monolayer is achieved.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))

    with mpl.rc_context(POINTS_MUTED):
        ax.plot(
            pressure,
            bet_points,
            label='all points',
        )
    with mpl.rc_context(POINTS_HIGHLIGHTED):
        ax.plot(
            pressure[minimum:maximum + 1],
            bet_points[minimum:maximum + 1],
            label='chosen points',
        )
    x_lim = [0, pressure[maximum]]
    y_lim = [slope * x_lim[0] + intercept, slope * x_lim[1] + intercept]
    with mpl.rc_context(LINE_FIT):
        ax.plot(
            x_lim,
            y_lim,
            color='black',
            label='model fit',
        )
    with mpl.rc_context(POINTS_IMPORTANT):
        ax.plot(
            p_monolayer,
            bet_monolayer,
            label='monolayer point',
        )

    ax.set_ylim(bottom=0, top=bet_points[maximum] * 1.2)
    ax.set_xlim(left=0, right=pressure[maximum] * 1.2)
    ax.set_title("BET plot")
    ax.set_xlabel('p/p°')
    ax.set_ylabel('$\\frac{p/p°}{n ( 1- p/p°)}$')
    ax.legend(loc='best')

    return ax


@mpl.rc_context(BASE_STYLE)
def langmuir_plot(
    pressure: t.Iterable[float],
    langmuir_points: t.Iterable[float],
    minimum: int,
    maximum: int,
    slope: float,
    intercept: float,
    ax=None,
):
    """
    Draw a Langmuir plot.

    Parameters
    ----------
    pressure : array
        Pressure points which will make up the x axix.
    langmuir_points : array
        Langmuir-transformed points which will make up the y axis.
    minimum : int
        Lower bound of the selected points.
    maximum : int
        Higher bound of the selected points.
    slope : float
        Slope of the chosen linear region.
    intercept : float
        Intercept of the chosen linear region.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))

    with mpl.rc_context(POINTS_MUTED):
        ax.plot(
            pressure,
            langmuir_points,
            label='all points',
        )
    with mpl.rc_context(POINTS_HIGHLIGHTED):
        ax.plot(
            pressure[minimum:maximum],
            langmuir_points[minimum:maximum],
            label='chosen points',
        )
    x_lim = [0, pressure[maximum - 1]]
    y_lim = [slope * x_lim[0] + intercept, slope * x_lim[1] + intercept]
    with mpl.rc_context(LINE_FIT):
        ax.plot(
            x_lim,
            y_lim,
            linestyle='--',
            color='black',
            label='model fit',
        )

    ax.set_ylim(bottom=0, top=langmuir_points[maximum - 1] * 1.2)
    ax.set_xlim(left=0, right=pressure[maximum - 1] * 1.2)
    ax.set_title("Langmuir plot")
    ax.set_xlabel('p/p°')
    ax.set_ylabel('(p/p°)/n')
    ax.legend(loc='best')

    return ax


@mpl.rc_context(BASE_STYLE)
def tp_plot(
    thickness_curve: t.Iterable[float],
    loading: t.Iterable[float],
    results: dict,
    alpha_s: bool = False,
    alpha_reducing_p: float = None,
    ax=None,
):
    """
    Draw a t-plot (also used for the alpha-s plot).

    Parameters
    ----------
    thickness_curve : array
        Thickness of the adsorbed layer at selected points.
        In the case of alpha_s plot, it is the alpha_s transform of the
        reference isotherm.
    loading : array
        Loading of the isotherm to plot.
    results : dict
        Dictionary of linear regions selected with the members:

        - ``section`` (array) : the points of the plot chosen for the line
        - ``area`` (float) : calculated surface area, from the section parameters
        - ``adsorbed_volume`` (float) : the amount adsorbed in the pores as
          calculated per section
        - ``slope`` (float) : slope of the straight trendline fixed through the region
        - ``intercept`` (float) : intercept of the straight trendline through the region
        - ``corr_coef`` (float) : correlation coefficient of the linear region

    alpha_s : bool
        Whether the function is used for alpha_s display.
    alpha_reducing_p : float
        The reducing pressure used for alpha_s.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots()

    if alpha_s:
        label_points = '$\\alpha_s$ transform'
        label_x = '$\\alpha_s (V/V_{' + str(alpha_reducing_p) + '})$'
        label_title = '$\\alpha_s$ method'
    else:
        label_points = 't transform'
        label_x = 'Layer thickness [nm]'
        label_title = 't-plot method'

    ax.plot(
        thickness_curve,
        loading,
        label=label_points,
        color="k",
    )
    for index, result in enumerate(results):
        # plot chosen points
        with mpl.rc_context(POINTS_HIGHLIGHTED):
            ax.plot(
                thickness_curve[result.get('section')],
                loading[result.get('section')],
                color=f"C{index}",
            )

        # plot line
        min_lim = 0
        max_lim = max(thickness_curve[result.get('section')]) * 1.2
        x_lim = [min_lim, max_lim]
        y_lim = [
            result.get('slope') * min_lim + result.get('intercept'),
            result.get('slope') * max_lim + result.get('intercept')
        ]
        with mpl.rc_context(LINE_FIT):
            ax.plot(
                x_lim,
                y_lim,
                color=f"C{index}",
                label=f'linear {index+1}',
            )

    ax.set_title(label_title)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(label_x)
    ax.set_ylabel('Loading')
    ax.legend(loc='best')

    return ax


@mpl.rc_context(BASE_STYLE)
def psd_plot(
    pore_widths: t.Iterable[float],
    pore_dist: t.Iterable[float],
    pore_vol_cum: t.Iterable[float] = None,
    method: str = None,
    labeldiff: str = 'distribution',
    labelcum: str = 'cumulative',
    log: bool = True,
    right: int = None,
    left: int = None,
    ax=None,
):
    """
    Draw a pore size distribution plot.

    Parameters
    ----------
    pore_widths : array
        Array of the pore radii which will become the x axis.
    pore_dist : array
        Contribution of each pore radius which will make up the y axis.
    pore_vol_cum : array
        Pre-calculated cumulative value.
    method : str
        The method used. Will be a string part of the title.
    labeldiff : str
        The label for the plotted data, which will appear in the legend.
    labelcum : str, optional
        The label for the cumulative data, which will appear in the legend.
        Set to None to remove cumulative distribution
    log : bool
        Whether to display a logarithmic graph.
    right : int
        Higher bound of the selected pore widths.
    right : int
        Lower bound of the selected pore widths.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    # Generate the figure if needed
    if ax is None:
        fig = plt.figure(figsize=(15, 5))
        ax = fig.add_subplot(111)

    l1 = ax.plot(
        pore_widths,
        pore_dist,
        label=labeldiff,
        color='k',
    )
    if labelcum:
        ax2 = ax.twinx()
        l2 = ax2.plot(
            pore_widths,
            pore_vol_cum,
            color='r',
            label=labelcum,
        )

    def formatter(x, pos):
        """Forces matplotlib to display whole numbers"""
        return f"{x:g}"

    if log:
        ax.set_xscale('log')
        ax.xaxis.set_minor_formatter(ticker.FuncFormatter(formatter))
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(formatter))
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=15, numdecs=20))
        ax.tick_params(axis='x', which='minor', width=0.75, length=2.5)
        ax.tick_params(axis='x', which='major', width=2, length=10)
        ax.set_xlim(left=left, right=right)
    else:
        if not left:
            left = 0
        ax.set_xlim(left=left, right=right)
        ax.tick_params(axis='both', which='major')

    ax.set_title("PSD plot " + str(method))
    ax.set_xlabel('Pore width [nm]')
    ax.set_ylabel('Distribution, dV/dw [$cm^3 g^{-1} nm^{-1}$]')
    if labelcum:
        ax2.set_ylabel('Cumulative volume [$cm^3 g^{-1}$]')

    lns = l1
    if labelcum:
        lns = l1 + l2
    ax.legend(lns, [lbl.get_label() for lbl in lns], loc='lower right')
    ax.set_ylim(bottom=0)
    if labelcum:
        ax2.set_ylim(bottom=0)
    ax.grid(True)

    return ax


@mpl.rc_context(BASE_STYLE)
def isosteric_enthalpy_plot(
    loading: t.Iterable[float],
    isosteric_enthalpy: t.Iterable[float],
    std_err: t.Iterable[float],
    isotherm,
    log: bool = False,
    ax=None,
):
    """
    Draws the isosteric enthalpy plot.

    Parameters
    ----------
    loading : array
        Loadings for which the isosteric enthalpy was calculated.
    isosteric_enthalpy : array
        The isosteric enthalpy corresponding to each loading.
    std_err : array
        Standard error for each point.
    isotherm : PointIsotherm, ModelIsotherm
        An isotherm to determine graph units.
    log : int
        Whether to display a logarithmic graph.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots()

    with mpl.rc_context(LINE_ERROR):
        ax.errorbar(
            loading,
            isosteric_enthalpy,
            yerr=std_err,
            color='r',
            label=r'$\Delta h_{st}$',
        )
    if log:
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=15, numdecs=20))
    ax.set_xlabel(label_units_iso(isotherm, 'loading'))
    ax.set_ylabel(r'Isosteric enthalpy [$kJ\/mol^{-1}$]')
    ax.legend(loc='best')
    ax.tick_params(axis='both', which='major')
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    return ax


@mpl.rc_context(BASE_STYLE)
def initial_enthalpy_plot(
    loading: t.Iterable[float],
    enthalpy: t.Iterable[float],
    fitted_enthalpy: t.Iterable[float],
    log: bool = False,
    title: str = None,
    extras=None,  # TODO what is extra used for?
    ax=None,
):
    """
    Draws the initial enthalpy calculation plot.

    Parameters
    ----------
    loading : array
        Loadings for which the initial enthalpy was calculated.
    enthalpy : array
        The enthalpy corresponding to each loading.
    fitted_enthalpy : array
        The predicted enthalpy corresponding to each loading.
    log : int
        Whether to display a logarithmic graph
    title : str
        Name of the material to put in the title.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots()

    with mpl.rc_context(POINTS_MUTED):
        ax.plot(
            loading,
            enthalpy,
            label='original',
        )
    ax.plot(
        loading,
        fitted_enthalpy,
        color='r',
        label='fitted',
    )

    if extras is not None:
        with mpl.rc_context(LINE_FIT):
            for param in extras:
                ax.plot(
                    param[0],
                    param[1],
                    label=param[2],
                    linestyle='--',
                )
    if log:
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(plt.ticker.LogLocator(base=10.0, numticks=15, numdecs=20))

    ax.set_title(title + " initial enthalpy fit")
    ax.set_xlabel('Loading')
    ax.set_ylabel('Enthalpy')
    ax.legend(loc='best')
    ax.set_ylim(bottom=0, top=(max(enthalpy) * 1.2))
    ax.set_xlim(left=0)
    ax.tick_params(axis='both', which='major')

    return ax


@mpl.rc_context(BASE_STYLE)
def dra_plot(
    logv: t.Iterable[float],
    log_n_p0p: t.Iterable[float],
    minimum: int,
    maximum: int,
    slope: float,
    intercept: float,
    exp: float,
    ax=None,
):
    """
    Draw a Dubinin plot.

    Parameters
    ----------
    logv : array
        Logarithm of volume adsorbed.
    log_n_p0p : array
        Logarithm of pressure term.
    minimum : int
        Lower index of the selected points.
    maximum : int
        Higher index of the selected points.
    slope : float
        Slope of the fitted line.
    intercept : float
        Intercept of the fitted line.
    exp : float
        The exponent of the DA/DR graph.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots()

    with mpl.rc_context(POINTS_MUTED):
        ax.plot(
            log_n_p0p,
            logv,
            label='all points',
        )
    with mpl.rc_context(POINTS_HIGHLIGHTED):
        ax.plot(
            log_n_p0p[minimum:maximum + 1],
            logv[minimum:maximum + 1],
            label='chosen points',
        )
    with mpl.rc_context(LINE_FIT):
        ax.plot(
            log_n_p0p,
            slope * log_n_p0p + intercept,
            color='black',
            label='model fit',
        )

    ax.set_xlabel('log $p^0/p$')
    ax.set_ylabel('log $V/V_0$')
    ax.legend()

    return ax


@mpl.rc_context(BASE_STYLE)
def virial_plot(
    loading: t.Iterable[float],
    ln_p_over_n: t.Iterable[float],
    n_load: t.Iterable[float],
    p_load: t.Iterable[float],
    added_point: bool,
    ax=None,
):
    """
    Draw a Virial plot.
    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(loading, ln_p_over_n)
    ax.plot(n_load, p_load, '-')
    if added_point:
        ax.plot(1e-1, ln_p_over_n[0], 'or')
    ax.set_title("Virial fit")
    ax.set_xlabel("Loading")
    ax.set_ylabel("ln(p/n)")
    ax.tick_params(axis='both', which='major')

    return ax
