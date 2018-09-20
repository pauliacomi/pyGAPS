"""
This module contains the functions for plotting calculation-specific graphs.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def roq_plot(pressure, roq_points, minimum, maximum,
             p_monolayer, roq_monolayer):
    """
    Draws the Rouquerol plot.

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

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pressure, roq_points,
             marker='', color='g', label='all points')
    ax1.plot(pressure[minimum:maximum], roq_points[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    ax1.plot(p_monolayer, roq_monolayer,
             marker='x', linestyle='', color='black', label='monolayer point')
    ax1.set_title("Rouquerol plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')

    return ax1


def bet_plot(pressure, bet_points, minimum, maximum,
             slope, intercept, p_monolayer, bet_monolayer):
    """
    Draws the BET plot.

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

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pressure, bet_points,
             marker='', color='g')
    ax1.plot(pressure[minimum:maximum], bet_points[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    x_lim = [0, pressure[maximum]]
    y_lim = [slope * x_lim[0] + intercept,
             slope * x_lim[1] + intercept]
    ax1.plot(x_lim, y_lim, linestyle='--', color='black', label='trendline')
    ax1.plot(p_monolayer, bet_monolayer,
             marker='x', linestyle='', color='black', label='monolayer point')

    ax1.set_ylim(bottom=0, top=bet_points[maximum] * 1.2)
    ax1.set_xlim(
        left=0, right=pressure[maximum] * 1.2)
    ax1.set_title("BET plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')

    return ax1


def langmuir_plot(pressure, langmuir_points, minimum, maximum,
                  slope, intercept):
    """
    Draws the Langmuir plot.

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

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pressure, langmuir_points,
             marker='', color='g')
    ax1.plot(pressure[minimum:maximum], langmuir_points[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    x_lim = [0, pressure[maximum]]
    y_lim = [slope * x_lim[0] + intercept,
             slope * x_lim[1] + intercept]
    ax1.plot(x_lim, y_lim, linestyle='--', color='black', label='trendline')

    ax1.set_ylim(bottom=0, top=langmuir_points[maximum] * 1.2)
    ax1.set_xlim(
        left=0, right=pressure[maximum] * 1.2)
    ax1.set_title("Langmuir plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/n')
    ax1.legend(loc='best')

    return ax1


def plot_tp(thickness_curve, loading, results, alpha_s=False, alpha_reducing_p=None):
    """
    Draws the t-plot.
    Also used for alpha-s plot.

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

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.
    """

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    if alpha_s:
        label1 = '$\\alpha_s$ method'
        label2 = '$\\alpha_s (V/V_{' + str(alpha_reducing_p) + '})$'
        label3 = '$\\alpha_s$ method'
    else:
        label1 = 't transform'
        label2 = 'Layer thickness (nm)'
        label3 = 't-plot method'
    ax1.plot(thickness_curve, loading,
             marker='', color='g', label=label1)

    for index, result in enumerate(results):
        # plot chosen points
        ax1.plot(thickness_curve[result.get('section')], loading[result.get('section')],
                 marker='.', linestyle='')

        # plot line
        min_lim = 0
        max_lim = max(thickness_curve[result.get('section')]) * 1.2
        x_lim = [min_lim, max_lim]
        y_lim = [result.get('slope') * min_lim + result.get('intercept'),
                 result.get('slope') * max_lim + result.get('intercept')]

        ax1.plot(x_lim, y_lim, linestyle='--',
                 color='black', label='linear' + str(index + 1))

    ax1.set_title(label3)
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.set_xlabel(label2)
    ax1.set_ylabel('Loading')
    ax1.legend(loc='best')

    return ax1


def psd_plot(pore_widths, pore_dist, method=None, label=None,
             log=True, right=None, left=None):
    """
    Draws the pore size distribution plot.

    Parameters
    ----------
    pore_widths : array
        Array of the pore radii which will become the x axis.
    pore_dist : array
        Contribution of each pore radius which will make up the y axis.
    method : str
        The method used. Will be a string part of the title.
    label : str
        The label for the plotted data, which will appear in the legend.
    log : int
        Whether to display a logarithmic graph.
    right : int
        Higher bound of the selected pore widths.
    right : int
        Lower bound of the selected pore widths.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    if not label:
        label = 'distribution'

    fig = plt.figure(figsize=(15, 5))
    ax1 = fig.add_subplot(111)
    ax1.plot(pore_widths, pore_dist,
             marker='', color='g', label=label)

    # Func formatter
    def formatter(x, pos):
        return "{0:g}".format(x)

    if log:

        ax1.set_xscale('log')
        ax1.xaxis.set_minor_formatter(ticker.FuncFormatter(formatter))
        ax1.xaxis.set_major_formatter(ticker.FuncFormatter(formatter))
        ax1.xaxis.set_major_locator(ticker.LogLocator(
            base=10.0, numticks=15, numdecs=20))
        ax1.tick_params(axis='x', which='minor', width=0.75,
                        length=2.5, labelsize=10)
        ax1.tick_params(axis='x', which='major',
                        width=2, length=10, labelsize=10)
        ax1.set_xlim(left=left, right=right)
    else:
        if not left:
            left = 0
        ax1.set_xlim(left=left, right=right)

    ax1.set_title("PSD plot " + str(method))
    ax1.set_xlabel('Pore width (nm)')
    ax1.set_ylabel('Distribution')
    ax1.legend(loc='best')
    ax1.set_ylim(bottom=0)
    ax1.grid(True)

    return ax1


def isosteric_heat_plot(loading, isosteric_heat, log=False):
    """
    Draws the isosteric heat plot.

    Parameters
    ----------
    loading : array
        Loadings for which the isosteric heat was calculated.
    isosteric_heat : array
        The isosteric heat corresponding to each loading.
    log : int
        Whether to display a logarithmic graph.
    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(loading, isosteric_heat,
             marker='o', color='g', label='heat')
    if(log):
        ax1.set_xscale('log')
        ax1.xaxis.set_major_locator(ticker.LogLocator(
            base=10.0, numticks=15, numdecs=20))
    ax1.set_title("Isosteric heat plot")
    ax1.set_xlabel('Loading')
    ax1.set_ylabel('Isosteric heat')
    ax1.legend(loc='best')
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.grid(True)

    return ax1


def initial_enthalpy_plot(loading, enthalpy, fitted_enthalpy, log=False,
                          title=None, extras=None):
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
        Name of the sample to put in the title.

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(loading, enthalpy,
             marker='o', color='black', label='original', linestyle='')
    ax1.plot(loading, fitted_enthalpy,
             color='r', label='fitted', linestyle='-')

    if extras is not None:
        for param in extras:
            ax1.plot(param[0], param[1], label=param[2], linestyle='--')
    if log:
        ax1.set_xscale('log')
        ax1.xaxis.set_major_locator(ticker.LogLocator(
            base=10.0, numticks=15, numdecs=20))

    ax1.set_title(title + " initial enthalpy fit")
    ax1.set_xlabel('Loading')
    ax1.set_ylabel('Enthalpy')
    ax1.legend(loc='best')
    ax1.set_ylim(bottom=0, top=(max(enthalpy) * 1.2))
    ax1.set_xlim(left=0)
    ax1.grid(True)

    return ax1
