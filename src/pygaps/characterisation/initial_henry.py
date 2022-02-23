"""Module calculating the initial henry constant."""

import numpy

from pygaps import logger
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.modelling import get_isotherm_model
from pygaps.utilities.exceptions import ParameterError


def initial_henry_slope(
    isotherm: "PointIsotherm | ModelIsotherm",
    max_adjrms: int = 0.02,
    p_limits: "tuple[float, float]" = None,
    l_limits: "tuple[float, float]" = None,
    verbose: bool = False,
    **plot_parameters,
):
    """
    Calculate a henry constant based on the initial slope.

    Parameters
    ----------
    isotherm : PointIsotherm, ModelIsotherm
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
    if p_limits or l_limits:

        if not p_limits:
            p_limits = [-numpy.inf, numpy.inf]
        if not l_limits:
            l_limits = [-numpy.inf, numpy.inf]

        pressure = isotherm.pressure(branch='ads', indexed=True, limits=p_limits)
        loading = isotherm.loading(branch='ads', indexed=True, limits=l_limits)

        pressure, loading = pressure.align(loading, join='inner')
        pressure, loading = pressure.values, loading.values

        if len(pressure) == 0 or len(loading) == 0:
            raise ParameterError("Limits chosen lead to no selected data.")

    else:
        pressure = isotherm.pressure(branch='ads')
        loading = isotherm.loading(branch='ads')

    # add a zero point to the graph since the henry
    # constant must have a zero intercept (if needed)
    if pressure[0] != 0 and loading[0] != 0:
        pressure = numpy.hstack(([0], pressure))
        loading = numpy.hstack(([0], loading))

    # define model
    henry = get_isotherm_model("Henry")
    henry.pressure_range = [min(pressure), max(pressure)]
    henry.loading_range = [min(loading), max(loading)]

    # define variables
    adjrmsd = None
    initial_rows = len(pressure)
    rows_taken = initial_rows

    while rows_taken != 1:

        param_guess = henry.initial_guess(pressure[:rows_taken], loading[:rows_taken])
        # fit model to isotherm data
        henry.fit(pressure[:rows_taken], loading[:rows_taken], param_guess)
        adjrmsd = henry.rmse / numpy.ptp(loading)

        if adjrmsd > max_adjrms and rows_taken != 2:
            rows_taken = rows_taken - 1
            continue
        else:
            break

    if verbose:
        logger.info(f"Calculated K = {henry.params['K']:.4g}")
        logger.info(f"Starting points: {initial_rows}")
        logger.info(f"Selected points: {rows_taken}")
        logger.info(f"Final adjusted RMSE: {adjrmsd:.3g}")
        params = {'branch': 'ads', 'lgd_keys': ['material']}
        params.update(plot_parameters)
        henry.pressure_range = [pressure[0], pressure[:rows_taken][-1]]
        henry.loading_range = [pressure[0], loading[:rows_taken][-1]]

        iso_params = isotherm.to_dict()
        model_isotherm = ModelIsotherm(
            model=henry,
            **iso_params,
        )
        model_isotherm.material = "model"
        from pygaps.graphing.isotherm_graphs import plot_iso
        plot_iso([isotherm, model_isotherm], **params)

    # return the henry constant
    return henry.params["K"]


def initial_henry_virial(
    isotherm: "PointIsotherm | ModelIsotherm",
    optimization_params: dict = None,
    verbose: bool = False,
):
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

    Returns
    -------
    float
        Initial Henry's constant.

    """
    model_isotherm = ModelIsotherm.from_pointisotherm(
        isotherm, model='Virial', optimization_params=optimization_params, verbose=verbose
    )
    return model_isotherm.model.params['K']
