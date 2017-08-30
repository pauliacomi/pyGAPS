# %%
from os.path import expanduser

import pygaps

#################################################################################
#       Database import
#
# %%
db_path = expanduser(
    r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")
isotherms = []
criteria = {
    'sname':        "UiO-66(Zr)",
    # 'sbatch':       "",
    # 'user':         "PI",
    't_exp':        303,
    # 't_act':        "",
    # 'machine':      "",
    # 'gas':          "N2",
    # 'exp_type':     "",
}
isotherms = pygaps.db_get_experiments(db_path, criteria)
sel_isotherms = isotherms

#################################################################################
#################################################################################


#################################################################################
#################################################################################
# Common plots for the selected isotherms
#   isotherm
#   enthalpy
#   iso-enthalpy
#
# %%
fig_title = sel_isotherms[0].gas + 'physisorption'
legend_list = ['name']
enthalpy_max = 60
loading_max = None
pressure_max = None

pygaps.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
pygaps.plot_iso(sel_isotherms, plot_type='isotherm', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)
pygaps.plot_iso(sel_isotherms, plot_type='enthalpy', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
pygaps.plot_iso(sel_isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=False, color=True, fig_title=fig_title, legend_list=legend_list)
pygaps.plot_iso(sel_isotherms, plot_type='iso-enth', branch=['ads'],
                  y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                  logarithmic=True, color=True, fig_title=fig_title, legend_list=legend_list)


# %%
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

    legend_list = ['batch', 't_act']

    enthalpy_max = None
    loading_max = None
    pressure_max = None

    for iso in s_isotherms:

        title = iso.gas

        fig_title = title
        img_title = save_folder + "\\" + iso.name + ' ' + fig_title + '.png'

        pygaps.plot_iso({iso},
                          plot_type='iso-enth',
                          branch=['ads', 'des'],
                          path=fig_title,
                          logarithmic=False, color=True, save=save,
                          y_enthmaxrange=enthalpy_max,
                          y_adsmaxrange=loading_max,
                          xmaxrange=pressure_max,
                          fig_title=fig_title, legend_list=legend_list)

        fig_title = title + " log"
        img_title = save_folder + "\\" + iso.name + ' ' + fig_title + '.png'

        pygaps.plot_iso({iso}, plot_type='iso-enth', branch=['ads', 'des'], path=fig_title,
                          logarithmic=True, color=True, save=save,
                          y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                          fig_title=fig_title, legend_list=legend_list)

        fig_title = title + " enthalpy"
        img_title = save_folder + "\\" + iso.name + ' ' + fig_title + '.png'

        pygaps.plot_iso({iso}, plot_type='enthalpy', branch=['ads', 'des'], path=fig_title,
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

    pygaps.plot_iso(s_isotherms, plot_type='iso-enth', branch=['ads', 'des'], path=img_title,
                      logarithmic=False, color=True, save=save,
                      y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                      fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

    fig_title = title + " log"
    img_title = save_folder + "\\" + title + ' log isotherms.png'

    pygaps.plot_iso(s_isotherms, plot_type='iso-enth', branch=['ads', 'des'], path=img_title,
                      logarithmic=True, color=True, save=save,
                      y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=pressure_max,
                      fig_title=fig_title, legend_list=legend_list, legend_bottom=True)

    fig_title = title + " enthalpy"
    img_title = save_folder + "\\" + title + ' enthalpy.png'

    pygaps.plot_iso(s_isotherms, plot_type='enthalpy', branch=['ads', 'des'], path=img_title,
                      logarithmic=False, color=True, save=save,
                      y_enthmaxrange=enthalpy_max, y_adsmaxrange=loading_max, xmaxrange=loading_max,
                      fig_title=fig_title, legend_list=legend_list, legend_bottom=True)


#################################################################################
#################################################################################
#       Selections
# %%
sel_isotherms = isotherms
print("Selected:", len(sel_isotherms))

# %%
# ONE GAS
req_gas = ['C4H10']
sel_isotherms = []
for gas in req_gas:
    sel_isotherms = list(filter(lambda x: x.gas == gas, isotherms))
print("Selected:", len(sel_isotherms))

# %%
#############
# ONE BATCH
req_batch = ["SKDM030"]
sel_isotherms = []
for batch in req_batch:
    sel_isotherms += list(filter(lambda x: x.batch in batch, isotherms))

print("Selected:", len(sel_isotherms))

# %%
#############
# ONE USER
req_user = ["Pi"]
sel_isotherms = list(filter(lambda x: x.user in req_user, isotherms))
print("Selected:", len(sel_isotherms))

# %%
#############
# SEVERAL BATCHES
s2_isotherms = []
req_batch = ["KRICT AlO Pellets", "KRICT01", "KRICT PVA Pellets"]
for batch in req_batch:
    s2_isotherms += list(filter(lambda x: x.batch == batch, sel_isotherms))
sel_isotherms = s2_isotherms
print("Selected:", len(sel_isotherms))

# %%
#############
# SEVERAL USERS
s2_isotherms = []
req_batch = ["ADW", "NC"]
for user in req_batch:
    s2_isotherms += list(filter(lambda x: x.user in user, sel_isotherms))
sel_isotherms = s2_isotherms
print("Selected:", len(sel_isotherms))

# %%
#############
# SEVERAL GASSES
s2_isotherms = []
req_batch = ["C4H10"]
for gas in req_batch:
    s2_isotherms += list(filter(lambda x: x.gas in gas, sel_isotherms))
sel_isotherms = s2_isotherms
print("Selected:", len(sel_isotherms))

# %%
req_iso = [0, 2]
sel_isotherms = [sel_isotherms[i] for i in req_iso]
print("Selected:", len(sel_isotherms))

# %%
#############
# SEVERAL GASSES
req_gas = ["N2", "CO2", "CO", "CH4", "C2H6", "C3H6", "C3H8", "C4H10"]
for gas in req_gas:
    s2_isotherms = list(filter(lambda x: x.gas in gas, sel_isotherms))

# %%
save_folder = expanduser(r"~\Desktop")
plot_individual_selected(sel_isotherms, save=False, save_folder=save_folder)

# %%
save_folder = expanduser(r"~\Desktop")
sel_isotherms.sort(key=lambda isotherm: isotherm.batch, reverse=True)
plot_all_selected(sel_isotherms, True, 150, None,
                  None, save_folder=save_folder)

# %%
sample = sel_isotherms[1]
# %%
factor = 2.8
# %%
sample.data[sample.loading_key] = sample.data[sample.loading_key].apply(
    lambda x: x * factor)

# %%
sample.data[sample.loading_key] = sample.data[sample.loading_key].apply(
    lambda x: x / factor)
