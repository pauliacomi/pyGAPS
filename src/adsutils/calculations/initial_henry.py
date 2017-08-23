"""
This module calculates the initial henry constant based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

# import copy

import matplotlib.pyplot as plt
import numpy

# import pandas

# from ..classes.modelisotherm import ModelIsotherm
# from ..graphing.isothermgraphs import plot_iso


def calc_initial_henry(isotherm, max_adjrms=0.1, verbose=False):
    """
    Calculates a henry constant based on initial slope

    :param isotherm: an isotherm to use for the calculation

    """
    # # copy the isotherm into memory
    # loading = isotherm.loading_ads()
    # pressure = isotherm.pressure_ads()

    # # if the initial pressure is not zero
    # # add a zero point to the graph since the henry constant must have a zero intercept
    # if loading[0] != 0:
    #     loading.insert(0, 0)
    #     pressure.insert(0, 0)

    # adjrmsd = 1
    # initial_rows = len(loading)
    # rows_taken = initial_rows

    # while rows_taken != 1:
    #     model_isotherm = ModelIsotherm(selected_points.data_ads().head(rows_taken),
    #                                    loading_key=isotherm.loading_key,
    #                                    pressure_key=isotherm.pressure_key,
    #                                    model="Henry")
    #     adjrmsd = model_isotherm.rmse / numpy.ptp(isotherm.loading_ads())

    #     if adjrmsd > max_adjrms and rows_taken != 2:
    #         rows_taken = rows_taken - 1
    #         continue
    #     else:
    #         break

    # # modify the isotherm to have only the identified points
    # selected_points.data_ads() = selected_points.data_ads().head(rows_taken)
    # model_selected = selected_points.get_model_isotherm("Henry")
    # model_selected.name = "Selected henry points"

    # # logging for debugging
    # if verbose:
    #     print("Starting points:", initial_rows)
    #     print("Selected points:", rows_taken)
    #     print("Final adjusted root mean square difference:", adjrmsd)
    #     plot_iso({isotherm, model_selected}, plot_type='isotherm',
    #              branch='ads', logarithmic=False, color=True)

    # # return the henry constant
    # return model_isotherm.params["KH"]


def calc_initial_henry_virial(isotherm, verbose=False):
    """
    Calculates a henry constant based on fitting the virial equation

    :param isotherm: an isotherm to use for the calculation

    """

    pressures = numpy.array(isotherm.pressure_ads())
    loadings = numpy.array(isotherm.loading_ads())
    if pressures[0] == 0 or loadings[0] == 0:
        pressures = numpy.delete(pressures, 0, 0)
        loadings = numpy.delete(loadings, 0, 0)
    if numpy.amin(pressures) < 0 or numpy.amin(loadings) < 0:
        print("Some values negative")
        return numpy.NaN

    ln_n_over_p = numpy.log(numpy.divide(loadings, pressures))

    full_info = numpy.polyfit(loadings, ln_n_over_p, 3, full=True)
    virial_C = full_info[0]
    virial_func = numpy.poly1d(virial_C)

    # logging for debugging
    if verbose:
        print("Virial coefficients:", full_info[0])
        print("Residuals:", full_info[1])
        print("Rank:", full_info[2])
        print("Singular values:", full_info[3])
        print("Conditioning threshold:", full_info[4])
        xp = numpy.linspace(0, numpy.amax(loadings), 100)
        plt.plot(loadings, ln_n_over_p, '.', xp, virial_func(xp), '-')
        plt.xlabel("Loading")
        plt.ylabel("ln(n/p)")
        plt.show()

    return numpy.exp(virial_func(0))
