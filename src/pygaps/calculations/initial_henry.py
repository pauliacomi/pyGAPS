"""Module calculating the initial henry constant."""

import matplotlib.pyplot as plt
import numpy
import pandas

from ..classes.modelisotherm import ModelIsotherm
from ..graphing.isothermgraphs import plot_iso
from ..utilities.exceptions import CalculationError


def initial_henry_slope(isotherm,
                        max_adjrms=0.02,
                        p_limits=None,
                        l_limits=None,
                        verbose=False,
                        **plot_parameters):
    """
    Calculate a henry constant based on the initial slope.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to use for the calculation.
    max_adjrms : float, optional
        Maximum adjusted root mean square between the linear fit and isotherm data.
    p_limits : [float, float]
        Minimum and maximum pressure to take for the fitting routine.
    l_limits : [float, float]
        Minimum and maximum loading to take for the fitting routine.
    verbose : bool, optional
        Whether to print out extra information.
    plot_parameters : dict, optional
        Other parameters to be passed to the plotting function

    Returns
    -------
    float
        Initial Henry's constant.

    """
    # get the isotherm data on the adsorption branch
    data = isotherm.data(branch='ads')
    if p_limits:
        if p_limits[0] is None:
            p_limits[0] = -numpy.inf
        if p_limits[1] is None:
            p_limits[1] = numpy.inf
        data = data[data[isotherm.pressure_key] > p_limits[0]]
        data = data[data[isotherm.pressure_key] < p_limits[1]]
    if l_limits:
        if l_limits[0] is None:
            l_limits[0] = -numpy.inf
        if l_limits[1] is None:
            l_limits[1] = numpy.inf
        data = data[data[isotherm.loading_key] > l_limits[0]]
        data = data[data[isotherm.loading_key] < l_limits[1]]

    # add a zero point to the graph since the henry constant must have a zero intercept
    zeros = pandas.DataFrame(
        [[0 for column in data.columns]], columns=data.columns)
    data = zeros.append(data)

    # define variables
    adjrmsd = None
    initial_rows = len(data)
    rows_taken = initial_rows

    while rows_taken != 1:
        model_isotherm = ModelIsotherm.from_isotherm(
            isotherm,
            isotherm_data=data.head(rows_taken),
            pressure_key=isotherm.pressure_key,
            loading_key=isotherm.loading_key,
            model="Henry"
        )
        adjrmsd = model_isotherm.model.rmse / numpy.ptp(data[isotherm.loading_key])

        if adjrmsd > max_adjrms and rows_taken != 2:
            rows_taken = rows_taken - 1
            continue
        else:
            break

    # logging for debugging
    if verbose:
        print("Calculated K =", model_isotherm.model.params["K"])
        print("Starting points:", initial_rows)
        print("Selected points:", rows_taken)
        print("Final adjusted root mean square difference:", adjrmsd)
        model_isotherm.material_name = 'Henry model'
        params = {
            'plot_type': 'isotherm',
            'branch': 'ads',
            'fig_title': (' '.join([isotherm.material_name, isotherm.material_batch])),
            'lgd_keys': ['material_name', 'adsorbate', 't_iso']
        }
        params.update(plot_parameters)
        plot_iso([isotherm, model_isotherm], **params)

        plt.show()

    # return the henry constant
    return model_isotherm.model.params["K"]


def initial_henry_virial(isotherm, verbose=False, optimization_params=None, **plot_parameters):
    """
    Calculate an initial Henry constant based on fitting the virial equation.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to use for the calculation.
    verbose : bool, optional
        Whether to print out extra information.
    optimization_params : dict
        Custom parameters to pass to SciPy.optimize.least_squares.
    plot_parameters : dict
        Custom parameters to pass to pygaps.plot_iso.

    Returns
    -------
    float
        Initial Henry's constant.

    """
    model_isotherm = ModelIsotherm.from_pointisotherm(
        isotherm,
        model='Virial',
        optimization_params=optimization_params,
        verbose=verbose
    )

    if verbose:
        model_isotherm.material_name = 'model'
        try:
            params = {
                'plot_type': 'isotherm',
                'branch': 'ads',
                'logx': False,
                'fig_title': (' '.join([isotherm.material_name, isotherm.material_batch])),
                'lgd_keys': ['material_name', 'adsorbate', 't_iso']
            }
            params.update(plot_parameters)
            plot_iso([isotherm, model_isotherm], **params)
            plt.show()
        except CalculationError:
            plt.close()
            print('Cannot plot comparison due to model instability')

    return model_isotherm.model.params['K']
