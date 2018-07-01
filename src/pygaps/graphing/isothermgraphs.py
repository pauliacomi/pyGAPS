"""
This module contains the functions for plotting and comparing isotherms.
"""

import collections

import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import cm
from numpy import linspace

from ..utilities.exceptions import GraphingError
from ..utilities.exceptions import ParameterError
from ..utilities.string_utilities import convert_chemformula

# ! list of plot types
_PLOT_TYPES = ("isotherm", "property", "combined")

# ! list of branch types
_BRANCH_TYPES = ("ads", "des")


def plot_iso(isotherms,
             plot_type='isotherm', secondary_key=None,
             branch=_BRANCH_TYPES, logx=False, color=True,

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
    branch : list
        List with branches to disply, options: 'ads', 'des'.
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
    legend_force : ['bottom', 'right']
        Specify to have the legend forced to the bottom or the right of the graph.

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
    if plot_type is None:
        raise ParameterError("Specify a plot type to graph"
                             " e.g. plot_type=\'isotherm\'")
    if plot_type not in _PLOT_TYPES:
        raise ParameterError("Plot type {0} not an option. Viable plot"
                             "types are {1}".format(plot_type, _PLOT_TYPES))
    if plot_type == 'property' or plot_type == 'combined':
        if secondary_key is None:
            raise ParameterError("No secondary_key parameter specified")
        if all(secondary_key not in isotherm.other_keys for isotherm in isotherms):
            raise GraphingError(
                "None of the isotherms supplied have {} data".format(secondary_key))

    # Store which branches will be displayed
    if branch is None:
        raise ParameterError("Specify a branch to display"
                             " e.g. branch=\'ads\'")
    if not [i for i in branch if i in _BRANCH_TYPES]:
        raise GraphingError("One of the supplied branch types is not valid."
                            "Viable types are {}".format(_BRANCH_TYPES))

    ads = False
    des = False
    if 'ads' in branch:
        ads = True
    if 'des' in branch:
        des = True

    # Create empty axes object
    axes2 = None

    # Add limits for data x and y
    range_pressure = None
    range_property = None
    range_loading = None

#######################################
#
# Settings and graph generation
    #
    # Generate the graph itself
    fig = plt.figure(figsize=figsize)
    axes = plt.subplot(111)
    if plot_type == 'combined':
        axes2 = axes.twinx()

    # Build the name of the axes
    text_xaxis = r'Pressure'
    text_yaxis = r'Loading'
    if secondary_key == 'enthalpy':
        text_y2axis = r'Enthalpy of adsorption $(-kJ\/mol^{-1})$'
    else:
        text_y2axis = secondary_key
    if pressure_mode == "absolute":
        text_xaxis = text_xaxis + ' ($' + pressure_unit + '$)'
    elif pressure_mode == "relative":
        text_xaxis = "Relative " + text_xaxis
    text_yaxis = text_yaxis + \
        ' ($' + loading_unit + '/' + adsorbent_unit + '$)'

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
        pc_iso = (cy1 * polychrome_cy)
        pc_prop = (cy2 * polychrome_cy)
    else:
        monochrome_cy = cycler('color', ['black', 'grey', 'silver'])
        linestyle_cy = cycler('linestyle', ['-', '--', ':', '-.'])
        pc_iso = (cy1 * linestyle_cy * monochrome_cy)
        pc_prop = (cy4 * linestyle_cy * monochrome_cy)

    # Set the colours and ranges for the axes
    if plot_type == 'isotherm':
        axes.set_prop_cycle(pc_iso)
        range_pressure = x_range
        range_loading = y1_range
        range_property = (None, None)
    elif plot_type == 'property':
        axes.set_prop_cycle(pc_prop)
        range_pressure = (None, None)
        range_loading = x_range
        range_property = y1_range
    elif plot_type == 'combined':
        axes.set_prop_cycle(pc_iso)
        axes2.set_prop_cycle(pc_prop)
        range_pressure = x_range
        range_loading = y1_range
        range_property = y2_range

    # Styles in the graph
    styles = dict(title_style=dict(horizontalalignment='center',
                                   fontsize=25, fontdict={'family': 'monospace'}),
                  label_style=dict(horizontalalignment='center',
                                   fontsize=20, fontdict={'family': 'monospace'}),
                  line_style=dict(linewidth=2, markersize=8),
                  tick_style=dict(labelsize=17),
                  legend_style=dict(handlelength=3, fontsize=15, loc='best'),
                  save_style=dict(),
                  )

    # Update with any user provided styles
    for st in ['title_style', 'label_style', 'line_style', 'tick_style', 'save_style']:
        new_st = other_parameters.get(st)
        if new_st:
            styles[st].update(new_st)

    # Put grid on plot
    axes.grid(True, zorder=5)

    # Graph title
    if fig_title is None:
        fig_title = plot_type.capitalize() + ' Graph'
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

    def isotherm_graph(axes, data_x, data_y, line_label, styles_dict):
        "Plot an isotherm graph, regular or logx"

        # Labels and ticks
        axes.set_xlabel(text_xaxis, **styles_dict['label_style'])
        axes.set_ylabel(text_yaxis, **styles_dict['label_style'])
        axes.tick_params(axis='both', which='major',
                         **styles_dict['tick_style'])

        # Plot line
        line, = axes.plot(data_x, data_y, label=line_label,
                          **styles_dict['line_style'])

        return line

    def property_graph(axes, data_x, data_y, line_label, styles_dict):
        "Plot an property graph versus amount adsorbed"

        # Labels and ticks
        axes.set_xlabel(text_yaxis, **styles_dict['label_style'])
        axes.set_ylabel(text_y2axis, **styles_dict['label_style'])
        axes.tick_params(axis='both', which='major',
                         **styles_dict['tick_style'])
        axes.set_ymargin(1)

        # Generate a linestyle from the incoming dictionary
        specific_line_style = styles_dict['line_style'].copy()
        specific_line_style.update(dict(linewidth=0))

        # Plot line
        line, = axes.plot(data_x, data_y, label=line_label,
                          **specific_line_style)

        return line

    def graph_caller(axes, axes2, isotherm, plot_branch, label, pl_type, styles):
        """
        Convenience function to call other graphing functions
        """

        line = None

        # Get the data from the isotherm
        def pressure():
            return isotherm.pressure(
                branch=plot_branch,
                pressure_unit=pressure_unit,
                pressure_mode=pressure_mode,
                min_range=range_pressure[0],
                max_range=range_pressure[1],
                indexed=True,
            )

        def loading():
            return isotherm.loading(
                branch=plot_branch,
                loading_unit=loading_unit,
                loading_basis=loading_basis,
                adsorbent_unit=adsorbent_unit,
                adsorbent_basis=adsorbent_basis,
                min_range=range_loading[0],
                max_range=range_loading[1],
                indexed=True,
            )

        def secondary_prop():
            return isotherm.other_data(
                secondary_key,
                branch=plot_branch,
                min_range=range_property[0],
                max_range=range_property[1],
                indexed=True,
            )

        if pl_type == 'isotherm':
            p_points, l_points = pressure().align(loading(), join='inner')
            line = isotherm_graph(axes,
                                  p_points,
                                  l_points,
                                  label, styles_dict=styles)

        elif pl_type == 'property':
            l_points, o_points = loading().align(secondary_prop(), join='inner')
            line = property_graph(axes,
                                  l_points,
                                  o_points,
                                  label, styles_dict=styles)

        elif pl_type == 'combined':
            p_points, l_points = pressure().align(loading(), join='inner')
            line = isotherm_graph(axes,
                                  p_points,
                                  l_points,
                                  label, styles_dict=styles)

            if secondary_prop is not None and secondary_key in isotherm.other_keys:
                p_points, o_points = pressure().align(secondary_prop(), join='inner')
                property_graph(axes2,
                               p_points,
                               o_points,
                               label, styles_dict=styles)
            else:
                pass

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
                                    isotherm, plot_branch,
                                    lbl, plot_type, styles)

                line_color = line.get_color()

        if des:
            plot_branch = 'des'
            if isotherm.has_branch(branch=plot_branch):

                # Label the branch
                lbl = line_label
                if legend_list is not None and 'branch' in legend_list:
                    lbl += ' des'

                # Set marker fill to empty, and match the colour from desorption
                styles['line_style']['mfc'] = 'none'
                if line_color is not None:
                    styles['line_style']['c'] = line_color

                # Call the plotting function
                line = graph_caller(axes, axes2,
                                    isotherm, plot_branch,
                                    lbl, plot_type, styles)

                # Delete the colour changes to go back to original settings
                del styles['line_style']['mfc']
                if line_color is not None:
                    del styles['line_style']['c']


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
    if plot_type == 'combined':
        lines2, labels2 = axes2.get_legend_handles_labels()
        lines = lines + lines2
        labels = labels + labels2

    if legend_force == 'bottom':
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

    if legend_force == 'right' or len(lines) > 4:
        lgd = fig.legend(lines, labels, **styles['legend_style'])
    else:
        lgd = axes.legend(lines, labels, **styles['legend_style'])

    # Fix size of graphs
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path,
                    bbox_extra_artists=[lgd],
                    bbox_inches='tight',
                    **styles['save_style'],
                    )

    return fig, axes, axes2
