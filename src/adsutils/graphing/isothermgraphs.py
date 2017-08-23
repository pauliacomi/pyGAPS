# %%
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import cm
from numpy import linspace

from ..utilities.matplotlib_chemformula import convert_chemformula

# ! list of plot types
_PLOT_TYPES = ["isotherm", "enthalpy", "iso-enth"]

# ! list of branch types
_BRANCH_TYPES = ["ads", "des"]


def plot_iso(isotherms, plot_type, branch, logarithmic=False, color=True,
             xmaxrange=None, y_adsmaxrange=None, y_enthmaxrange=None,
             legend_list=None, fig_title=None, legend_bottom=False,
             save=False, path=None):
    """
    Plots the isotherm graphs requested

    :param isotherms: an array of the isotherms to be plotted
    :param plot_type: the plot type, isotherm/enthalpies or combination
    :param branch: list with branches to disply, options: 'ads', 'des'
    :param logarithmic: whether the graph should be logarithmic in the x axis
    :param color: whether the graph should be coloured or grayscale

    """

    # Initial checks
    #
    # Check for isotherm units
    mode_adsorbent = isotherms[0].mode_adsorbent
    mode_pressure = isotherms[0].mode_pressure

    unit_pressure = isotherms[0].unit_pressure
    unit_loading = isotherms[0].unit_loading

    if not all(isotherm.mode_adsorbent == mode_adsorbent for isotherm in isotherms):
        raise Exception("Mode for adsorbent does not match all isotherms")

    if not all(isotherm.mode_pressure == mode_pressure for isotherm in isotherms):
        raise Exception("Mode for pressure does not match all isotherms")

    if not all(isotherm.unit_pressure == unit_pressure for isotherm in isotherms):
        raise Exception("Units for pressure do not match all isotherms")

    if not all(isotherm.unit_loading == unit_loading for isotherm in isotherms):
        raise Exception("Units for loading do not match all isotherms")

    # Check for plot type validity
    if plot_type is None:
        raise Exception("Specify a plot type to graph"
                        " e.g. plot_type=\"isotherm\"")
    if plot_type not in _PLOT_TYPES:
        raise Exception("Plot type %s not an option. See viable"
                        "types in _PLOT_TYPES" % plot_type)

    if plot_type == 'enthalpy' or plot_type == 'iso-enth':
        if all('enthalpy' not in isotherm.other_keys for isotherm in isotherms):
            raise Exception(
                "None of the isotherms supplied have enthalpy data")

    # Store which branches will be displayed
    if branch is None:
        raise Exception("Specify a branch to display"
                        " e.g. branch=\"ads\"")
    if not [i for i in branch if i in _BRANCH_TYPES]:
        raise Exception("One of the supplied branch types is not valid."
                        "See viable types in _BRANCH_TYPES")

    ads = False
    des = False
    if 'ads' in branch:
        ads = True
    if 'des' in branch:
        des = True

    # Add limits for x and y
    max_y1 = 0
    max_y2 = 0
    axes2 = None

    # Add limits for data x and y
    maxrange_pressure = None
    maxrange_enthalpy = None
    maxrange_loading = None

    # Settings and graph generation
    #
    # Generate the graph iself
    fig, axes = plt.subplots(1, 1, figsize=(8, 8))

    # Build the name of the axes
    _TEXT_PRESSURE = r'Pressure'
    _TEXT_LOADING = r'Loading'
    _TEXT_ENTHALPY = r'Enthalpy of adsorption $(-kJ\/mol^{-1})$'
    if mode_pressure == "absolute":
        _TEXT_PRESSURE = _TEXT_PRESSURE + ' ($' + unit_pressure + '$)'
    elif mode_pressure == "relative":
        _TEXT_PRESSURE = "Relative " + _TEXT_PRESSURE
    if mode_adsorbent == "mass":
        _TEXT_LOADING = _TEXT_LOADING + ' ($' + unit_loading + r'\/g^{-1}$)'
    elif mode_adsorbent == "volume":
        _TEXT_LOADING = _TEXT_LOADING + ' ($' + unit_loading + r'\/cm^{-3}$)'

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
        pc_enth = (cy2 * cy3)
    else:
        pc_iso = (cy1 * cy5 * cy6)
        pc_enth = (cy4 * cy5 * cy6)

    # Set the type of the graph
    if plot_type == 'isotherm':
        axes.set_prop_cycle(pc_iso)
        maxrange_pressure = xmaxrange
    elif plot_type == 'enthalpy':
        axes.set_prop_cycle(pc_enth)
        maxrange_enthalpy = xmaxrange
    elif plot_type == 'iso-enth':
        axes2 = axes.twinx()
        axes.set_prop_cycle(pc_iso)
        axes2.set_prop_cycle(pc_enth)
        maxrange_pressure = xmaxrange

    # Styles in the graph
    title_style = dict(horizontalalignment='center',
                       fontsize=25, fontdict={'family': 'monospace'})
    label_style = dict(horizontalalignment='center',
                       fontsize=20, fontdict={'family': 'monospace'})
    line_style = dict(linewidth=2, markersize=4)
    tick_style = dict(labelsize=17)
    legend_style = dict(handlelength=3, fontsize=15, loc='lower right')
    styles = dict(title_style=title_style, label_style=label_style,
                  line_style=line_style, tick_style=tick_style)

    # Put grid on plot
    axes.grid(True, zorder=5)

    # Graph title
    axes.set_title(fig_title, **title_style)

    ###########################################
    # Graph functions

    # Graph legend builder
    def build_label(list_, isotherm):
        """
        Builds a label for the legend depending on requested parameters
        """
        if list_ is None:
            return isotherm.sample_name + ' ' + convert_chemformula(isotherm.gas)
        else:
            text = []
            if 'sample_name' in list_:
                text.append(isotherm.sample_name)
            if 'sample_batch' in list_:
                text.append(isotherm.sample_batch)
            if 'gas' in list_:
                text.append(convert_chemformula(isotherm.gas))
            if 'type' in list_:
                text.append(isotherm.type)
            if 'user' in list_:
                text.append(isotherm.user)
            if 'machine' in list_:
                text.append(isotherm.machine)
            if 't_act' in list_:
                text.append(str(isotherm.t_act) + ' °C')
            if 't_exp' in list_:
                text.append(str(isotherm.t_exp) + ' K')
            if 'date' in list_:
                text.append(isotherm.date)

            return " ".join(text)

    def isotherm_graph(axes, data_x, data_y, line_label, styles_dict):
        "Plot an isotherm graph, regular or logarithmic"

        # Labels and ticks
        axes.set_xlabel(_TEXT_PRESSURE, **styles_dict['label_style'])
        axes.set_ylabel(_TEXT_LOADING, **styles_dict['label_style'])
        axes.tick_params(axis='both', which='major',
                         **styles_dict['tick_style'])

        # Generate a linestyle from the incoming dictionary
        line_style = styles_dict['line_style']
        specific_line_style = dict(linewidth=2, markersize=8)
        line_style.update(specific_line_style)

        # Plot line
        line, = axes.plot(data_x, data_y, label=line_label, **line_style)

        return line

    def enthalpy_adsorbed_graph(axes, data_x, data_y, line_label, styles_dict):
        "Plot an enthalpy graph, versus moles"

        # Labels and ticks
        axes.set_xlabel(_TEXT_LOADING, **styles_dict['label_style'])
        axes.set_ylabel(_TEXT_ENTHALPY, **styles_dict['label_style'])
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

    def graph_caller(axes, axes2, p_data, l_data, e_data, label, pl_type, styles):
        """
        Convenience function to call other graphing functions
        """

        max_y1 = 0
        max_y2 = 0
        line = None

        if pl_type == 'isotherm' and p_data is not None and len(p_data) > 0:
            fl_data = l_data[:len(p_data)]
            max_y1 = max(fl_data)
            line = isotherm_graph(axes, p_data, fl_data,
                                  label, styles_dict=styles)

        elif pl_type == 'enthalpy' and e_data is not None and len(e_data) > 0:
            fe_data = e_data[:len(l_data)]
            max_y1 = max(fe_data)
            line = enthalpy_adsorbed_graph(
                axes, l_data, fe_data, label, styles_dict=styles)

        elif pl_type == 'iso-enth' and p_data is not None and len(p_data) > 0:
            fl_data = l_data[:len(p_data)]
            max_y1 = max(fl_data)
            line = isotherm_graph(axes, p_data, fl_data,
                                  label, styles_dict=styles)
            if e_data is not None:
                fe_data = e_data[:len(p_data)]
                max_y2 = max(fe_data)
                enthalpy_adsorbed_graph(
                    axes2, p_data, fe_data, label + " dE", styles_dict=styles)
            else:
                axes2.plot(0, 0)

        return max_y1, max_y2, line

    #####################################
    # Actual plotting

    # Plot the data
    for isotherm in isotherms:

        line_label = build_label(legend_list, isotherm)

        color = None

        if ads:
            if isotherm.has_ads():
                line_label_ = line_label + ' ads'
                lmax_y1, lmax_y2, line = graph_caller(axes, axes2,
                                                      isotherm.pressure_ads(
                                                          maxrange_pressure),
                                                      isotherm.loading_ads(
                                                          maxrange_loading),
                                                      isotherm.other_key_ads("enthalpy",
                                                                             maxrange_enthalpy),
                                                      line_label_, plot_type, styles)
                max_y1 = max(max_y1, lmax_y1)
                max_y2 = max(max_y2, lmax_y2)
                color = line.get_color()

        if des:
            if isotherm.has_des():
                styles['line_style']['mfc'] = 'none'
                if color is not None:
                    styles['line_style']['c'] = color
                line_label_ = line_label + ' des'
                lmax_y1, lmax_y2, _ = graph_caller(axes, axes2,
                                                   isotherm.pressure_des(
                                                       maxrange_pressure),
                                                   isotherm.loading_des(
                                                       maxrange_loading),
                                                   isotherm.other_key_des("enthalpy",
                                                                          maxrange_enthalpy),
                                                   line_label_, plot_type, styles)
                max_y1 = max(max_y1, lmax_y1)
                max_y2 = max(max_y2, lmax_y2)
                del styles['line_style']['mfc']
                del styles['line_style']['c']

    # Convert the exes into logarithmic if required
    if not logarithmic:
        axes.set_xscale('linear')
        axes.set_xlim(xmin=0)
    else:
        axes.set_xscale('log')

    # Set the limits for y
    if y_adsmaxrange is None:
        if plot_type == 'enthalpy':
            pass
        else:
            axes.set_ylim(ymin=0, ymax=max_y1 * 1.1)
    else:
        if plot_type == 'enthalpy':
            pass
        else:
            axes.set_ylim(ymin=0, ymax=y_adsmaxrange)

    if y_enthmaxrange is None:
        if plot_type == 'enthalpy':
            axes.set_ylim(ymin=0, ymax=max_y1 * 1.1)
        elif plot_type == 'iso-enth':
            axes2.set_ylim(ymin=0, ymax=max_y2 * 1.1)
    else:
        if plot_type == 'enthalpy':
            axes.set_ylim(ymin=0, ymax=y_enthmaxrange)
        elif plot_type == 'iso-enth':
            axes2.set_ylim(ymin=0, ymax=y_enthmaxrange)

    # Add the legend
    lines, labels = axes.get_legend_handles_labels()
    if plot_type == 'iso-enth':
        lines2, labels2 = axes2.get_legend_handles_labels()
        lines = lines + lines2
        labels = labels + labels2

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

    plt.show()

    return
