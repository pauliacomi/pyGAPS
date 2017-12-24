"""
This module calculates the initial henry constant based on an isotherm
"""

import matplotlib.pyplot as plt
import numpy
import pandas

from ..classes.modelisotherm import ModelIsotherm
from ..graphing.isothermgraphs import plot_iso


def calc_initial_henry_slope(isotherm, max_adjrms=0.02, verbose=False):
    """
    Calculates a henry constant based on initial slope

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to use for the calculation
    max_adjrms : float, optional
        Maximum adjusted root mean square between the linear fit and isotherm data.
    verbose : bool, optional
        Whether to print out extra information.

    Returns
    -------
    float
        Initial Henry's constant

    """
    # get the isotherm data on the adsorption branch
    data = isotherm.data(branch='ads')

    # add a zero point to the graph since the henry constant must have a zero intercept
    zeros = pandas.DataFrame(
        [[0 for column in data.columns]], columns=data.columns)
    data = zeros.append(data)

    # define variables
    adjrmsd = None
    initial_rows = len(data)
    rows_taken = initial_rows

    while rows_taken != 1:
        model_isotherm = ModelIsotherm.from_isotherm(isotherm,
                                                     data.head(rows_taken),
                                                     model="Henry")
        adjrmsd = model_isotherm.rmse / numpy.ptp(data[isotherm.loading_key])

        if adjrmsd > max_adjrms and rows_taken != 2:
            rows_taken = rows_taken - 1
            continue
        else:
            break

    # logging for debugging
    if verbose:
        print("Starting points:", initial_rows)
        print("Selected points:", rows_taken)
        print("Final adjusted root mean square difference:", adjrmsd)
        model_isotherm.sample_name = 'model'
        plot_iso([isotherm, model_isotherm],
                 plot_type='isotherm', branch=['ads'], logx=True,
                 legend_list=['sample_name'])

        plt.show()

    # return the henry constant
    return model_isotherm.model.params["KH"]


def calc_initial_henry_virial(isotherm, verbose=False):
    """
    Calculates an initial Henry constant based on fitting the virial equation

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to use for the calculation
    verbose : bool, optional
        Whether to print out extra information.

    Returns
    -------
    float
        Initial Henry's constant
    """

    model_isotherm = ModelIsotherm.from_pointisotherm(
        isotherm, model='Virial', verbose=verbose)

    if verbose:
        model_isotherm.sample_name = 'model'
        plot_iso([isotherm, model_isotherm],
                 plot_type='isotherm', branch=['ads'], logx=False,
                 legend_list=['sample_name'])

        plt.show()

    return model_isotherm.model.params['KH']
