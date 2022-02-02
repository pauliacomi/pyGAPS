import matplotlib as mpl

from pygaps.graphing.isotherm_graphs import plot_iso
from pygaps.graphing.mpl_styles import BASE_STYLE
from pygaps.graphing.mpl_styles import POINTS_MUTED


@mpl.rc_context(BASE_STYLE)
def plot_model_guesses(attempts, pressure, loading):
    ax = plot_iso(
        attempts,
        x_points=pressure,
        lgd_pos=None,
        marker=None,
    )
    with mpl.rc_context(POINTS_MUTED):
        ax.plot(pressure, loading)
        ax.legend([m.model.name for m in attempts])

    return ax
