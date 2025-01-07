"""
A module for predicting isotherms at different pressures given a measured
isotherm and calculated isosteric heats of adsorption
"""

# TODO Remove after this program no longer support Python 3.8.*
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import constants

from pygaps import logger
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.graphing import prediction_graphs
from pygaps.utilities.exceptions import ParameterError

R = constants.gas_constant


def predict_isotherm_from_enthalpy_clapeyron(
    isotherm: PointIsotherm,
    temperature_prediction: float,
    isosteric_enthalpy_dictionary: dict = None,
    branch: str = 'ads',
    verbose: bool = False,
    dographs: bool = True,
) -> PointIsotherm:
    r"""
    Predicts isotherm at a given temperature :math:`T_p`, from isosteric
    heats of adsorption :math:`\Delta H_{st}`, and pressure :math:`P_e` and
    temperature :math:`T_e` of original experimental isotherm. Uses the
    Clausius-Clapeyron relationship to calculate the predicted pressures;

    ..math::
        \ln{P_p} = \left[ \Delta H_{st} \frac{T_p - T_e}{R T_p T_e} + \ln{P_e} \right ]_n

    Isosteric enthalpy, \Delta H_{st} can be input in two ways. The order
    of preference is as below;
        1. Defined in the other_data dictionary the `isotherm` object
        2. As a dict, like the output of enthalpy prediction functions, which
        use the `isosteric_enthalpy_dictionary` parameter.

    With option 1, it is important to ensure that the enthalpies
    actually correspond to loading points.

    Parameters
    ----------
    isotherm: PointIsotherm
        The experimental isotherm that has been measured.
        If it has an 'enthalpy' key in other_data, this will be used as the
        isosteric enthalpies with which to perform the calculation. Please
        ensure that these actually correspond to the loadings in the isotherm.
    temperature_predicted: float
        The temperature at which to predict the isotherm. Units are K.
    isosteric_enthalpy_dictionary: dict, optional
        You can input the output of enthalpy functions here. The function will
        then use the loading and isosteric_enthalpy (assumes kJ/mol) keys. Any
        dictionary with loading and enthalpy keys should work. Only used if
        enthalpy is not defined in original_isotherm.other_data.
    branch: {'ads', 'des', None}, optional
        Branch of the isotherm with which enthalpy is associated. Defaults to
        adsorption.
    verbose: bool, optional
        Whether to be verbose. Defaults to False.

    Returns
    -------
    predicted_isotherm: PointIsotherm
        The isotherm predicted from the above parameters. Pressure in Pa,
        loading in mol/kg.
    """
    if (isosteric_enthalpy_dictionary is None and 'enthalpy' not in isotherm.other_keys):
        raise ParameterError(
            '''
            There is no enthalpy specified. This can be specified by passing
            a dictionary of 'loading' and 'isosteric_enthalpy', or by passing
            an isotherm with enthalpy in its 'other_keys'
            '''
        )

    isotherm.convert(
        pressure_unit='Pa',
        pressure_mode='absolute',
        loading_unit='mol',
        loading_basis='molar',
        material_unit='kg',
        material_basis='mass',
    )
    isotherm.convert_temperature(unit_to='K')
    temperature_isotherm = isotherm.temperature

    if 'enthalpy' in isotherm.other_keys:
        enthalpy = isotherm.other_data(key='enthalpy', branch=branch)
        loading = isotherm.loading()
        if verbose:
            logger.info("Enthalpy retrieved from original_isotherm.other_keys.")

    elif isosteric_enthalpy_dictionary is not None:
        if not all(
            key in isosteric_enthalpy_dictionary for key in ['loading', 'enthalpy_sorption']
        ):
            raise ParameterError(
                '''
                You have specified a isosteric_enthalpy_dictionary as input,
                but it doesn't contain the right data.
                '''
            )

        enthalpy = isosteric_enthalpy_dictionary['enthalpy_sorption']
        loading = isosteric_enthalpy_dictionary['loading']

        if verbose:
            logger.info(
                '''
                Using enthalpy from isosteric_enthalpy_dictionary.
                '''
            )

    pressure_current = isotherm.pressure_at(
        loading,
        pressure_unit='Pa',
        interp_fill='extrapolate',
    )

    if not (len(loading) == len(pressure_current) == len(enthalpy)):
        raise ParameterError(
            f'''
            Loading, P_experiment, and enthalpies are different lengths.
            Check your data.
            Have you used the right branch ({branch})?
            '''
        )

    pressure_prediction = predict_pressure_raw(
        enthalpy, temperature_prediction, temperature_isotherm, pressure_current
    )

    isotherm_prediction = PointIsotherm(
        pressure=pressure_prediction,
        loading=loading,
        material=isotherm.material,
        adsorbate=str(isotherm.adsorbate),
        temperature=temperature_prediction,
        pressure_mode='absolute',
        pressure_unit='Pa',
        loading_basis='molar',
        loading_unit='mol',
        material_basis='mass',
        material_unit='kg',
        temperature_unit='K',
        apparatus='predicted from pygaps',
    )

    if verbose and dographs:
        prediction_graphs.plot_predict_isotherm_from_enthalpy(
            isotherm,
            isotherm_prediction,
            loading,
            enthalpy,
            branch=branch,
        )

    return isotherm_prediction


def predict_isosurface_from_enthalpy_clapeyron(
    isotherm: PointIsotherm,
    temperatures_prediction: list[float] = None,
    pressures_prediction: list[float] = None,
    isosteric_enthalpy_dictionary: dict = None,
    num: int = None,
    temperature_range: tuple[float, float] = None,
    branch: str = 'ads',
    verbose: bool = True,
):
    r"""
    Predicts loading as a function of pressure and temperature, from a single
    isotherm and a heat of adsorption. Uses `predict_isotherm` function which
    relies on the Clausius Clapeyron equation;

    ..math::
        \ln{P_p} = \left[ \Delta H_{st} \frac{T_p - T_e}{R T_p T_e} + \ln{P_e} \right ]_n

    Parameters
    ----------
    isotherm: PointIsotherm
        The experimental isotherm that has been measured.
        If it has an 'enthalpy' key in other_data, this will be used as the
        isosteric enthalpies with which to perform the calculation. Please
        ensure that these actually correspond to the loadings in the isotherm.
    temperatures_prediction: list[float], optional
        The temperatures (x-axis) of the resultant grid. If None, will use an
        array +/- 50 K from the temperature of `isotherm`. Number of
        steps defaults to be that of `pressures` array.
    pressures_prediction: list[float], optional
        The pressures (y-axis) of the resultant grid. If None, will use
        pressures in range of original isotherm, distributed linearly. Number
        of steps is determined by `num` parameter.
    isosteric_enthalpy_dictionary: dict, optional
        You can input the output of enthalpy functions here. The function will
        then use the loading and isosteric_enthalpy (assumes kJ/mol) keys. Any
        dictionary with loading and enthalpy keys should work. Only used if
        enthalpy is not defined in original_isotherm.other_data.
    num: int, optional
        The number of steps to use when generating the grid.
    branch: {'ads', 'des', None}, optional
        Branch of the isotherm with which enthalpy is associated. Defaults to
        adsorption.
    verbose: bool, optional
        Whether to be verbose. Defaults to False.

    Returns
    -------
    grid: pandas DataFrame
        Dataframe of predicted loadings as a function of temperature (index)
        and pressure (columns)
    """
    isotherm.convert(
        pressure_unit='Pa',
        pressure_mode='absolute',
    )
    temperature_current = isotherm.temperature

    if branch is None:
        raise ParameterError(
            """
            Functionality for both branches not completed yet. Please use 'ads'
            or 'des'.
            """
        )

    if num is None:
        num = 100

    if pressures_prediction is None:
        pressures_prediction = np.linspace(
            min(isotherm.pressure(branch=branch)),
            max(isotherm.pressure(branch=branch)),
            num=num,
        )

    if temperatures_prediction is None:
        if temperature_range is None:
            temperature_range = [temperature_current - 50, temperature_current + 50]
        if temperature_range[0] < 0:
            temperature_range[0] = 0
        temperatures_prediction = np.linspace(
            temperature_range[0],
            temperature_range[1],
            num=len(pressures_prediction),
        )

    data = []
    for T in temperatures_prediction:
        isotherm_predicted = predict_isotherm_from_enthalpy_clapeyron(
            temperature_prediction=T,
            isotherm=isotherm,
            isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
            branch=branch,
            verbose=False,
        )
        lims = [min(isotherm_predicted.pressure()), max(isotherm_predicted.pressure())]

        loadings = [
            float(isotherm_predicted.loading_at(p)) if lims[0] < p < lims[1] else None
            for p in pressures_prediction
        ]
        data.append(loadings)

    grid = pd.DataFrame(
        data=data,
        index=temperatures_prediction,
        columns=pressures_prediction,
    )

    if verbose:
        import matplotlib.pyplot as plt

        prediction_graphs.plot_predict_isosurface_from_enthalpy(
            grid,
            original_temperature=isotherm.temperature,
            units={
                'temperature': isotherm.temperature_unit,
                'loading': isotherm.loading_unit,
                'material': isotherm.material_unit,
            }
        )
        plt.show()

    return grid


def predict_pressure_raw(
    isosteric_enthalpy: list[float] = None,
    temperature_prediction: float = None,
    temperature_current: float = None,
    pressure_current: list[float] = None,
) -> list[float]:
    r"""
    Utility function for predicting pressures at a given temperature :math:`T_p`,
    :math:`P_p` from isosteric heats of adsorption :math:`\Delta H_{st}`, and
    pressure :math:`P_e` and temperature :math:`T_e` of original experimental
    isotherm. Uses the Clausius-Clapeyron relationship;

    ..math::
        \ln{P_p} = \left[ \Delta H_{st} \frac{T_p - T_e}{R T_p T_e} + \ln{P_e} \right ]_n

    Parameters
    ----------
    enthalpy: list[float]
        Molar isosteric enthalpies of adsorption. Units must be kJ/mol.
    temperature_prediction: float
        Temperature at which to predict an isotherm. Units must be K.
    temperature_current: float
        Temperature of measured isotherm. Units must be K.
    pressure_current: list[float]
        Pressures associated with isosteric enthalpies of adsorption. Units
        should be Pa.

    Returns
    -------
    pressure_prediction: list[float]
        Predicted pressures, in Pa if you've done everything else correctly.

    """
    if len(isosteric_enthalpy) != len(pressure_current):
        raise ParameterError('''enthalpy and P_experiment must be same length.''')

    RTT = R * temperature_current * temperature_prediction
    T_difference = temperature_prediction - temperature_current
    if abs(T_difference) > 50:
        warnings.warn(UserWarning(
            rf'''
            Difference in experimental and prediction temperatures is more
            than 50 K ({T_difference} K). This method may not be reliable
            for predicting a new isotherm.
            '''
        )
        )

    pressure_prediction = [
        np.exp(((1e3 * H * T_difference) / RTT) + np.log(P))
        for H, P in zip(isosteric_enthalpy, pressure_current)
    ]

    return pressure_prediction
