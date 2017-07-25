#%%
import numpy as np
import matplotlib.pyplot as plt
from peakutils.plot import plot as pplot
import pandas as pd
import peakutils

from scipy import signal, misc
from bokeh.io import push_notebook, show, output_notebook
from bokeh.plotting import figure

path = r"calo"

#%% numpy based
calodata_np = np.genfromtxt(path + "\data.csv", delimiter=";")
time_arr = calodata_np[1:,1]
pres_arr = calodata_np[1:,3]
pres_v_time = np.vstack((time_arr,pres_arr))
print(calodata_np.shape)

#%% pandas based
calodata_pd = pd.read_csv(path + "\data.csv", sep=';', encoding='cp1252')
calodata_pd.describe()

#%%
calodata_pd.head(20)

#%%
time_label = "Temps(s)"
calo_label = "Calorimètre(W)"
bp_label = "Basse Pression(Bar)"
hp_label = "Haute Pression(Bar)"
v6_label = "Vanne 6"
step_label = "Etape"
dose_label = "Dose"

#%% plot bokeh
# output to notebook
output_notebook()

# create a new plot
p = figure(
    #tools="pan,wheel_zoom,box_zoom,reset",
    title="calo",
    x_axis_label='time', y_axis_label='pressure',
    plot_width=900
)

# add some renderers
p.line(calodata_pd["Temps(s)"], calodata_pd["filtered_col"], legend="Filter", line_width=3)
p.line(calodata_pd["Temps(s)"], calodata_pd[hp_label], legend="High pressure", line_color="red", line_width=3)

# show the results
show(p)


#%%
increases, decreases = find_change_points(calodata_pd[time_label], calodata_pd[hp_label], verbose=True)

#%%
small_dose_step = 2
medium_dose_step = 3
large_dose_step = 4

back_offset = 10
small_dose_offset = 400
medium_dose_offset = 400
large_dose_offset = 500

calc_pd = pd.DataFrame(columns=[time_label, bp_label, hp_label, step_label, dose_label, time_label, bp_label, hp_label, step_label, dose_label])
print(calc_pd)

for index, point in enumerate(decreases):

    start_pt = calodata_pd.loc[point - back_offset, [time_label, bp_label, hp_label, step_label, dose_label]]

    calc_pd.iloc[index, 0:4] = start_pt

    if start_pt[step_label] == small_dose_step:
        forwd_offset = small_dose_offset
    elif start_pt[step_label] == medium_dose_step:
        forwd_offset = medium_dose_offset
    elif start_pt[step_label] == large_dose_step:
        forwd_offset = large_dose_offset
    else:
        raise Exception("Unknown step detected")

    if len(decreases) > (index + 1) and point + forwd_offset > decreases[index+1]:
        raise Exception("Forward step too large")

    end_pt = calodata_pd.loc[point + forwd_offset, [time_label, bp_label, hp_label, step_label, dose_label]]

    complete_pt_data = pd.DataFrame(pd.concat([start_pt, end_pt], axis=0))
    complete_pt_data.describe()
    #calc_pd = pd.concat(complete_pt_data, axis=1)

#%%
start_pt

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def find_change_points(time_data, pressure_data, threshold=-0.05, peak_min_distances=100, verbose=False):
    """
    returns inflexion points
    """
    #%% generate detection signal by convoluting with first order derivative of gaussian
    gaussian = signal.gaussian(40, 2)
    filtered_col = signal.fftconvolve(pressure_data, np.append(np.diff(gaussian),0), mode="same")

    #%% remove initial and final points and pad them with zeroes
    trim_amount = 20
    filtered_col[0:trim_amount] = 0
    filtered_col[len(filtered_col)-trim_amount:len(filtered_col)] = 0

    #%% Determine where the elements lower than the threshold are located
    increases, = np.where(filtered_col>-threshold)
    decreases, = np.where(filtered_col<threshold)

    #%%remove any points closer together than the requested
    def remove_extra_p(arr):
        """
        Ensures that there are no points which are doubled
        """
        first_p = 0
        mask = np.ones(len(arr), dtype=bool)

        for index, point in enumerate(arr):
            if index == 0:
                first_p = point
                continue
            elif point - first_p > peak_min_distances:
                first_p = point
                continue
            else:
                mask[index] = False

        arr = arr[mask]

        return arr

    increases = remove_extra_p(increases)
    decreases = remove_extra_p(decreases)

    if(verbose):
        #%% plot matplotlib
        fig, axes = plt.subplots(1, 1, figsize=(15, 5))
        pplot(time_data, pressure_data, increases)
        plt.show()
        fig, axes = plt.subplots(1, 1, figsize=(15, 5))
        pplot(time_data, pressure_data, decreases)
        plt.show()

    #%%
    return increases, decreases
