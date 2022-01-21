# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa
# isort:skip_file

from .mpl_styles import *


# TODO: very bad, temporary solution
# https://matplotlib.org/stable/tutorials/introductory/customizing.html
# Ideally the matplotlib custom styles are defined in a better way
def plot_iso(*args, **kwargs):
    from .isotherm_graphs import plot_iso
    plot_iso(*args, **kwargs)
