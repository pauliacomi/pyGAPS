
import adsutils

#################################################################################
#################################################################################

def plot_individual_selected(s_isotherms, save=False, save_folder=None):
    """
    ## All selected isotherms on a separate graph with
    isotherm
    enthalpy
    iso-enthalpy
    optional saving
    """
    save = save

    legend_list = ['batch']

    enthalpy_max = None
    loading_max = None
    pressure_max = None

    for iso in s_isotherms:

        title = iso.gas

        fig_title = title
        img_title = save_folder + "\\" + iso.name + ' ' + fig_title + '.png'

        adsutils.plot_iso({iso}, plot_type='iso-enth', branch=['ads', 'des'], path=fig_title,
                        logarithmic=False, color=True, save=save,
                        y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                        fig_title=fig_title, legend_list=legend_list)

        fig_title = title + " log"
        img_title = save_folder + "\\" + iso.name + ' ' + fig_title + '.png'

        adsutils.plot_iso({iso}, plot_type='iso-enth', branch=['ads', 'des'], path=fig_title,
                        logarithmic=True, color=True, save=save,
                        y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                        fig_title=fig_title, legend_list=legend_list)

        fig_title = title + " enthalpy"
        img_title = save_folder + "\\" + iso.name + ' ' + fig_title + '.png'

        adsutils.plot_iso({iso}, plot_type='enthalpy', branch=['ads', 'des'], path=fig_title,
                        logarithmic=False, color=True, save=save,
                        y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                        fig_title=fig_title, legend_list=legend_list)


def plot_all_selected(s_isotherms, save, enthalpy_max, loading_max, pressure_max, save_folder=None):
    """
    ## All selected isotherms on one isotherm graph, optional saving
    """
    save = save

    title = s_isotherms[0].gas + " comparison " + s_isotherms[0].mode_adsorbent
    legend_list = ['batch']
    enthalpy_max = enthalpy_max
    loading_max = loading_max
    pressure_max = pressure_max

    fig_title = title
    img_title = save_folder + "\\" + title + ' isotherms.png'

    adsutils.plot_iso(s_isotherms, plot_type='iso-enth', branch=['ads'], path=img_title,
                    logarithmic=False, color=True, save=save,
                    y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                    fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

    fig_title = title + " log"
    img_title = save_folder + "\\" + title + ' log isotherms.png'

    adsutils.plot_iso(s_isotherms, plot_type='iso-enth', branch=['ads'], path=img_title,
                    logarithmic=True, color=True, save=save,
                    y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                    fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

    fig_title = title + " enthalpy"
    img_title = save_folder + "\\" + title + ' enthalpy.png'

    adsutils.plot_iso(s_isotherms, plot_type='enthalpy', branch=['ads'], path=img_title,
                    logarithmic=False, color=True, save=save,
                    y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=loading_max,
                    fig_title=fig_title, legend_list=legend_list, legend_bottom=True)
