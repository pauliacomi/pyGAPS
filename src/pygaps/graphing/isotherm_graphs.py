"""Functions for plotting and comparing isotherms."""

import math
import typing as t
from collections import abc
from itertools import cycle

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

from pygaps import logger
from pygaps.graphing.labels import label_lgd
from pygaps.graphing.labels import label_units_dict
from pygaps.graphing.mpl_styles import BASE_STYLE
from pygaps.graphing.mpl_styles import ISO_MARKERS
from pygaps.graphing.mpl_styles import ISO_STYLE
from pygaps.graphing.mpl_styles import Y1_COLORS
from pygaps.graphing.mpl_styles import Y2_COLORS
from pygaps.utilities.exceptions import GraphingError
from pygaps.utilities.exceptions import ParameterError

#: list of branch types
_BRANCH_TYPES = {
    "ads": (True, False),
    "des": (False, True),
    "all": (True, True),
}


@mpl.rc_context(BASE_STYLE)
@mpl.rc_context(ISO_STYLE)
def plot_iso(
    isotherms,
    ax=None,
    x_data: str = 'pressure',
    y1_data: str = 'loading',
    y2_data: str = None,
    branch: str = "all",
    x_range: t.Tuple[float, float] = (None, None),
    y1_range: t.Tuple[float, float] = (None, None),
    y2_range: t.Tuple[float, float] = (None, None),
    x_points: t.Iterable[float] = None,
    y1_points: t.Iterable[float] = None,
    material_basis: str = None,
    material_unit: str = None,
    loading_basis: str = None,
    loading_unit: str = None,
    pressure_mode: str = None,
    pressure_unit: str = None,
    logx: bool = False,
    logy1: bool = False,
    logy2: bool = False,
    color: t.Union[bool, str, t.Iterable[str]] = True,
    marker: t.Union[bool, str, t.Iterable[str]] = True,
    y1_line_style: dict = None,
    y2_line_style: dict = None,
    lgd_keys: list = None,
    lgd_pos: str = 'best',
    save_path: str = None,
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
        or both ('all').

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

    logx : bool
        Whether the graph x axis should be logarithmic.
    logy1 : bool
        Whether the graph y1 axis should be logarithmic.
    logy2 : bool
        Whether the graph y2 axis should be logarithmic.

    color : bool, int, list, optional
        If a boolean, the option controls if the graph is coloured or
        grayscale. Grayscale graphs are usually preferred for publications
        or print media. Otherwise, give a list of matplotlib colours
        or a number of colours to repeat in the cycle.
    marker : bool, int, list, optional
        Whether markers should be used to denote isotherm points.
        If an int, it will be the number of markers used.
        Otherwise, give a list of matplotlib markers
        or a number of markers to repeat in the cycle.
    y1_line_style : dict
        A dictionary that will be passed into the matplotlib plot() function.
        Applicable for left axis.
    y2_line_style : dict
        A dictionary that will be passed into the matplotlib plot() function.
        Applicable for right axis.
    lgd_keys : iterable
        The components of the isotherm which are displayed on the legend. For example
        pass ['material', 'adsorbate'] to have the legend labels display only these
        two components. Works with any isotherm properties and with 'branch' and 'key',
        the isotherm branch and the y-axis key respectively.
        Defaults to 'material' and 'adsorbate'.
    lgd_pos : [None, Matplotlib legend classifier, 'out bottom', 'out top', 'out left', out right]
        Specify to have the legend position outside the figure (out...)
        or inside the plot area itself (as determined by Matplotlib). Defaults to 'best'.

    save_path : str, optional
        Whether to save the graph or not.
        If a path is provided, then that is where the graph will be saved.

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
    else:
        isotherms = list(isotherms)

    # Check for plot validity
    if None in [x_data, y1_data]:
        raise ParameterError(
            "Specify a plot type to graph"
            " e.g. x_data=\'loading\', y1_data=\'pressure\'"
        )

    # Check if required keys are present in isotherms
    if any(x_data not in _get_keys(isotherm) for isotherm in isotherms):
        raise GraphingError(f"One of the isotherms supplied does not have {x_data} data.")

    if any(y1_data not in _get_keys(isotherm) for isotherm in isotherms):
        raise GraphingError(f"One of the isotherms supplied does not have {y1_data} data.")

    if y2_data:
        if all(y2_data not in _get_keys(isotherm) for isotherm in isotherms):
            raise GraphingError(f"None of the isotherms supplied have {y2_data} data")
        if any(y2_data not in _get_keys(isotherm) for isotherm in isotherms):
            logger.warning(f"Some isotherms do not have {y2_data} data")

    # Store which branches will be displayed
    if not branch:
        raise ParameterError("Specify a branch to display"
                             " e.g. branch=\'ads\'")
    if branch not in _BRANCH_TYPES:
        raise GraphingError(
            "The supplied branch type is not valid."
            f"Viable types are {_BRANCH_TYPES}"
        )
    ads, des = _BRANCH_TYPES[branch]

    # Ensure iterable
    y1_line_style = y1_line_style if y1_line_style else {}
    y2_line_style = y2_line_style if y2_line_style else {}
    lgd_keys = lgd_keys if lgd_keys else []

    # Pack other parameters
    data_params = dict(
        x_data=x_data,
        y1_data=y1_data,
        y2_data=y2_data,
        x_points=x_points,
        y1_points=y1_points,
    )
    unit_params = dict(
        pressure_mode=pressure_mode if pressure_mode else isotherms[0].pressure_mode,
        pressure_unit=pressure_unit if pressure_unit else isotherms[0].pressure_unit,
        loading_basis=loading_basis if loading_basis else isotherms[0].loading_basis,
        loading_unit=loading_unit if loading_unit else isotherms[0].loading_unit,
        material_basis=material_basis if material_basis else isotherms[0].material_basis,
        material_unit=material_unit if material_unit else isotherms[0].material_unit,
    )
    range_params = dict(
        x_range=x_range,
        y1_range=y1_range,
        y2_range=y2_range,
        x_points=x_points,
        y1_points=y1_points
    )
    log_params = dict(
        logx=logx,
        logy1=logy1,
        logy2=logy2,
    )

    #######################################
    #
    # Settings and graph generation

    #
    # Generate or assign the figure and the axes
    if ax:
        ax1 = ax
        fig = ax1.get_figure()
    else:
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

    # Create second axes object, populate it if required
    ax2 = ax1.twinx() if y2_data else None

    # Get a cycling style for the graph
    #
    # Color styling
    y1_colors = _get_colors(color, Y1_COLORS)
    y2_colors = _get_colors(color, Y2_COLORS)
    y1_color_cy = cycler('color', y1_colors)
    y2_color_cy = cycler('color', y2_colors)
    #
    # Marker styling
    markers = _get_markers(marker)
    y1_marker_cy = cycler('marker', markers)
    y2_marker_cy = cycler('marker', markers[::-1])
    #
    # Combine cycles
    cycle_compose = True if marker else False
    pc_y1 = _cycle_compose(y1_marker_cy, y1_color_cy, cycle_compose)
    pc_y2 = _cycle_compose(y2_marker_cy, y2_color_cy, cycle_compose)

    # Labels
    ax1.set_xlabel(label_units_dict(x_data, unit_params))
    ax1.set_ylabel(label_units_dict(y1_data, unit_params))
    if y2_data:
        ax2.set_ylabel(label_units_dict(y2_data, unit_params))

    #####################################
    #
    # Actual plotting
    #
    # Plot the data
    for isotherm in isotherms:

        # Line styles for the current isotherm
        y1_ls = next(pc_y1)
        y2_ls = next(pc_y2)
        y1_ls.update(y1_line_style)
        y2_ls.update(y2_line_style)

        # If there's an adsorption branch, plot it
        iso_has_ads = isotherm.has_branch('ads')
        iso_has_des = isotherm.has_branch('des')
        if ads and iso_has_ads:
            # Points
            x1_p, y1_p, x2_p, y2_p = _get_data(
                isotherm,
                'ads',
                data_params=data_params,
                unit_params=unit_params,
                range_params=range_params,
            )
            # Plot line 1
            y1_lbl = label_lgd(isotherm, lgd_keys, 'ads', y1_data)
            ax1.plot(x1_p, y1_p, label=y1_lbl, **y1_ls)

            # Plot line 2
            if y2_data and y2_p is not None:
                y2_lbl = label_lgd(isotherm, lgd_keys, 'ads', y2_data)
                ax2.plot(x2_p, y2_p, label=y2_lbl, **y2_ls)

        # Switch to desorption linestyle (dotted, white marker)
        y1_ls['markerfacecolor'] = 'white'
        y1_ls['linestyle'] = '--'
        y2_ls['markerfacecolor'] = 'white'

        # If there's a desorption branch, plot it
        if des and iso_has_des:
            # Points
            x1_p, y1_p, x2_p, y2_p = _get_data(
                isotherm,
                'des',
                data_params=data_params,
                unit_params=unit_params,
                range_params=range_params,
            )
            # Plot line 1
            if branch == 'all' and 'branch' not in lgd_keys and iso_has_ads:
                y1_lbl = ''
            else:
                y1_lbl = label_lgd(isotherm, lgd_keys, 'des', y1_data)
            ax1.plot(x1_p, y1_p, label=y1_lbl, **y1_ls)

            # Plot line 2
            if y2_data and y2_p is not None:
                if branch == 'all' and 'branch' not in lgd_keys and iso_has_ads:
                    y2_lbl = ''
                else:
                    y2_lbl = label_lgd(isotherm, lgd_keys, 'des', y2_data)
                ax2.plot(x2_p, y2_p, label=y2_lbl, **y2_ls)

    #####################################
    #
    # Final settings

    _final_styling(
        fig,
        ax1,
        ax2,
        log_params,
        range_params,
        lgd_pos,
        save_path,
    )

    if ax2:
        return (ax1, ax2)
    return ax1


def _get_keys(iso):
    return ['loading', 'pressure'] + iso.other_keys


def _get_colors(color, palette):
    if color:
        if isinstance(color, bool):
            return palette
        if isinstance(color, int):
            ncol = len(palette) if color > len(palette) else color
            return palette[:ncol]
        if isinstance(color, abc.Iterable):
            return color
        raise ParameterError("Unknown ``color`` parameter type.")
    return ['black', 'grey', 'silver']


def _get_markers(marker):
    if marker:
        if isinstance(marker, bool):
            return ISO_MARKERS
        if isinstance(marker, int):
            nmark = len(ISO_MARKERS) if marker > len(ISO_MARKERS) else marker
            return ISO_MARKERS[:nmark]
        if isinstance(marker, abc.Iterable):
            return marker
        raise ParameterError("Unknown ``marker`` parameter type.")
    return []


def _cycle_compose(cy_1, cy_2, cycle_compose):
    if cycle_compose:
        return cycle(cy_1 * cy_2)

    l_1 = len(cy_1)
    l_2 = len(cy_2)
    if l_1 == 0:
        return cycle(cy_2)
    if l_2 == 0:
        return cycle(cy_1)
    if l_1 > l_2:
        return cycle(cy_1 + (cy_2 * math.ceil(l_1 / l_2))[:l_1])
    return cycle(cy_2 + (cy_1 * math.ceil(l_2 / l_1))[:l_2])


def _get_data(
    isotherm,
    branch,
    data_params,
    unit_params,
    range_params,
):
    """Plot the y1 data and y2 data of each branch."""

    if data_params['x_points'] is None and data_params['y1_points'] is None:

        # Data X
        x1_p = _get_data_column(
            isotherm=isotherm,
            data_name=data_params['x_data'],
            branch=branch,
            unit_params=unit_params,
            data_range=range_params['x_range'],
        )
        # Data line 1
        y1_p = _get_data_column(
            isotherm=isotherm,
            data_name=data_params['y1_data'],
            branch=branch,
            unit_params=unit_params,
            data_range=range_params['y1_range'],
        )
        x1_p, y1_p = x1_p.align(y1_p, join='inner')
        # Data line 2
        x2_p = None
        y2_p = None
        if data_params['y2_data'] and data_params['y2_data'] in _get_keys(isotherm):

            y2_p = _get_data_column(
                isotherm,
                data_name=data_params['y2_data'],
                branch=branch,
                unit_params=unit_params,
                data_range=range_params['y2_range'],
            )
            x2_p, y2_p = x1_p.align(y2_p, join='inner')

    else:
        if data_params['x_points'] is not None:
            x1_p = data_params['x_points']
            y1_p = _get_data_column(
                isotherm=isotherm,
                data_name=data_params['y1_data'],
                branch=branch,
                unit_params=unit_params,
                data_range=range_params['y1_range'],
                data_points=data_params['x_points'],
            )
        elif data_params['y1_points'] is not None:
            x1_p = _get_data_column(
                isotherm=isotherm,
                data_name=data_params['x_data'],
                branch=branch,
                unit_params=unit_params,
                data_range=range_params['x_range'],
                data_points=data_params['y1_points'],
            )
            y1_p = data_params['y1_points']
        x2_p = None
        y2_p = None

    return x1_p, y1_p, x2_p, y2_p


def _get_data_column(
    isotherm,
    data_name,
    branch,
    unit_params,
    data_range=None,
    data_points=None,
):
    """Get different data from an isotherm."""
    caller_dict = {'branch': branch}

    if data_name == 'pressure':
        caller_dict['pressure_mode'] = unit_params['pressure_mode']
        caller_dict['pressure_unit'] = unit_params['pressure_unit']
        if data_points is not None:
            return isotherm.pressure_at(data_points, **caller_dict)
        return isotherm.pressure(limits=data_range, indexed=True, **caller_dict)

    if data_name == 'loading':
        caller_dict['loading_basis'] = unit_params['loading_basis']
        caller_dict['loading_unit'] = unit_params['loading_unit']
        caller_dict['material_basis'] = unit_params['material_basis']
        caller_dict['material_unit'] = unit_params['material_unit']
        if data_points is not None:
            return isotherm.loading_at(data_points, **caller_dict)
        return isotherm.loading(limits=data_range, indexed=True, **caller_dict)

    return isotherm.other_data(data_name, limits=data_range, indexed=True, **caller_dict)


def _final_styling(
    fig,
    ax1,
    ax2,
    log_params,
    range_params,
    lgd_pos,
    save_path,
):
    """Axes scales and limits, legend and graph saving."""
    # Convert the axes into logarithmic if required
    if log_params['logx']:
        ax1.set_xscale('log')
    if log_params['logy1']:
        ax1.set_yscale('log')
    if ax2 and log_params['logy2']:
        ax2.set_yscale('log')

    # Axes range settings
    ax1.set_xlim(range_params['x_range'])
    ax1.set_ylim(range_params['y1_range'])
    if ax2:
        ax2.set_ylim(range_params['y2_range'])

    # Add the legend
    bbox_extra_artists = []
    if lgd_pos is not None:
        # Get handles and combine them
        lines, labels = ax1.get_legend_handles_labels()
        if ax2:
            lines2, labels2 = ax2.get_legend_handles_labels()
            lines = lines + lines2
            labels = labels + labels2
        # Add the option for a large figure legend
        if lgd_pos in ['out left', 'out right', 'out bottom', 'out top']:
            lgd_style = {'bbox_transform': fig.transFigure}
            if lgd_pos == 'out top':
                lgd_style['bbox_to_anchor'] = (0.5, 1)
                lgd_style['loc'] = 'lower center'
                lgd_style['ncol'] = 2
            elif lgd_pos == 'out bottom':
                lgd_style['bbox_to_anchor'] = (0.5, 0)
                lgd_style['loc'] = 'upper center'
                lgd_style['ncol'] = 2
            elif lgd_pos == 'out right':
                lgd_style = {}
                lgd_style['bbox_to_anchor'] = (1, 0.5)
                lgd_style['loc'] = 'center left'
            elif lgd_pos == 'out left':
                lgd_style = {}
                lgd_style['bbox_to_anchor'] = (0, 0.5)
                lgd_style['loc'] = 'center right'
            lgd = fig.legend(lines, labels, **lgd_style)
        else:
            lgd = ax1.legend(lines, labels, loc=lgd_pos)
        bbox_extra_artists.append(lgd)

    # Fix size of graphs
    fig.tight_layout()

    # Save if desired
    if save_path:
        fig.savefig(
            save_path,
            bbox_extra_artists=bbox_extra_artists,
            bbox_inches='tight',
            dpi=300,
        )
