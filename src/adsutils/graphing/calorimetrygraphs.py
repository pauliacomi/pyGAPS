# %%
from bokeh.io import show, output_notebook
from bokeh.plotting import figure
import pandas


def plot_calo(path):
    calo_csv = pandas.read_csv(path + r"\data.csv", sep=';', encoding='cp1252')
    print(calo_csv)

    # %%

    # output to notebook
    output_notebook()

    # create a new plot
    p = figure(
        # tools="pan,wheel_zoom,box_zoom,reset",
        title="calo",
        x_axis_label='time', y_axis_label='pressure',
        plot_width=900
    )

    # add some renderers
    p.line(calo_csv["Temps(s)"], calo_csv["Basse Pression(Bar)"],
           legend="Low pressure", line_width=3)
    p.line(calo_csv["Temps(s)"], calo_csv["Haute Pression(Bar)"],
           legend="High pressure", line_color="red", line_width=3)

    # show the results
    show(p)

    return
