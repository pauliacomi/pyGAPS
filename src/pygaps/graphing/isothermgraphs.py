"""
This module contains the functions for plotting and comparing isotherms.
"""

import collections

import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import cm
from numpy import linspace
import warnings

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

             figsize=(8, 8),
             x_range=(None, None),
             y1_range=(None, None),
             y2_range=(None, None),

             fig_title=None,
             legend_list=None,
             legend_force=None,

             save_path=None,
             **other_parameters):
    """
    Plots the isotherm(s) provided on a single graph.

    Parameters
    ----------
    isotherms : PointIsotherms or list of Pointisotherms
        An isotherm or iterable of isotherms to be plotted.
    plot_type : {'isotherm', 'property', 'combined'}
        The plot type, to display: isotherm, a property or a combination.
        The 'isotherm' graph type displays only isotherm data and is the standard.
        If other data is recorded in the isotherm object, such as enthalpy, it
        can be displayed at the same time as the isotherm or in a property v
        loading graph by selecting one of the other graph types.
    secondary_key : 'str'
        The key which has the column with the supplementary data to be plotted.
        This parameter is only required in the 'property' and 'combined' graphs.
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

    figsize : tuple
        Size of figure to be passed to matplotlib.figure. eg: (0, 1).
    x_range : tuple
        Range for data on the x axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    y1_range : tuple
        Range for data on the regular y axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.
    y2_range : tuple
        Range for data on the secondary y axis. eg: (0, 1). Is applied to each
        isotherm, in the unit/mode/basis requested.

    legend_list : iterable
        The components of the isotherm which are displayed on the legend. For example
        pass ['sample_batch', 'adsorbate'] to have the legend labels display only these
        two components. Defaults to the sample name and adsorbate.
    fig_title : str
        Title of the graph. Defaults to type of graph.
    legend_force : ['none', 'bottom', 'right', 'inner']
        Specify to have the legend forced to the bottom, the right of the graph
        or inside the plot area itself.

    save_path : str, optional
        Whether to save the graph or not.
        If a path is provided, then that is where the graph will be saved.

    Other Parameters
    ----------------
    title_style : dict
        A dictionary that will be passed into the matplotlib set_title() function.

    label_style : dict
        A dictionary that will be passed into the matplotlib set_label() function.

    line_style : dict
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
        Ax object for primary graph.
    axes2 : Matplotlib ax
        Ax object for secondary graph.

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
    axes2 = None

#######################################
#
# Settings and graph generation
    #
    # Generate the graph itself
    fig = plt.figure(figsize=figsize)
    axes = plt.subplot(111)
    if y2_data:
        axes2 = axes.twinx()

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

    # Set the colours of the graph
    cy1 = cycler('marker', ['o', 's'])
    cy2 = cycler('marker', ['v', '^'])
    cy4 = cycler('marker', ['v', '^', '<', '>'])

    if color:
        number_of_lines = 7
        if not isinstance(color, bool):
            number_of_lines = color

        if isinstance(color, int):
            colors = [cm.jet(x) for x in linspace(0, 1, number_of_lines)]

        if isinstance(color, list):
            colors = color

        polychrome_cy = cycler('color', colors)
        pc_primary = (cy1 * polychrome_cy)
        pc_secondary = (cy2 * polychrome_cy)
    else:
        monochrome_cy = cycler('color', ['black', 'grey', 'silver'])
        linestyle_cy = cycler('linestyle', ['-', '--', ':', '-.'])
        pc_primary = (cy1 * linestyle_cy * monochrome_cy)
        pc_secondary = (cy4 * linestyle_cy * monochrome_cy)

    # Set the colours and ranges for the axes
    axes.set_prop_cycle(pc_primary)
    if y2_data:
        axes2.set_prop_cycle(pc_secondary)

    # Styles in the graph
    styles = dict(title_style=dict(horizontalalignment='center',
                                   fontsize=25, fontdict={'family': 'monospace'}),
                  label_style=dict(horizontalalignment='center',
                                   fontsize=20, fontdict={'family': 'monospace'}),
                  line_style=dict(linewidth=2, markersize=8),
                  line_style_sec=dict(linewidth=0, markersize=8),
                  tick_style=dict(labelsize=17),
                  legend_style=dict(handlelength=3, fontsize=15, loc='best'),
                  save_style=dict(),
                  )

    # Update with any user provided styles
    for st in ['title_style', 'label_style', 'line_style',
               'line_style_sec', 'tick_style', 'save_style']:
        new_st = other_parameters.get(st)
        if new_st:
            styles[st].update(new_st)

    # Put grid on plot
    axes.grid(True, zorder=5)

    # Graph title
    if fig_title is None:
        fig_title = ''
    axes.set_title(fig_title, **styles['title_style'])

    # Graph legend builder
    def build_label(lbl_components, isotherm):
        """
        Builds a label for the legend depending on requested parameters
        """
        if lbl_components is None:
            return isotherm.sample_name + ' ' + convert_chemformula(isotherm.adsorbate)
        else:
            text = []
            for selected in lbl_components:
                if selected == 'branch':
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
# Individual graphing functions
    #

    def graph(ax, data_x, data_y, line_label, text, tick, label, line):
        "Plot a graph, regular or logx"

        # Labels and ticks
        ax.set_xlabel(text_xaxis, **label)
        ax.set_ylabel(text, **label)
        ax.tick_params(axis='both', which='major', **tick)

        # Plot line
        line, = ax.plot(data_x, data_y, label=line_label, **line)

        return line

    def get_data(isotherm, data_name, data_range):
        if data_name == 'pressure':
            data = isotherm.pressure(
                branch=plot_branch,
                pressure_unit=pressure_unit,
                pressure_mode=pressure_mode,
                min_range=data_range[0],
                max_range=data_range[1],
                indexed=True,
            )
        elif data_name == 'loading':
            data = isotherm.loading(
                branch=plot_branch,
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
                branch=plot_branch,
                min_range=data_range[0],
                max_range=data_range[1],
                indexed=True,
            )
        return data

    def graph_caller(axes, axes2, isotherm, plot_branch, label):
        """
        Convenience function to call other graphing functions
        """

        line = None

        x_p, y_p = get_data(isotherm, x_data, x_range).align(
            get_data(isotherm, y1_data, y1_range), join='inner')
        line = graph(axes, x_p, y_p,
                     label, text_yaxis,
                     styles['tick_style'],
                     styles['label_style'],
                     styles['line_style']
                     )

        if y2_data and y2_data in keys(isotherm):
            x_p, y2_p = get_data(isotherm, x_data, x_range).align(
                get_data(isotherm, y2_data, y2_range), join='inner')
            graph(axes2, x_p, y2_p,
                  label, text_y2axis,
                  styles['tick_style'],
                  styles['label_style'],
                  styles['line_style_sec']
                  )

        return line

#####################################
#
# Actual plotting
    #
    # Plot the data
    for isotherm in isotherms:

        # First build the label of the isotherm for the legend
        line_label = build_label(legend_list, isotherm)

        # Colour of the line, now empty
        line_color = None

        # If there's an adsorption branch, plot it
        if ads:
            plot_branch = 'ads'
            if isotherm.has_branch(branch=plot_branch):

                # Label the branch
                lbl = line_label
                if legend_list is not None and 'branch' in legend_list:
                    lbl += ' ads'

                # Call the plotting function
                line = graph_caller(axes, axes2,
                                    isotherm, plot_branch, lbl)

                line_color = line.get_color()

        if des:
            plot_branch = 'des'
            if isotherm.has_branch(branch=plot_branch):

                # Label the branch
                if branch == 'all-nol':
                    lbl = ''
                else:
                    lbl = line_label
                    if legend_list is not None and 'branch' in legend_list:
                        lbl += ' des'

                # Set marker fill to empty, and match the colour from desorption
                styles['line_style']['mfc'] = 'none'
                if line_color is not None:
                    styles['line_style']['c'] = line_color
                    styles['line_style']['linestyle'] = '--'

                # Call the plotting function
                line = graph_caller(axes, axes2,
                                    isotherm, plot_branch, lbl)

                # Delete the colour changes to go back to original settings
                del styles['line_style']['mfc']
                if line_color is not None:
                    del styles['line_style']['c']
                    del styles['line_style']['linestyle']


#####################################
#
# Final settings
    #
    # Convert the axes into logarithmic if required
    if logx:
        axes.set_xscale('log')
    else:
        axes.set_xscale('linear')
        axes.set_xlim(xmin=0)

    axes.set_xlim(x_range)
    axes.set_ylim(y1_range)
    if axes2:
        axes2.set_ylim(y2_range)

    # Add the legend
    lines, labels = axes.get_legend_handles_labels()
    if y2_data:
        lines2, labels2 = axes2.get_legend_handles_labels()
        lines = lines + lines2
        labels = labels + labels2

    if legend_force == 'inner':
        pass
    elif legend_force == 'bottom':
        styles['legend_style']['bbox_to_anchor'] = (0.5, -0.1)
        styles['legend_style']['loc'] = 'lower center'
        styles['legend_style']['bbox_transform'] = fig.transFigure
        styles['legend_style']['ncol'] = 2
    elif legend_force == 'right' or len(lines) > 5:
        styles['legend_style']['bbox_to_anchor'] = (1.3, 0.5)
        styles['legend_style']['loc'] = 'center right'

    # Update with any user provided styles
    new_st = other_parameters.get('legend_style')
    if new_st:
        styles['legend_style'].update(new_st)

    lgd = None

    if legend_force == 'none':
        pass
    elif legend_force == 'inner':
        lgd = axes.legend(lines, labels, **styles['legend_style'])
    elif legend_force == 'bottom':
        lgd = fig.legend(lines, labels, **styles['legend_style'])
    elif legend_force == 'right' or len(lines) > 5:
        lgd = fig.legend(lines, labels, **styles['legend_style'])
    else:
        lgd = axes.legend(lines, labels, **styles['legend_style'])

    bbox_extra_artists = []
    if lgd:
        bbox_extra_artists.append(lgd)

    # Fix size of graphs
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path,
                    bbox_extra_artists=bbox_extra_artists,
                    bbox_inches='tight',
                    **styles['save_style'],
                    )

    return fig, axes, axes2
