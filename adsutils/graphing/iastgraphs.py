#%%
import xlwings as xw
import numpy as np
import matplotlib.pyplot as plt

def plot_iast_vle():
    "Function to generate the selectivity graph"

    # get excel workbook, sheet and range
    wb = xw.Book
    sht = xw.sheets[3]
    data_1 = sht.range('A1').options(np.array, expand='table').value
    data_2 = sht.range('D1').options(np.array, expand='table').value
    data_3 = sht.range('G1').options(np.array, expand='table').value

    # split into multiple
    data_1_x, data_1_y = np.hsplit(data_1, 2)
    data_2_x, data_2_y = np.hsplit(data_2, 2)
    data_3_x ,data_3_y = np.hsplit(data_3, 2)

    text_x = r'y $CO_2$'
    text_y = r'x $CO_2$'
    #title_graph = r'$CO_2$ in $N_2$, 303K'
    #title_graph = r'$CO_2$ in $CH_4$, 303K'
    title_graph = r'$C_3H_6$ in $C_3H_8$, 303K'

    fig, ax = plt.subplots(figsize=(8, 8))

    # graph title
    plt.title(title_graph, fontsize=22, ha='center', va='bottom')

    # labels for the axes
    plt.xlabel(text_x, fontsize=15)
    plt.ylabel(text_y, fontsize=15)

    plt.plot(data_1_x, data_1_y, label='1 bar')
    plt.plot(data_2_x, data_2_y, label='5 bar')
    plt.plot(data_3_x, data_3_y, label='10 bar')

    # Straight line
    line = [0,1]
    plt.plot(line, line, color = 'black')

    plt.legend(fontsize = 15, loc='lower right')

    ax.grid(True, zorder=5)
    ax.set_xlim(xmin=0, xmax=1)
    ax.set_ylim(ymin=0, ymax=1)
    ax.set_xscale('linear')
    
    title = title_graph + '.png'
    plt.savefig(title, transparent=False)

    plt.show()

    return

plot_iast_vle()
