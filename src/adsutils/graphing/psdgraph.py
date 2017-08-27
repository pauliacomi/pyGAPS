import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def psd_plot(fig, pore_radii, pore_dist):
    """Draws the pore size distribution plot"""
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pore_radii, pore_dist,
             marker='', color='g', label='distribution')
    ax1.set_xscale('log')
    ax1.set_title("PSD plot")
    ax1.set_xlabel('Pore width (nm)')
    ax1.set_ylabel('Pore size')
    ax1.legend(loc='best')
    ax1.set_ylim(ymin=0)
    ax1.grid(True)
    ax1.xaxis.set_major_locator(ticker.LogLocator(
        base=10.0, numticks=15, numdecs=20))
    plt.show()
