"""Functions for plotting calculation-specific graphs."""

from . import plt
from .mpl_styles import FIG_STYLE
from .mpl_styles import LABEL_STYLE
from .mpl_styles import LEGEND_STYLE
from .mpl_styles import POINTS_ALL_STYLE
from .mpl_styles import POINTS_SEL_STYLE
from .mpl_styles import TICK_STYLE
from .mpl_styles import TITLE_STYLE


def roq_plot(
    pressure,
    roq_points,
    minimum,
    maximum,
    p_monolayer,
    roq_monolayer,
    ax=None
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
        _, ax = plt.pyplot.subplots(figsize=(6, 4))

    ax.plot(
        pressure,
        roq_points,
        label='all points',
        **POINTS_ALL_STYLE,
    )
    ax.plot(
        pressure[minimum:maximum],
        roq_points[minimum:maximum],
        label='chosen points',
        **POINTS_SEL_STYLE,
    )
    ax.plot(
        p_monolayer,
        roq_monolayer,
        marker='X',
        markersize=10,
        linestyle='',
        color='k',
        label='monolayer point'
    )
    ax.set_title("Rouquerol plot")
    ax.set_xlabel('p/p°', fontsize=15)
    ax.set_ylabel('$n ( 1 - p/p°)$', fontsize=10)
    ax.legend(loc='best')

    return ax


def bet_plot(
    pressure,
    bet_points,
    minimum,
    maximum,
    slope,
    intercept,
    p_monolayer,
    bet_monolayer,
    ax=None
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
        _, ax = plt.pyplot.subplots(figsize=(6, 4))

    ax.plot(
        pressure,
        bet_points,
        label='all points',
        **POINTS_ALL_STYLE,
    )
    ax.plot(
        pressure[minimum:maximum],
        bet_points[minimum:maximum],
        label='chosen points',
        **POINTS_SEL_STYLE,
    )
    x_lim = [0, pressure[maximum]]
    y_lim = [slope * x_lim[0] + intercept, slope * x_lim[1] + intercept]
    ax.plot(
        x_lim,
        y_lim,
        linestyle='--',
        color='black',
        label='model fit',
    )
    ax.plot(
        p_monolayer,
        bet_monolayer,
        marker='X',
        markersize=10,
        linestyle='',
        color='k',
        label='monolayer point'
    )

    ax.set_ylim(bottom=0, top=bet_points[maximum] * 1.2)
    ax.set_xlim(left=0, right=pressure[maximum] * 1.2)
    ax.set_title("BET plot")
    ax.set_xlabel('p/p°', fontsize=15)
    ax.set_ylabel('$\\frac{p/p°}{n ( 1- p/p°)}$', fontsize=15)
    ax.legend(loc='best')

    return ax


def langmuir_plot(
    pressure, langmuir_points, minimum, maximum, slope, intercept, ax=None
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
        _, ax = plt.pyplot.subplots(figsize=(6, 4))

    ax.plot(
        pressure,
        langmuir_points,
        label='all points',
        **POINTS_ALL_STYLE,
    )
    ax.plot(
        pressure[minimum:maximum],
        langmuir_points[minimum:maximum],
        label='chosen points',
        **POINTS_SEL_STYLE,
    )
    x_lim = [0, pressure[maximum]]
    y_lim = [slope * x_lim[0] + intercept, slope * x_lim[1] + intercept]
    ax.plot(
        x_lim,
        y_lim,
        linestyle='--',
        color='black',
        label='model fit',
    )

    ax.set_ylim(bottom=0, top=langmuir_points[maximum] * 1.2)
    ax.set_xlim(left=0, right=pressure[maximum] * 1.2)
    ax.set_title("Langmuir plot")
    ax.set_xlabel('p/p°', fontsize=15)
    ax.set_ylabel('(p/p°)/n', fontsize=15)
    ax.legend(loc='best')

    return ax


def tp_plot(
    thickness_curve,
    loading,
    results,
    alpha_s=False,
    alpha_reducing_p=None,
    ax=None
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

            - ``section(array)`` : the points of the plot chosen for the line
            - ``area(float)`` : calculated surface area, from the section parameters
            - ``adsorbed_volume(float)`` : the amount adsorbed in the pores as calculated
              per section
            - ``slope(float)`` : slope of the straight trendline fixed through the region
            - ``intercept(float)`` : intercept of the straight trendline through the region
            - ``corr_coef(float)`` : correlation coefficient of the linear region

    alpha_s : bool
        Whether the function is used for alpha_s display.
    alpha_reducing_p : bool
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
        _, ax = plt.pyplot.subplots()

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
        **POINTS_ALL_STYLE,
    )
    style = POINTS_SEL_STYLE.copy()
    for index, result in enumerate(results):
        style['color'] = f"C{index}"
        # plot chosen points
        ax.plot(
            thickness_curve[result.get('section')],
            loading[result.get('section')],
            **style,
        )

        # plot line
        min_lim = 0
        max_lim = max(thickness_curve[result.get('section')]) * 1.2
        x_lim = [min_lim, max_lim]
        y_lim = [
            result.get('slope') * min_lim + result.get('intercept'),
            result.get('slope') * max_lim + result.get('intercept')
        ]

        ax.plot(
            x_lim,
            y_lim,
            linestyle='--',
            color=f"C{index}",
            label=f'linear {index+1}'
        )

    ax.set_title(label_title)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(label_x)
    ax.set_ylabel('Loading')
    ax.legend(loc='best', frameon=False)

    return ax


def psd_plot(
    pore_widths,
    pore_dist,
    pore_vol_cum=None,
    method=None,
    labeldiff='distribution',
    labelcum='cumulative',
    line_style=None,
    log=True,
    right=None,
    left=None,
    ax=None
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
    line_style : dict, optional
        The style dictionary to send to the plot() function.
    log : int
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
        fig = plt.pyplot.figure(figsize=(15, 5))
        ax = fig.add_subplot(111)

    lst = {'marker': '', 'color': 'k'}
    if line_style is not None:
        lst.update(line_style)

    l1 = ax.plot(pore_widths, pore_dist, label=labeldiff, **lst)
    if labelcum:
        ax2 = ax.twinx()
        l2 = ax2.plot(
            pore_widths,
            pore_vol_cum,
            marker='',
            color='r',
            linestyle="--",
            label=labelcum
        )

    def formatter(x, pos):
        """Forces matplotlib to display whole numbers"""
        return f"{x:g}"

    if log:
        ax.set_xscale('log')
        ax.xaxis.set_minor_formatter(plt.ticker.FuncFormatter(formatter))
        ax.xaxis.set_major_formatter(plt.ticker.FuncFormatter(formatter))
        ax.xaxis.set_major_locator(
            plt.ticker.LogLocator(base=10.0, numticks=15, numdecs=20)
        )
        ax.tick_params(
            axis='x', which='minor', width=0.75, length=2.5, **TICK_STYLE
        )
        ax.tick_params(
            axis='x', which='major', width=2, length=10, **TICK_STYLE
        )
        ax.set_xlim(left=left, right=right)
    else:
        if not left:
            left = 0
        ax.set_xlim(left=left, right=right)
        ax.tick_params(axis='both', which='major', **TICK_STYLE)

    ax.set_title("PSD plot " + str(method), **TITLE_STYLE)
    ax.set_xlabel('Pore width [nm]', **LABEL_STYLE)
    ax.set_ylabel('Distribution [dV/dw]', **LABEL_STYLE)
    if labelcum:
        ax2.set_ylabel('Cumulative Vol [$cm^3 g^{-1}$]', **LABEL_STYLE)

    lns = l1
    if labelcum:
        lns = l1 + l2
    ax.legend(
        lns, [lbl.get_label() for lbl in lns], loc='lower right', fontsize=13
    )
    ax.set_ylim(bottom=0)
    if labelcum:
        ax2.set_ylim(bottom=0)
    ax.grid(True)

    return ax


def isosteric_enthalpy_plot(
    loading, isosteric_enthalpy, std_err, log=False, ax=None
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
        _, ax = plt.pyplot.subplots(**FIG_STYLE)

    ax.errorbar(
        loading,
        isosteric_enthalpy,
        yerr=std_err,
        marker='o',
        markersize=3,
        label=r'$\Delta h_{st}$',
    )
    if log:
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(
            plt.ticker.LogLocator(base=10.0, numticks=15, numdecs=20)
        )
    ax.set_title("Isosteric enthalpy", **TITLE_STYLE)
    ax.set_xlabel(r'Loading [$mmol\/g^{-1}$]', **LABEL_STYLE)
    ax.set_ylabel(r'Isosteric enthalpy [$kJ\/mol^{-1}$]', **LABEL_STYLE)
    ax.legend(loc='best', **LEGEND_STYLE)
    ax.tick_params(axis='both', which='major', **TICK_STYLE)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    return ax


def initial_enthalpy_plot(
    loading,
    enthalpy,
    fitted_enthalpy,
    log=False,
    title=None,
    extras=None,
    ax=None
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
        _, ax = plt.pyplot.subplots(**FIG_STYLE)

    ax.plot(
        loading,
        enthalpy,
        marker='o',
        color='black',
        label='original',
        linestyle=''
    )
    ax.plot(loading, fitted_enthalpy, color='r', label='fitted', linestyle='-')

    if extras is not None:
        for param in extras:
            ax.plot(param[0], param[1], label=param[2], linestyle='--')
    if log:
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(
            plt.ticker.LogLocator(base=10.0, numticks=15, numdecs=20)
        )

    ax.set_title(title + " initial enthalpy fit")
    ax.set_xlabel('Loading', **LABEL_STYLE)
    ax.set_ylabel('Enthalpy', **LABEL_STYLE)
    ax.legend(loc='best', **LEGEND_STYLE)
    ax.set_ylim(bottom=0, top=(max(enthalpy) * 1.2))
    ax.set_xlim(left=0)
    ax.tick_params(axis='both', which='major', **TICK_STYLE)

    return ax


def dra_plot(
    logv,
    log_n_p0p,
    minimum,
    maximum,
    slope,
    intercept,
    exp,
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
        _, ax = plt.pyplot.subplots()

    ax.plot(log_n_p0p, logv, label='all points', **POINTS_ALL_STYLE)
    ax.plot(
        log_n_p0p[minimum:maximum],
        logv[minimum:maximum],
        marker='o',
        linestyle='',
        color='r',
        label='chosen points'
    )
    ax.plot(
        log_n_p0p,
        slope * log_n_p0p + intercept,
        linestyle='--',
        color='black',
        label='model fit'
    )

    ax.set_xlabel('log $p^0/p$')
    ax.set_ylabel('log $V/V_0$')
    ax.legend()

    return ax


def virial_plot(
    loading,
    ln_p_over_n,
    n_load,
    p_load,
    added_point,
    ax=None,
):
    """
    Draw a Virial plot.
    """
    # Generate the figure if needed
    if ax is None:
        _, ax = plt.pyplot.subplots(**FIG_STYLE)
    ax.plot(loading, ln_p_over_n, **POINTS_ALL_STYLE)
    ax.plot(n_load, p_load, '-')
    if added_point:
        ax.plot(1e-1, ln_p_over_n[0], 'or')
    ax.set_title("Virial fit", **TITLE_STYLE)
    ax.set_xlabel("Loading", **LABEL_STYLE)
    ax.set_ylabel("ln(p/n)", **LABEL_STYLE)
    ax.tick_params(axis='both', which='major', **TICK_STYLE)

    return ax
