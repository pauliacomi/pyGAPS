"""
This module contains the functions for plotting and comparing isotherms.
"""

import collections
import warnings
from itertools import cycle

import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import cm
from numpy import linspace

from ..utilities.exceptions import GraphingError
from ..utilities.exceptions import ParameterError
from ..utilities.string_utilities import convert_chemformula

# ! list of branch types
_BRANCH_TYPES = ("ads", "des", "all", "all-nol")


def plot_iso(isotherms,
             x_data='pressure',
             y1_data='loading',
             y2_data=None,

             branch="all", logx=False, color=True,

             adsorbent_basis="mass",
             adsorbent_unit="g",
             loading_basis="molar",
             loading_unit="mmol",
             pressure_mode="absolute",
             pressure_unit="bar",

             x_range=(None, None),
             y1_range=(None, None),
             y2_range=(None, None),

             fig_title=None,
             lgd_keys=None,
             lgd_pos='best',

             save_path=None,
             **other_parameters):
    """
    Plots the isotherm(s) provided on a single graph.

    Parameters
    ----------
    isotherms : PointIsotherms or list of Pointisotherms
        An isotherm or iterable of isotherms to be plotted.

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
    color : bool, optional
        Whether the graph should be coloured or grayscale. Grayscale graphs
        are usually preferred for publications or print media.

    adsorbent_basis : str, optional
        Whether the adsorption is read in terms of either 'per volume'
        or 'per mass'.
    adsorbent_unit : str, optional
        Unit of loading.
    loading_basis : str, optional
        Loading basis.
    loading_unit : str, optional
        Unit of loading.
    pressure_mode : str, optional
        The pressure mode, either absolute pressures or relative in
        the form of p/p0.
    pressure_unit : str, optional
        Unit of pressure.

    x_range : tuple
        Range for data on the x axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    y1_range : tuple
        Range for data on the regular y axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    y2_range : tuple
        Range for data on the secondary y axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.

    fig_title : str
        Title of the graph. Defaults to none.
    lgd_keys : iterable
        The components of the isotherm which are displayed on the legend. For example
        pass ['sample_name', 'sample_batch'] to have the legend labels display only these
        two components. Works with any isotherm properties and with 'branch' and 'key',
        the isotherm branch and the y-axis key respectively.
        Defaults to 'sample_name' and 'adsorbate'.
    lgd_pos : ['best', 'none', 'bottom', 'right', 'inner']
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

    tick_style : dict
        A dictionary that will be passed into the matplotlib tick_params() function.

    legend_style : dict
        A dictionary that will be passed into the matplotlib legend() function.

    save_style : dict
        A dictionary that will be passed into the matplotlib savefig() function
        if the saving of the figure is selected.

    Returns
    -------
    fig : Matplotlib figure
        The figure object generated.
    axes1 : Matplotlib ax
        Ax object for left y1 axis.
    axes2 : Matplotlib ax
        Ax object for right y2 axis (if applicable).

    """
#######################################
#
# Initial checks
    # Make iterable if not already
    if not isinstance(isotherms, collections.Iterable):
        isotherms = [isotherms]

    # Check for plot type validity
    if None in [x_data, y1_data]:
        raise ParameterError("Specify a plot type to graph"
                             " e.g. x_data=\'loading\', y1_data=\'pressure\'")

    # Check if required keys are present in isotherms
    def keys(iso):
        ks = ['loading', 'pressure']
        ks.extend(getattr(iso, 'other_keys', []))
        return ks

    if any(x_data not in keys(isotherm) for isotherm in isotherms):
        raise GraphingError(
            "None of the isotherms supplied have {} data".format(x_data))

    if any(y1_data not in keys(isotherm) for isotherm in isotherms):
        raise GraphingError(
            "None of the isotherms supplied have {} data".format(y1_data))

    if y2_data is not None:
        if all(y2_data not in keys(isotherm) for isotherm in isotherms):
            raise GraphingError(
                "None of the isotherms supplied have {} data".format(y2_data))
        elif any(y2_data not in keys(isotherm) for isotherm in isotherms):
            warnings.warn('Some isotherms do not have {} data'.format(y2_data))

    # Store which branches will be displayed
    if branch is None:
        raise ParameterError("Specify a branch to display"
                             " e.g. branch=\'ads\'")
    if branch not in _BRANCH_TYPES:
        raise GraphingError("The supplied branch type is not valid."
                            "Viable types are {}".format(_BRANCH_TYPES))

    ads = False
    des = False
    if branch == 'ads':
        ads = True
    elif branch == 'des':
        des = True
    else:
        ads = True
        des = True

    # Create empty axes object
    ax2 = None

#######################################
#
# Settings and graph generation

    # Create style dictionaries and get user defined ones
    styles = {
        'fig_style': {'figsize': (8, 8)},
        'title_style': {
            'horizontalalignment': 'center',
            'fontsize': 25,
            'fontdict': {'family': 'monospace'}
        },
        'label_style': {
            'horizontalalignment': 'center',
            'fontsize': 20,
            'fontdict': {'family': 'monospace'},
        },
        'y1_line_style': {'linewidth': 2, 'markersize': 8},
        'y2_line_style': {'linewidth': 0, 'markersize': 8},
        'tick_style': {'labelsize': 17},
        'legend_style': {'handlelength': 3, 'fontsize': 15},
        'save_style': {},
    }

    # Overwrite with any user provided styles
    for style in styles:
        new_style = other_parameters.get(style)
        if new_style:
            styles[style].update(new_style)

    #
    # Generate the graph itself
    fig = plt.figure(**styles['fig_style'])
    ax1 = plt.subplot(111)
    if y2_data:
        ax2 = ax1.twinx()

    # Build the name of the axes
    def get_name(key):
        if key == 'pressure':
            if pressure_mode == "absolute":
                text = 'Pressure ($' + pressure_unit + '$)'
            elif pressure_mode == "relative":
                text = "Relative pressure"
        elif key == 'loading':
            text = 'Loading ($' + loading_unit + '/' + adsorbent_unit + '$)'
        elif key == 'enthalpy':
            text = r'Enthalpy of adsorption $(-kJ\/mol^{-1})$'
        else:
            text = key
        return text

    text_xaxis = get_name(x_data)
    text_yaxis = get_name(y1_data)
    if y2_data:
        text_y2axis = get_name(y2_data)

    # Get a cycling style for the graph
    if color:
        number_of_lines = 7
        if not isinstance(color, bool):
            number_of_lines = color

        if isinstance(color, int):
            colors = [cm.jet(x) for x in linspace(0, 1, number_of_lines)]

        if isinstance(color, list):
            colors = color

        polychrome_cy = cycler('color', colors)
        y1_marker_cy = cycler('marker', ['o', 's'])
        y2_marker_cy = cycler('marker', ['v', '^'])

        pc_primary = cycle(y1_marker_cy * polychrome_cy)
        pc_secondary = cycle(y2_marker_cy * polychrome_cy)
    else:
        y1_marker_cy = cycler('marker', ['o', 's'])
        y2_marker_cy = cycler('marker', ['v', '^', '<', '>'])
        monochrome_cy = cycler('color', ['black', 'grey', 'silver'])

        pc_primary = cycle(y1_marker_cy * monochrome_cy)
        pc_secondary = cycle(y2_marker_cy * monochrome_cy)

    # Put grid on plot
    ax1.grid(True, zorder=5)

    # Graph title
    if fig_title is None:
        fig_title = ''
    ax1.set_title(fig_title, **styles['title_style'])

    # Graph legend builder
    def build_label(isotherm, lbl_components, iso_branch, key):
        """
        Builds a label for the legend depending on requested parameters
        """
        if lbl_components is None:
            return isotherm.sample_name + ' ' + convert_chemformula(isotherm.adsorbate)
        else:
            if branch == 'all-nol' and iso_branch == 'des':
                return ''
            text = []
            for selected in lbl_components:
                if selected == 'branch':
                    text.append(iso_branch)
                    continue
                elif selected == 'key':
                    text.append(key)
                    continue
                val = getattr(isotherm, selected)
                if val:
                    if selected == 'adsorbate':
                        text.append(convert_chemformula(val))
                    else:
                        text.append(str(val))

            return " ".join(text)

###########################################
#
# Getting specific data from an isotherm
    #

    def get_data(isotherm, data_name, data_range, branch):
        if data_name == 'pressure':
            data = isotherm.pressure(
                branch=branch,
                pressure_unit=pressure_unit,
                pressure_mode=pressure_mode,
                min_range=data_range[0],
                max_range=data_range[1],
                indexed=True,
            )
        elif data_name == 'loading':
            data = isotherm.loading(
                branch=branch,
                loading_unit=loading_unit,
                loading_basis=loading_basis,
                adsorbent_unit=adsorbent_unit,
                adsorbent_basis=adsorbent_basis,
                min_range=data_range[0],
                max_range=data_range[1],
                indexed=True,
            )
        else:
            data = isotherm.other_data(
                data_name,
                branch=branch,
                min_range=data_range[0],
                max_range=data_range[1],
                indexed=True,
            )
        return data

###########################################
#
# Generic ax1/ax2 graphing function
    #

    def graph_caller(isotherm, iso_branch, y1_style, y2_style):
        """
        Convenience function to call other graphing functions
        """

        # Labels and ticks
        ax1.set_xlabel(text_xaxis, **styles['label_style'])
        ax1.set_ylabel(text_yaxis, **styles['label_style'])
        ax1.tick_params(axis='both', which='major', **styles['tick_style'])

        # Plot line 1
        label = build_label(isotherm, lgd_keys, iso_branch, y1_data)
        x_p, y_p = get_data(isotherm, x_data, x_range, iso_branch).align(
            get_data(isotherm, y1_data, y1_range, iso_branch), join='inner')
        ax1.plot(x_p, y_p, label=label, **y1_style)

        # Plot line 2 (if applicable)
        if y2_data and y2_data in keys(isotherm):
            x_p, y2_p = get_data(isotherm, x_data, x_range, iso_branch).align(
                get_data(isotherm, y2_data, y2_range, iso_branch), join='inner')

            label = build_label(isotherm, lgd_keys, iso_branch, y2_data)
            print(label)
            ax2.set_ylabel(text_y2axis, **styles['label_style'])
            ax2.tick_params(axis='both', which='major', **styles['tick_style'])
            ax2.plot(x_p, y2_p, label=label, **y2_style)


#####################################
#
# Actual plotting
    #
    # Plot the data
    for isotherm in isotherms:

        # First build the label of the isotherm for the legend

        # Line styles for the current isotherm
        y1_line_style = next(pc_primary)
        y2_line_style = next(pc_secondary)
        y1_line_style.update(styles['y1_line_style'])
        y2_line_style.update(styles['y2_line_style'])

        # If there's an adsorption branch, plot it
        if ads:
            iso_branch = 'ads'
            if isotherm.has_branch(branch=iso_branch):

                # Call the plotting function
                graph_caller(isotherm, iso_branch,
                             y1_line_style, y2_line_style)

        # Switch to desorption linestyle (dotted, open marker)
        y1_line_style['markerfacecolor'] = 'none'
        y1_line_style['linestyle'] = '--'
        y2_line_style['markerfacecolor'] = 'none'

        # If there's a desorption branch, plot it
        if des:
            iso_branch = 'des'
            if isotherm.has_branch(branch=iso_branch):

                # Call the plotting function
                graph_caller(isotherm, iso_branch,
                             y1_line_style, y2_line_style)


#####################################
#
# Final settings
    #
    # Convert the axes into logarithmic if required
    if logx:
        ax1.set_xscale('log')
    else:
        ax1.set_xscale('linear')
        ax1.set_xlim(left=0)

    ax1.set_xlim(x_range)
    ax1.set_ylim(y1_range)
    if ax2:
        ax2.set_ylim(y2_range)

    # Add the legend
    lines, labels = ax1.get_legend_handles_labels()
    if y2_data:
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines = lines + lines2
        labels = labels + labels2

    lgd = None

    if lgd_pos == 'best':
        if len(lines) > 5:
            lgd_pos = 'right'
        else:
            lgd_pos = 'inner'

    if lgd_pos == 'none':
        pass
    elif lgd_pos == 'inner':
        lgd = ax1.legend(lines, labels, **styles['legend_style'])
    elif lgd_pos == 'bottom':
        legend_style = {}
        legend_style['bbox_to_anchor'] = (0.5, 0)
        legend_style['loc'] = 'upper center'
        legend_style['bbox_transform'] = fig.transFigure
        legend_style['ncol'] = 2
        legend_style.update(styles['legend_style'])
        lgd = fig.legend(lines, labels, **legend_style)
    elif lgd_pos == 'right':
        legend_style = {}
        legend_style['bbox_to_anchor'] = (1, 0.5)
        legend_style['loc'] = 'center left'
        legend_style['bbox_transform'] = fig.transFigure
        legend_style.update(styles['legend_style'])
        lgd = fig.legend(lines, labels, **legend_style)
    elif lgd_pos == 'left':
        legend_style = {}
        legend_style['bbox_to_anchor'] = (0, 0.5)
        legend_style['loc'] = 'center right'
        legend_style['bbox_transform'] = fig.transFigure
        legend_style.update(styles['legend_style'])
        lgd = fig.legend(lines, labels, **legend_style)
    else:
        lgd = ax1.legend(lines, labels, **styles['legend_style'])

    bbox_extra_artists = []
    if lgd:
        bbox_extra_artists.append(lgd)

    # Fix size of graphs
    fig.tight_layout()

    if save_path:
        fig.savefig(
            save_path,
            bbox_extra_artists=bbox_extra_artists,
            bbox_inches='tight',
            **styles['save_style'],
        )

    return fig, ax1, ax2
