"""
A module for predicting isotherms at different pressures given a measured
isotherm and calculated isosteric heats of adsorption
"""

import numpy as np
import pandas as pd
from scipy import constants

import pygaps.graphing as pgg
from pygaps import logger
from pygaps.characterisation import enthalpy_sorption_whittaker
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import ParameterError

R = constants.gas_constant

# TODO decide if we need to change PointIsotherm object to include enthalpies


def isotherm_to_predicted(
    T_predict: list[float],
    original_isotherm: PointIsotherm,
    model: 'str',
    loading: list[float] = None,
    branch: str = 'ads',
    verbose: bool = False,
    **kwargs,
):
    """
    Directly predicts an isotherm at a different temperature, based on
    modelling with a Whittaker-consistent (Toth-type) model. This is a wrapper
    function that uses `characterisation.enthalpy_sorption_whittaker()` and
    `from_whittaker_and_isotherm()` functions.

    Parameters
    ---------
    T_predict: float
        The temperature at which to predict the isotherm. Units are K.
    original_isotherm: PointIsotherm
        The experimental isotherm that has been measured.
    model: 'str'
        The model to use to fit the PointIsotherm, must be one of
        `_WHITTAKER_MODELS`. If set to 'guess', will attempt fitting with all of
        the `_WHITTAKER_MODELS`, and selects best fit.
    loading: list[float], optional
        The loadings for which to calculate the isosteric heat of adsorption
        with the `enthalpy_sorption_whittaker()` function.
    branch: str,  optional
        Branch of the isotherm to use, and thus to generate predicted isotherm
        with.
        Defaults to adsorption.
    verbose: bool, optional
        Whether to print out extra information and generate a graph.
    **kwargs

    Returns
    ------
    predicted_isotherm: PointIsotherm
        The isotherm predicted from the above parameters. Pressure in Pa,
        loading in mol/kg.
    whittaker_dictionary: dict
        A dictionary with the isosteric enthalpies per loading, with the form:

        - ``enthalpy_sorption`` (array) : the isosteric enthalpy of adsorption in kJ/mol
        - ``loading`` (array) : the loading for each point of the isosteric
          enthalpy, in mmol/g
        - ``model_isotherm`` (ModelIsotherm): the model isotherm used to
        calculate the enthalpies.
    """
    if loading is None:
        loading = original_isotherm.loading(branch=branch)

    whittaker_dictionary = enthalpy_sorption_whittaker(
        original_isotherm,
        model=model,
        loading=loading,
        verbose=verbose,
        dographs=False,
        **kwargs,
    )

    predicted_isotherm = enthalpy_and_isotherm_to_predicted(
        T_predict,
        original_isotherm,
        isosteric_enthalpy_dictionary=whittaker_dictionary,
        branch=branch,
        verbose=verbose,
        dographs=False,
    )

    if verbose:
        pgg.prediction_graphs.plot_isothermfit_enthalpy_prediction(
            original_isotherm,
            whittaker_dictionary['model_isotherm'],
            predicted_isotherm,
            loading,
            enthalpy=whittaker_dictionary['enthalpy_sorption'],
            branch=branch,
        )

    return predicted_isotherm, whittaker_dictionary


def enthalpy_and_isotherm_to_predicted(
    T_predict: float,
    original_isotherm: PointIsotherm,
    isosteric_enthalpy_dictionary: dict() = None,
    branch: str = 'ads',
    verbose: bool = False,
    dographs: bool = True,
):
    r"""
    Predicts isotherm at a given temperature :math:`T_p`, from isosteric
    heats of adsorption :math:`\Delta H_{st}`, and pressure :math:`P_e` and
    temperature :math:`T_e` of original experimental isotherm. Uses the
    Clausius-Clapeyron relationship to calculate the predicted pressures;

    ..math::
        \ln{P_p} = \left[ \Delta H_{st} \frac{T_p - T_e}{R T_p T_e} + \ln{P_e} \right ]_n

    Isosteric enthalpy, \Delta H_{st} can be input in two ways. The order
    of preference is as below;
        1. Defined in the other_data dictionary the `original_isotherm` object
        2. As the output of `enth_sorption_whittaker()` or `isosteric_enthalpy`
        using the `isosteric_enthalpy_dictionary` parameter.

    With options 1, it is important to ensure that the enthalpies
    actually correspond to loading points.

    Parameters
    ----------
    T_predict: float
        The temperature at which to predict the isotherm. Units are K.
    original_isotherm: PointIsotherm
        The experimental isotherm that has been measured.
        If it has an 'enthalpy' key in other_data, this will be used as the
        isosteric enthalpies with which to perform the calculation. Please
        ensure that these actually correspond to the loadings in the isotherm.
    isosteric_enthalpy_dictionary: dict, optional
        You can input the output of `enthalpy_sorption_whittaker()` or
        `isosteric_enthalpy` here. The function will then use the loading and
        isosteric_enthalpy (assumes kJ/mol) keys. Any dictionary with loading
        and enthalpy keys should work.  Only used if enthalpy is not defined
        in original_isotherm.other_data.
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
    if (isosteric_enthalpy_dictionary is None and 'enthalpy' not in original_isotherm.other_keys):
        raise ParameterError(
            '''
            There is no enthalpy specified. This can be specified by passing
            a dictionary of 'loading' and 'isosteric_enthalpy', or by passing
            an isotherm with enthalpy in its 'other_keys'
            '''
        )

    original_isotherm.convert(
        pressure_unit='Pa',
        pressure_mode='absolute',
        loading_unit='mol',
        loading_basis='molar',
        material_unit='kg',
        material_basis='mass',
    )
    original_isotherm.convert_temperature(unit_to='K')
    T_experiment = original_isotherm.temperature

    if 'enthalpy' in original_isotherm.other_keys:
        enthalpy = original_isotherm.other_data(key='enthalpy', branch=branch)
        loading = original_isotherm.loading()
        if verbose:
            logger.info(
                """
                Enthalpy retrieved from original_isotherm.other_keys.
                """
            )

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

    P_experiment = original_isotherm.pressure_at(
        loading,
        pressure_unit='Pa',
        interp_fill='extrapolate',
    )

    if not (len(loading) == len(P_experiment) == len(enthalpy)):
        raise ParameterError(
            f'''
            Loading, P_experiment, and enthalpies are different lengths.
            Check your data.
            Have you used the right branch ({branch})?
            '''
        )

    P_predict = predict_pressure_raw(T_experiment, T_predict, enthalpy, P_experiment)

    predicted_isotherm = PointIsotherm(
        pressure=P_predict,
        loading=loading,
        material=original_isotherm.material,
        adsorbate=str(original_isotherm.adsorbate),
        temperature=T_predict,
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
        pgg.prediction_graphs.plot_enthalpy_prediction(
            original_isotherm,
            predicted_isotherm,
            loading,
            enthalpy,
            branch=branch,
        )

    return predicted_isotherm


def predict_adsorption_surface(
    original_isotherm: PointIsotherm,
    isosteric_enthalpy_dictionary: dict = None,
    temperatures: list[float] = None,
    pressures: list[float] = None,
    num: int = None,
    T_range: tuple[float, float] = None,
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
    original_isotherm: PointIsotherm
        The experimental isotherm that has been measured.
        If it has an 'enthalpy' key in other_data, this will be used as the
        isosteric enthalpies with which to perform the calculation. Please
        ensure that these actually correspond to the loadings in the isotherm.
    isosteric_enthalpy_dictionary: dict, optional
        You can input the output of `enthalpy_sorption_whittaker()` or
        `isosteric_enthalpy` here. The function will then use the loading and
        isosteric_enthalpy (assumes kJ/mol) keys. Any dictionary with loading
        and enthalpy keys should work.  Only used if enthalpy is not defined
        in original_isotherm.other_data.
    temperatures: list[float], optional
        The temperatures (x-axis) of the resultant grid. If None, will use an
        array +/- 50 K from the temperature of `original_isotherm`. Number of
        steps defaults to be that of `pressures` array.
    pressures: list[float], optional
        The pressures (y-axis) of the resultant grid. If None, will use
        pressures in range of original isotherm, distributed linearly. Number
        of steps is determined by `num` parameter.
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
    original_isotherm.convert(
        pressure_unit='Pa',
        pressure_mode='absolute',
    )
    T_experiment = original_isotherm.temperature

    if branch is None:
        raise ParameterError(
            """
            Functionality for both branches not completed yet. Please use 'ads'
            or 'des'.
            """
        )

    if num is None:
        num = 100

    if pressures is None:
        pressures = np.linspace(
            min(original_isotherm.pressure(branch=branch)),
            max(original_isotherm.pressure(branch=branch)),
            num=num,
        )

    if temperatures is None:
        if T_range is None:
            T_range = [T_experiment - 50, T_experiment + 50]
        if T_range[0] < 0:
            T_range[0] = 0
        temperatures = np.linspace(
            T_range[0],
            T_range[1],
            num=len(pressures),
        )

    data = []
    for T in temperatures:
        predicted_isotherm = enthalpy_and_isotherm_to_predicted(
            T_predict=T,
            original_isotherm=original_isotherm,
            isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
            branch=branch,
            verbose=False,
        )
        lims = [min(predicted_isotherm.pressure()), max(predicted_isotherm.pressure())]

        loadings = [
            float(predicted_isotherm.loading_at(p)) if lims[0] < p < lims[1] else None
            for p in pressures
        ]
        data.append(loadings)

    grid = pd.DataFrame(
        data=data,
        index=temperatures,
        columns=pressures,
    )

    if verbose:
        import matplotlib.pyplot as plt

        from pygaps.graphing import prediction_graphs
        prediction_graphs.plot_adsorption_heatmap(
            grid,
            original_temperature=original_isotherm.temperature,
            units={
                'temperature': original_isotherm.temperature_unit,
                'loading': original_isotherm.loading_unit,
                'material': original_isotherm.material_unit,
            }
        )
        plt.show()

    return grid


def predict_pressure_raw(
    T_experiment: float = None,
    T_predict: float = None,
    enthalpy: list[float] = None,
    P_experiment: list[float] = None,
):
    r"""
    Utility function for predicting pressures at a given temperature :math:`T_p`,
    :math:`P_p` from isosteric heats of adsorption :math:`\Delta H_{st}`, and
    pressure :math:`P_e` and temperature :math:`T_e` of original experimental
    isotherm. Uses the Clausius-Clapeyron relationship;

    ..math::
        \ln{P_p} = \left[ \Delta H_{st} \frac{T_p - T_e}{R T_p T_e} + \ln{P_e} \right ]_n

    Parameters
    ----------
    T_experiment: float
        Temperature of measured isotherm. Units must be K.
    T_predicted: float
        Temperature at which to predict an isotherm. Units must be K.
    enthalpy: list[float]
        Molar isosteric enthalpies of adsorption. Units must be kJ/mol.
    P_experiment: list[float]
        Pressures associated with isosteric enthalpies of adsorption. Units
        should be Pa.

    Returns
    -------
    P_predict: list[float]
        Predicted pressures, in Pa if you've done everything else correctly.

    """
    if len(enthalpy) != len(P_experiment):
        raise ParameterError('''enthalpy and P_experiment must be same length.''')

    RTT = R * T_experiment * T_predict
    T_difference = T_predict - T_experiment
    if T_difference > 50:
        logger.warning(
            rf'''
            Difference in experimental and prediction temperatures is more
            than 50 K ({T_difference} K). This method may not be reliable
            for predicting a new isotherm.
            '''
        )

    P_predict = [
        np.exp(((1e3 * H * T_difference) / RTT)
               + np.log(P))
        for H, P in zip(enthalpy, P_experiment)
    ]

    return P_predict
