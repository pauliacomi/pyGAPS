"""
This module contains the functions for plotting calculation-specific graphs
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def roq_plot(pressure, roq_points, minimum, maximum,
             p_monolayer, roq_monolayer):
    """
    Draws the roquerol plot

    Parameters
    ----------
    pressure : array
        Pressure points which will make up the x axix
    roq_points : array
        Roquerol-transformed points which will make up the y axis
    minimum : int
        Lower bound of the selected points
    maximum : int
        Higher bound of the selected points
    p_monolayer : float
        Pressure at which statistical monolayer is achieved
    rol_monolayer : float
        Roquerol transform of the point at which statistical monolayer is achieved

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
    ax1.set_title("Roquerol plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')

    return ax1


def bet_plot(pressure, bet_points, minimum, maximum,
             slope, intercept, p_monolayer, bet_monolayer):
    """
    Draws the bet plot

    Parameters
    ----------
    pressure : array
        Pressure points which will make up the x axix
    bet_points : array
        BET-transformed points which will make up the y axis
    minimum : int
        Lower bound of the selected points
    maximum : int
        Higher bound of the selected points
    slope : float
        Slope of the chosen linear region
    intercept : float
        Intercept of the cosen linear region
    p_monolayer : float
        Pressure at which statistical monolayer is achieved
    rol_monolayer : float
        BET transform of the point at which statistical monolayer is achieved

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

    ax1.set_ylim(ymin=0, ymax=bet_points[maximum] * 1.2)
    ax1.set_xlim(
        xmin=0, xmax=pressure[maximum] * 1.2)
    ax1.set_title("BET plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')

    return ax1


def plot_tp(thickness_curve, loading, results, alpha_s=False):
    """
    Draws the t-plot
    Also used for alpha-s plot

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
        Whether the function is used for alpha_s display

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
        label2 = '$\\alpha_s (V/V_0.4)$'
        label3 = '$\\alpha_s$ method'
    else:
        label1 = 't transform'
        label2 = 'layer thickness (nm)'
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
                 color='black', label='linear' + str(index))

    ax1.set_title(label3)
    ax1.set_xlim(xmin=0)
    ax1.set_ylim(ymin=0)
    ax1.set_xlabel(label2)
    ax1.set_ylabel('amount adsorbed (mol/g)')
    ax1.legend(loc='best')

    return ax1


def psd_plot(pore_radii, pore_dist, method=None, log=True, xmax=None):
    """
    Draws the pore size distribution plot

    Parameters
    ----------
    pore_radii : array
        Array of the pore radii which will become the x axis
    pore_dist : array
        Contribution of each pore radius which will make up the y axis
    log : int
        Whether to display a logarithmic graph
    xmax : int
        Higher bound of the selected pore widths

    Returns
    -------
    matplotlib.axes
        Matplotlib axes of the graph generated. The user can then apply their
        own styling if desired.

    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pore_radii, pore_dist,
             marker='', color='g', label='distribution')
    if(log):
        ax1.set_xscale('log')
        ax1.xaxis.set_major_locator(ticker.LogLocator(
            base=10.0, numticks=15, numdecs=20))
    ax1.set_title("PSD plot " + str(method))
    ax1.set_xlabel('Pore width (nm)')
    ax1.set_ylabel('Pore size')
    ax1.legend(loc='best')
    ax1.set_xlim(xmin=0, xmax=xmax)
    ax1.set_ylim(ymin=0)
    ax1.grid(True)

    return ax1
