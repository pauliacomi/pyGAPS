import matplotlib as mpl

from pygaps.graphing.isotherm_graphs import plot_iso
from pygaps.graphing.mpl_styles import BASE_STYLE
from pygaps.graphing.mpl_styles import POINTS_MUTED


@mpl.rc_context(BASE_STYLE)
def plot_model_guesses(attempts, pressure, loading):
    """Plot one or more isotherm model fits."""
    ax = None
    for attempt in attempts:
        if attempt.model.calculates == 'pressure':
            pts = {'y1_points': loading}
        else:
            pts = {'x_points': pressure}

        if not ax:
            ax = plot_iso(attempts, lgd_pos=None, marker=None, **pts)
        else:
            plot_iso(attempts, ax=ax, lgd_pos=None, marker=None, **pts)

    with mpl.rc_context(POINTS_MUTED):
        ax.plot(pressure, loading)

    ax.legend([m.model.name for m in attempts])

    return ax
