"""Functions for plotting and comparing isotherms."""

import collections.abc as abc
import copy
import math
import warnings
from itertools import cycle

import numpy
from cycler import cycler

from ..utilities.exceptions import GraphingError
from ..utilities.exceptions import ParameterError
from ..utilities.python_utilities import deep_merge
from . import plt
from .axis_labels import label_axis_text_pl
from .axis_labels import label_lgd
from .mpl_styles import ISO_STYLES

# list of branch types
_BRANCH_TYPES = {
    "ads": (True, False),
    "des": (False, True),
    "all": (True, True),
    "all-nol": (True, True)
}


def plot_iso(
    isotherms,
    ax=None,
    x_data: str = 'pressure',
    y1_data: str = 'loading',
    y2_data: str = None,
    branch: str = "all",
    logx: bool = False,
    logy1: bool = False,
    logy2: bool = False,
    color=True,
    marker=None,
    material_basis: str = None,
    material_unit: str = None,
    loading_basis: str = None,
    loading_unit: str = None,
    pressure_mode: str = None,
    pressure_unit: str = None,
    x_range=(None, None),
    y1_range=(None, None),
    y2_range=(None, None),
    x_points=None,
    y1_points=None,
    fig_title: str = None,
    lgd_keys=None,
    lgd_pos: str = 'best',
    save_path: str = None,
    **other_parameters
):
    """
    Plot the isotherm(s) provided on a single graph.

    Parameters
    ----------
    isotherms : PointIsotherms or list of Pointisotherms
        An isotherm or iterable of isotherms to be plotted.
    ax : matplotlib axes object, default None
        The axes object where to plot the graph if a new figure is
        not desired.

    x_data : str
        Key of data to plot on the x axis. Defaults to 'pressure'.
    y1_data : tuple
        Key of data to plot on the left y axis. Defaults to 'loading'.
    y2_data : tuple
        Key of data to plot on the right y axis. Defaults to None.
    branch : str
        Which branch to display, adsorption ('ads'), desorption ('des'),
        both ('all') or both with a single legend entry ('all-nol').
    logx : bool
        Whether the graph x axis should be logarithmic.
    logy1 : bool
        Whether the graph y1 axis should be logarithmic.
    logy2 : bool
        Whether the graph y2 axis should be logarithmic.

    color : bool, int, list, optional
        If a boolean, the option controls if the graph is coloured or
        grayscale. Grayscale graphs are usually preferred for publications
        or print media. If an int, it will be the number of colours the
        colourspace is divided into. If a list of matplotlib colour names
        or values, it will be passed directly to the plot function.
    marker : bool, int, list, optional
        Whether the graph should contain different markers.
        Implied ``True`` if color=False. Set both to "True" to
        get both effects at the same time.
        If an int, it will be the number of markers used.
        If a list of matplotlib markers,
        it will be passed directly to the plot function.

    material_basis : str, optional
        Whether the adsorption is read in terms of either 'per volume'
        or 'per mass'.
    material_unit : str, optional
        Unit of loading, otherwise first isotherm value is used.
    loading_basis : str, optional
        Loading basis, otherwise first isotherm value is used.
    loading_unit : str, optional
        Unit of loading, otherwise first isotherm value is used.
    pressure_mode : str, optional
        The pressure mode, either absolute pressures or relative in
        the form of p/p0, otherwise first isotherm value is used.
    pressure_unit : str, optional
        Unit of pressure, otherwise first isotherm value is used.

    x_range : tuple
        Range for data on the x axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    y1_range : tuple
        Range for data on the regular y axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    y2_range : tuple
        Range for data on the secondary y axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    x_points : tuple
        Specific points of pressure where to evaluate an isotherm. Assumes x=pressure.
    y1_points : tuple
        Specific points of loading where to evaluate an isotherm. Assumes y1=loading.

    fig_title : str
        Title of the graph. Defaults to none.
    lgd_keys : iterable
        The components of the isotherm which are displayed on the legend. For example
        pass ['material', 'adsorbate'] to have the legend labels display only these
        two components. Works with any isotherm properties and with 'branch' and 'key',
        the isotherm branch and the y-axis key respectively.
        Defaults to 'material' and 'adsorbate'.
    lgd_pos : [None, 'best', 'bottom', 'right', 'inner']
        Specify to have the legend position to the bottom, the right of the graph
        or inside the plot area itself. Defaults to 'best'.

    save_path : str, optional
        Whether to save the graph or not.
        If a path is provided, then that is where the graph will be saved.

    Other Parameters
    ----------------
    fig_style : dict
        A dictionary that will be passed into the matplotlib figure()
        function.

    title_style : dict
        A dictionary that will be passed into the matplotlib set_title() function.

    label_style : dict
        A dictionary that will be passed into the matplotlib set_label() function.

    y1_line_style : dict
        A dictionary that will be passed into the matplotlib plot() function.
        Applicable for left axis.

    y2_line_style : dict
        A dictionary that will be passed into the matplotlib plot() function.
        Applicable for right axis.

    tick_style : dict
        A dictionary that will be passed into the matplotlib tick_params() function.

    lgd_style : dict
        A dictionary that will be passed into the matplotlib legend() function.

    save_style : dict
        A dictionary that will be passed into the matplotlib savefig() function
        if the saving of the figure is selected.

    Returns
    -------
    axes : matplotlib.axes.Axes or numpy.ndarray of them

    """
    #######################################
    #
    # Initial checks

    # Make iterable if not already
    if not isinstance(isotherms, abc.Iterable):
        isotherms = (isotherms, )

    # Check for plot type validity
    if None in [x_data, y1_data]:
        raise ParameterError(
            "Specify a plot type to graph"
            " e.g. x_data=\'loading\', y1_data=\'pressure\'"
        )

    # Check if required keys are present in isotherms
    def keys(iso):
        return ['loading', 'pressure'] + getattr(iso, 'other_keys', [])

    if any(x_data not in keys(isotherm) for isotherm in isotherms):
        raise GraphingError(
            f"One of the isotherms supplied does not have {x_data} data."
        )

    if any(y1_data not in keys(isotherm) for isotherm in isotherms):
        raise GraphingError(
            f"One of the isotherms supplied does not have {y1_data} data."
        )

    if y2_data:
        if all(y2_data not in keys(isotherm) for isotherm in isotherms):
            raise GraphingError(
                f"None of the isotherms supplied have {y2_data} data"
            )
        if any(y2_data not in keys(isotherm) for isotherm in isotherms):
            warnings.warn(f"Some isotherms do not have {y2_data} data")

    # Store which branches will be displayed
    if not branch:
        raise ParameterError(
            "Specify a branch to display"
            " e.g. branch=\'ads\'"
        )
    if branch not in _BRANCH_TYPES:
        raise GraphingError(
            "The supplied branch type is not valid."
            f"Viable types are {_BRANCH_TYPES}"
        )

    ads, des = _BRANCH_TYPES[branch]

    # Pack other parameters
    log_params = dict(logx=logx, logy1=logy1, logy2=logy2)
    range_params = dict(x_range=x_range, y1_range=y1_range, y2_range=y2_range)
    iso_params = dict(
        pressure_mode=pressure_mode
        if pressure_mode else isotherms[0].pressure_mode,
        pressure_unit=pressure_unit
        if pressure_unit else isotherms[0].pressure_unit,
        loading_basis=loading_basis
        if loading_basis else isotherms[0].loading_basis,
        loading_unit=loading_unit
        if loading_unit else isotherms[0].loading_unit,
        material_basis=material_basis
        if material_basis else isotherms[0].material_basis,
        material_unit=material_unit
        if material_unit else isotherms[0].material_unit,
    )

    #######################################
    #
    # Settings and graph generation

    # Create style dictionaries and get user defined ones
    styles = copy.deepcopy(ISO_STYLES)

    # Overwrite with any user provided styles
    for style in styles:
        new_style = other_parameters.get(style, None)
        if new_style:
            styles[style] = deep_merge(styles[style], new_style)

    #
    # Generate or assign the figure and the axes
    if ax:
        ax1 = ax
        fig = ax1.get_figure()
    else:
        fig = plt.pyplot.figure(**styles['fig_style'])
        ax1 = fig.add_subplot(111)

    # Create second axes object, populate it if required
    ax2 = ax1.twinx() if y2_data else None

    # Get a cycling style for the graph
    #
    # Color styling
    if color:
        if isinstance(color, bool):
            colors = (plt.cm.jet(x) for x in numpy.linspace(0, 1, 7))
        elif isinstance(color, int):
            colors = (plt.cm.jet(x) for x in numpy.linspace(0, 1, color))
        elif isinstance(color, abc.Iterable):
            colors = color
        else:
            raise ParameterError("Unknown ``color`` parameter type.")

        color_cy = cycler('color', colors)

    else:
        color_cy = cycler('color', ['black', 'grey', 'silver'])
    #
    # Marker styling
    all_markers = ('o', 's', 'D', 'P', '*', '<', '>', 'X', 'v', '^')
    if marker is None:
        marker = True

    cycle_compose = True
    if isinstance(marker, bool):
        if marker:
            cycle_compose = False
            markers = all_markers
        else:
            markers = ()
    elif isinstance(marker, int):
        marker = len(all_markers) if marker > len(all_markers) else marker
        markers = all_markers[:marker]
    elif isinstance(marker, abc.Iterable):
        markers = marker
    else:
        raise ParameterError("Unknown ``marker`` parameter type.")

    y1_marker_cy = cycler('marker', markers)
    y2_marker_cy = cycler('marker', markers[::-1])

    # Combine cycles
    def extend_cycle(cy_1, cy_2):
        l_1 = len(cy_1)
        l_2 = len(cy_2)
        if l_1 == 0:
            return cycle(cy_2)
        if l_2 == 0:
            return cycle(cy_1)
        if l_1 > l_2:
            return cycle(cy_1 + (cy_2 * math.ceil(l_1 / l_2))[:l_1])
        return cycle(cy_2 + (cy_1 * math.ceil(l_2 / l_1))[:l_2])

    if cycle_compose:
        pc_primary = extend_cycle(y1_marker_cy, color_cy)
        pc_secondary = extend_cycle(y2_marker_cy, color_cy)
    else:
        pc_primary = cycle(y1_marker_cy * color_cy)
        pc_secondary = cycle(y2_marker_cy * color_cy)

    # Labels and ticks
    x_label = label_axis_text_pl(iso_params, x_data)
    y1_label = label_axis_text_pl(iso_params, y1_data)
    ax1.set_xlabel(x_label, **styles['label_style'])
    ax1.set_ylabel(y1_label, **styles['label_style'])
    ax1.tick_params(axis='both', which='major', **styles['tick_style'])
    if y2_data:
        y2_label = label_axis_text_pl(iso_params, y2_data)
        ax2.set_ylabel(y2_label, **styles['label_style'])
        ax2.tick_params(axis='both', which='major', **styles['tick_style'])

    # Graph title
    if fig_title:
        ax1.set_title(fig_title, **styles['title_style'])

    ###########################################
    #
    # Generic axes graphing function
    #

    def _data_plot(isotherm, current_branch, y1_style, y2_style, **iso_params):
        """Plot the y1 data and y2 data of each branch."""

        # Plot line 1
        y1_lbl = label_lgd(isotherm, lgd_keys, current_branch, branch, y1_data)

        if x_points is not None:
            x_p = x_points
            y1_p = _get_data(
                isotherm, y1_data, current_branch, y1_range, x_points,
                **iso_params
            )
        elif y1_points is not None:
            x_p = _get_data(
                isotherm, x_data, current_branch, x_range, y1_points,
                **iso_params
            )
            y1_p = y1_points
        else:
            x_p = _get_data(
                isotherm, x_data, current_branch, x_range, **iso_params
            )
            y1_p = _get_data(
                isotherm, y1_data, current_branch, y1_range, **iso_params
            )
            x_p, y1_p = x_p.align(y1_p, join='inner')

        ax1.plot(x_p, y1_p, label=y1_lbl, **y1_style)

        # Plot line 2 (if applicable)
        if y2_data and y2_data in keys(isotherm):

            y2_p = _get_data(
                isotherm, y2_data, current_branch, y2_range, **iso_params
            )
            aligned = x_p.align(y2_p, join='inner')

            y2_lbl = label_lgd(
                isotherm, lgd_keys, current_branch, branch, y2_data
            )
            ax2.plot(aligned[0], aligned[1], label=y2_lbl, **y2_style)

    #####################################
    #
    # Actual plotting
    #
    # Plot the data
    for isotherm in isotherms:

        # Line styles for the current isotherm
        y1_line_style = next(pc_primary)
        y2_line_style = next(pc_secondary)
        y1_line_style.update(styles['y1_line_style'])
        y2_line_style.update(styles['y2_line_style'])

        # If there's an adsorption branch, plot it
        if ads and isotherm.has_branch('ads'):
            _data_plot(
                isotherm, 'ads', y1_line_style, y2_line_style, **iso_params
            )

        # Switch to desorption linestyle (dotted, open marker)
        y1_line_style['markerfacecolor'] = 'none'
        y1_line_style['linestyle'] = '--'
        y2_line_style['markerfacecolor'] = 'none'

        # If there's a desorption branch, plot it
        if des and isotherm.has_branch('des'):
            _data_plot(
                isotherm, 'des', y1_line_style, y2_line_style, **iso_params
            )

    #####################################
    #
    # Final settings

    _final_styling(
        fig, ax1, ax2, log_params, range_params, lgd_pos, styles, save_path
    )

    if ax2:
        return [ax1, ax2]
    return ax1


def _get_data(
    isotherm,
    data_name,
    current_branch,
    drange=None,
    points=None,
    **kwargs,
):
    """Get different data from an isotherm."""
    if data_name == 'pressure':
        if points is not None:
            return isotherm.pressure_at(
                points,
                branch=current_branch,
                pressure_mode=kwargs['pressure_mode'],
                pressure_unit=kwargs['pressure_unit'],
            )
        return isotherm.pressure(
            branch=current_branch,
            pressure_mode=kwargs['pressure_mode'],
            pressure_unit=kwargs['pressure_unit'],
            limits=drange,
            indexed=True,
        )
    elif data_name == 'loading':
        if points is not None:
            return isotherm.loading_at(
                points,
                branch=current_branch,
                loading_basis=kwargs['loading_basis'],
                loading_unit=kwargs['loading_unit'],
                material_basis=kwargs['material_basis'],
                material_unit=kwargs['material_unit'],
            )
        return isotherm.loading(
            branch=current_branch,
            loading_basis=kwargs['loading_basis'],
            loading_unit=kwargs['loading_unit'],
            material_basis=kwargs['material_basis'],
            material_unit=kwargs['material_unit'],
            limits=drange,
            indexed=True,
        )
    return isotherm.other_data(
        data_name,
        branch=current_branch,
        limits=drange,
        indexed=True,
    )


def _final_styling(
    fig, ax1, ax2, log_params, range_params, lgd_pos, styles, save_path
):
    """Axes scales and limits, legend and graph saving."""
    # Convert the axes into logarithmic if required
    if log_params['logx']:
        ax1.set_xscale('log')
    else:
        ax1.set_xlim(left=0)
    if log_params['logy1']:
        ax1.set_yscale('log')
    else:
        ax1.set_ylim(bottom=0)
    if ax2 and log_params['logy2']:
        ax2.set_yscale('log')

    # Axes range settings
    ax1.set_xlim(range_params['x_range'])
    ax1.set_ylim(range_params['y1_range'])
    if ax2:
        ax2.set_ylim(range_params['y2_range'])

    # Add the legend
    lines, labels = ax1.get_legend_handles_labels()
    if ax2:
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines = lines + lines2
        labels = labels + labels2

    lgd = None

    if lgd_pos == 'best':
        if len(lines) > 5:
            lgd_pos = 'right'
        else:
            lgd_pos = 'inner'

    if lgd_pos is None:
        pass
    elif lgd_pos == 'inner':
        lgd = ax1.legend(lines, labels, **styles['lgd_style'])
    elif lgd_pos == 'bottom':
        lgd_style = {}
        lgd_style['bbox_to_anchor'] = (0.5, 0)
        lgd_style['loc'] = 'upper center'
        lgd_style['bbox_transform'] = fig.transFigure
        lgd_style['ncol'] = 2
        lgd_style.update(styles['lgd_style'])
        lgd = fig.legend(lines, labels, **lgd_style)
    elif lgd_pos == 'right':
        lgd_style = {}
        lgd_style['bbox_to_anchor'] = (1, 0.5)
        lgd_style['loc'] = 'center left'
        lgd_style['bbox_transform'] = fig.transFigure
        lgd_style.update(styles['lgd_style'])
        lgd = fig.legend(lines, labels, **lgd_style)
    elif lgd_pos == 'left':
        lgd_style = {}
        lgd_style['bbox_to_anchor'] = (0, 0.5)
        lgd_style['loc'] = 'center right'
        lgd_style['bbox_transform'] = fig.transFigure
        lgd_style.update(styles['lgd_style'])
        lgd = fig.legend(lines, labels, **lgd_style)
    else:
        lgd = ax1.legend(lines, labels, **styles['lgd_style'])

    bbox_extra_artists = []
    if lgd:
        bbox_extra_artists.append(lgd)

    # Fix size of graphs
    fig.tight_layout()

    # Save if desired
    if save_path:
        fig.savefig(
            save_path,
            bbox_extra_artists=bbox_extra_artists,
            bbox_inches='tight',
            **styles['save_style'],
            dpi=300,
        )
