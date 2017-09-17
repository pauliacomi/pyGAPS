"""
This module contains the functions for plotting and comparing isotherms
"""

import pandas
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import cm
from numpy import linspace

from ..utilities.string_utilities import convert_chemformula
from ..utilities.exceptions import ParameterError
from ..utilities.exceptions import GraphingError

# ! list of plot types
_PLOT_TYPES = ("isotherm", "property", "combo")

# ! list of branch types
_BRANCH_TYPES = ("ads", "des")


def plot_iso(isotherms,
             plot_type='isotherm', secondary_key=None,
             branch=_BRANCH_TYPES, logx=False, color=True,

             basis_adsorbent='mass',
             mode_pressure='absolute',
             unit_pressure='bar',
             unit_loading='mmol',

             x_range=(None, None),
             y1_range=(None, None),
             y2_range=(None, None),

             legend_list=None,
             fig_title=None,
             legend_bottom=False,

             save=False, path=None,
             **other_parameters):
    """
    Plots the isotherm(s) provided on a single graph

    Parameters
    ----------
    isotherms : list
        an iterable of the isotherms to be plotted
    plot_type : {'isotherm', 'property', 'combo'}
        The plot type, to display: isotherm, a property or a combination.
        The 'isotherm' graph type displays only isotherm data and is the standard.
        If other data is recorded in the isotherm object, such as enthalpy, it
        can be displayed at the same time as the isotherm or in a property v
        loading graph by selecting one of the other graph types
    secondary_key : 'str'
        The key which has the column with the supplementary data to be plotted.
        This parameter is only required in the 'property' and 'combo' graphs
    branch : list
        List with branches to disply, options: 'ads', 'des'.
    logx : bool
        Whether the graph x axis should be logarithmic.
    color : bool, optional
        Whether the graph should be coloured or grayscale. Grayscale graphs
        are usually preffered for publications or print media.

    basis_adsorbent : str, optional
        Whether the adsorption is read in terms of either 'per volume'
        or 'per mass'.
    mode_pressure : str, optional
        The pressure mode, either absolute pressures or relative in
        the form of p/p0.
    unit_loading : str, optional
        Unit of loading
    unit_pressure : str, optional
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

    legend_list : iterable
        The components of the isotherm which are displayed on the legend. For example
        pass ['sample_batch', 'adsorbate'] to have the legend labels display only these
        two components. Defaults to the sample name and adsorbate.
    fig_title : str
        Title of the graph. Defaults to type of graph.
    legend_bottom : bool
        Specify as True to have the legend at the bottom of the graph. Alternatively,
        when plotting a lot of data, the legend is best displayed separately to the
        side of the graph. In that case, set this to False.

    save : bool, optional
        Whether to save the graph or not.
    path : str, optional
        The path where the graph will be saved.

    Returns
    -------
    """
#######################################
#
# Initial checks
    #
    # Check for plot type validity
    if plot_type is None:
        raise ParameterError("Specify a plot type to graph"
                             " e.g. plot_type=\'isotherm\'")
    if plot_type not in _PLOT_TYPES:
        raise ParameterError("Plot type {0} not an option. Viable plot"
                             "types are {1}".format(plot_type, _PLOT_TYPES))

    if plot_type == 'property' or plot_type == 'combo':
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
    # Generate the graph iself
    fig, axes = plt.subplots(1, 1, figsize=(8, 8))
    if plot_type == 'combo':
        axes2 = axes.twinx()

    # Build the name of the axes
    text_xaxis = r'Pressure'
    text_yaxis = r'Loading'
    text_y2axis = r'Enthalpy of adsorption $(-kJ\/mol^{-1})$'
    if mode_pressure == "absolute":
        text_xaxis = text_xaxis + ' ($' + unit_pressure + '$)'
    elif mode_pressure == "relative":
        text_xaxis = "Relative " + text_xaxis
    if basis_adsorbent == "mass":
        text_yaxis = text_yaxis + ' ($' + unit_loading + ' g^{-1}$)'
    elif basis_adsorbent == "volume":
        text_yaxis = text_yaxis + ' ($' + unit_loading + ' cm^{-3}$)'

    # Set the colours of the graph
    number_of_lines = 6
    cm_subsection = linspace(0, 1, number_of_lines)
    colors = [cm.jet(x) for x in cm_subsection]
    cy1 = cycler('marker', ['o', 's'])
    cy2 = cycler('marker', ['v', '^'])
    cy3 = cycler('color', colors)
    cy4 = cycler('marker', ['v', '^', '<', '>'])
    cy5 = cycler('linestyle', ['-', '--', ':', '-.'])
    cy6 = cycler('color', ['black', 'grey', 'silver'])

    if color:
        pc_iso = (cy1 * cy3)
        pc_prop = (cy2 * cy3)
    else:
        pc_iso = (cy1 * cy5 * cy6)
        pc_prop = (cy4 * cy5 * cy6)

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
    elif plot_type == 'combo':
        axes.set_prop_cycle(pc_iso)
        axes2.set_prop_cycle(pc_prop)
        range_pressure = x_range
        range_loading = y1_range
        range_property = y2_range

    # Styles in the graph
    title_style = dict(horizontalalignment='center',
                       fontsize=25, fontdict={'family': 'monospace'})
    label_style = dict(horizontalalignment='center',
                       fontsize=20, fontdict={'family': 'monospace'})
    line_style = dict(linewidth=2, markersize=4)
    tick_style = dict(labelsize=17)
    styles = dict(title_style=title_style, label_style=label_style,
                  line_style=line_style, tick_style=tick_style)

    styles.update(other_parameters)  # Update with any user provided styles

    # Put grid on plot
    axes.grid(True, zorder=5)

    # Graph title
    if fig_title is None:
        fig_title = plot_type.capitalize() + ' Graph'
    axes.set_title(fig_title, **title_style)

    # Graph legend builder
    def build_label(lbl_components, isotherm):
        """
        Builds a label for the legend depending on requested parameters
        """
        if lbl_components is None:
            return isotherm.sample_name + ' ' + convert_chemformula(isotherm.adsorbate)
        else:
            parameters = isotherm.to_dict()
            text = []
            for selected in lbl_components:
                if selected in parameters:
                    if selected == 'adsorbate':
                        text.append(convert_chemformula(
                            parameters.get(selected)))
                    else:
                        text.append(str(parameters.get(selected)))

            return " ".join(text)
###########################################
#
# Individual raphing functions
    #

    def isotherm_graph(axes, data_x, data_y, line_label, styles_dict):
        "Plot an isotherm graph, regular or logx"

        # Labels and ticks
        axes.set_xlabel(text_xaxis, **styles_dict['label_style'])
        axes.set_ylabel(text_yaxis, **styles_dict['label_style'])
        axes.tick_params(axis='both', which='major',
                         **styles_dict['tick_style'])

        # Generate a linestyle from the incoming dictionary
        line_style = styles_dict['line_style']
        specific_line_style = dict(linewidth=2, markersize=8)
        line_style.update(specific_line_style)

        # Plot line
        line, = axes.plot(data_x, data_y, label=line_label, **line_style)

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
        line_style = styles_dict['line_style']
        specific_line_style = dict(linewidth=0, markersize=8)
        line_style.update(specific_line_style)

        # Plot line
        line, = axes.plot(data_x, data_y, label=line_label, **line_style)

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
                unit=unit_pressure,
                mode=mode_pressure,
                min_range=range_pressure[0],
                max_range=range_pressure[1],
                indexed=True,
            )

        def loading():
            return isotherm.loading(
                branch=plot_branch,
                unit=unit_loading,
                basis=basis_adsorbent,
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

        elif pl_type == 'combo':
            p_points, l_points = pressure().align(loading(), join='inner')
            line = isotherm_graph(axes,
                                  p_points,
                                  l_points,
                                  label, styles_dict=styles)

            if secondary_prop is not None:
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
        color = None

        # If there's an adsorption branch, plot it
        if ads:
            plot_branch = 'ads'
            if isotherm.has_branch(branch=plot_branch):

                # Label the branch
                lbl = line_label + ' ads'

                # Call the plotting function
                line = graph_caller(axes, axes2,
                                    isotherm, plot_branch,
                                    lbl, plot_type, styles)

                color = line.get_color()

        if des:
            plot_branch = 'des'
            if isotherm.has_branch(branch=plot_branch):

                # Label the branch
                lbl = line_label + ' des'

                # Set marker fill to empty, and match the colour from desorption
                styles['line_style']['mfc'] = 'none'
                if color is not None:
                    styles['line_style']['c'] = color

                # Call the plotting function
                line = graph_caller(axes, axes2,
                                    isotherm, plot_branch,
                                    lbl, plot_type, styles)

                # Delete the colour changes to go back to original settings
                del styles['line_style']['mfc']
                if color is not None:
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

    # Add the legend
    lines, labels = axes.get_legend_handles_labels()
    if plot_type == 'combo':
        lines2, labels2 = axes2.get_legend_handles_labels()
        lines = lines + lines2
        labels = labels + labels2

    legend_style = dict(handlelength=3, fontsize=15, loc='lower right')
    if legend_bottom:
        legend_style['bbox_to_anchor'] = (0.5, -0.1)
        legend_style['ncol'] = 2
        legend_style['loc'] = 'upper center'
    elif len(lines) > 5:
        legend_style['bbox_to_anchor'] = (1.15, 0.5)
        legend_style['loc'] = 'center left'

    lgd = axes.legend(lines, labels, **legend_style)

    # Fix size of graphs
    plt.tight_layout()

    if save is True:
        plt.savefig(path, bbox_extra_artists=(lgd,),
                    bbox_inches='tight', transparent=False)

    return axes, axes2
