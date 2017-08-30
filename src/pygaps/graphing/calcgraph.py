"""
This module contains the functions for plotting calculation-specific graphs
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def roq_plot(pressure, roq_points, minimum, maximum, p_monolayer, n_monolayer, roq_monolayer):
    """Draws the roquerol plot"""
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
    plt.show()


def bet_plot(pressure, bet_points, minimum, maximum, p_monolayer, n_monolayer, bet_monolayer):
    """Draws the bet plot"""
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pressure, bet_points,
             marker='', color='g', label='all points')
    ax1.plot(pressure[minimum:maximum], bet_points[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    ax1.plot(p_monolayer, bet_monolayer,
             marker='x', linestyle='', color='black', label='monolayer point')
    ax1.set_ylim(ymin=0, ymax=bet_points[maximum] * 1.2)
    ax1.set_xlim(
        xmin=0, xmax=pressure[maximum] * 1.2)
    ax1.set_title("BET plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')
    plt.show()


def psd_plot(pore_radii, pore_dist, log=True, xmax=None):
    """Draws the pore size distribution plot"""
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pore_radii, pore_dist,
             marker='', color='g', label='distribution')
    if(log):
        ax1.set_xscale('log')
        ax1.xaxis.set_major_locator(ticker.LogLocator(
            base=10.0, numticks=15, numdecs=20))
    ax1.set_title("PSD plot")
    ax1.set_xlabel('Pore width (nm)')
    ax1.set_ylabel('Pore size')
    ax1.legend(loc='best')
    ax1.set_xlim(xmin=0, xmax=xmax)
    ax1.set_ylim(ymin=0)
    ax1.grid(True)
    plt.show()
