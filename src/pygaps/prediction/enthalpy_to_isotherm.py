"""
A module for predicting isotherms at different pressures given a measured
isotherm and calulated isosteric heats of adsorption
"""

import numpy
from scipy import constants

import pygaps.graphing as pgg

from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm

from pygaps import logger
from pygaps.utilities.exceptions import ParameterError

R = constants.gas_constant


def predict_isotherm(
    T_predict: float = None,
    original_isotherm: PointIsotherm = None,
    isosteric_enthalpy_dictionary: dict() = None,
    branch: str ='ads',
    verbose: bool = False,
):
    r"""
    Predicts isotherm at a given temperature :math:`T_p`, from isosteric
    heats of adsorption :math:`\Delta H_{st}`, and pressure :math:`P_e` and
    temperature :math:`T_e` of original experimental isotherm. Uses the
    Clausius-Clapeyron relationship to calculate the predicted pressures;

    ..math::
        \ln{P_p} = \left[ \Delta H_{st} \frac{T_p - T_e}{R T_p T_e} + \ln{P_e} \right ]_n

    Isosteric enthalpy, \Delta H_{st} can be input in the three ways. The order
    is below;
        1. Defined in the other_data dictionary the `original_isotherm` object
        2. As the output of `enth_sorption_whittaker()` or `isosteric_enthalpy`.

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
        isosteric_enthalpy (assumes J/mol) keys. Any dictionary with loading
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
    if original_isotherm is None:
        raise ParameterError(
            f'''
            No original isotherm specified, cannot continue.
            '''
        )

    if (
        isosteric_enthalpy_dictionary is None and
        'enthalpy' not in original_isotherm.other_keys
    ):
        raise ParameterError(
            '''
            There is no enthalpy specified. This can be specified by passing
            a dictionary of 'loading' and 'isosteric_enthalpy', or by passing
            an isotherm with enthalpy in its 'other_keys'

            '''
        )

    original_isotherm.convert(
        pressure_unit='Pa', pressure_mode='absolute',
        loading_unit='mol', loading_basis='molar',
        material_unit='kg', material_basis='mass',
    )
    original_isotherm.convert_temperature(unit_to='K')
    T_experiment = original_isotherm.temperature

    if 'enthalpy' in original_isotherm.other_keys:
        enthalpy = original_isotherm.other_data(key='enthalpy', branch=branch)
        loading = original_isotherm.loading()
        if verbose:
            logger.info(
                f"""
                Enthalpy retrieved from original_isotherm.other_keys.
                """
            )

    elif isosteric_enthalpy_dictionary is not None:
        if not all(
            key in isosteric_enthalpy_dictionary
            for key in ['loading', 'enthalpy_sorption']
        ):
            raise ParameterError(
                f'''
                You have specified a isosteric_enthalpy_dictionary as input,
                but it doesn't contain the right data.
                '''
            )

        enthalpy = isosteric_enthalpy_dictionary['enthalpy_sorption']
        loading = isosteric_enthalpy_dictionary['loading']

        if verbose:
            logger.info(
                f"""
                Using enthalpy from isosteric_enthalpy_dictionary.
                """
            )

    if verbose:
        logger.info(
            f"""
            Min={min(enthalpy)}\tmax={max(enthalpy)}\tlength={len(enthalpy)}
            """
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

    P_predict = predict_pressure_raw(
        T_experiment, T_predict,
        enthalpy,
        P_experiment
    )

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

    if verbose:
        import matplotlib.pyplots as plt
        fig, (isos_ax, enthalpy_ax) = plt.subplots(1, 2)
        pgg.plot_iso(
            [original_isotherm, predicted_isotherm],
            ax=isos_ax
        )
        pgg.isosteric_enthalpy_plot(
            loading, enthalpy/1000,
            std_err = [0 for n in loading],
            units=predicted_isotherm.units,
            ax=enthalpy_ax,
        )

    return predicted_isotherm


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
        Molar isosteric enthalpies of adsorption. Units must be J/mol.
    P_predicted: list[float]
        Pressures associated with isosteric enthalpies of adsorption. Units
        should be Pa.

    Returns
    -------
    P_predicted: list[float]
        Predicted pressures, in Pa if you've done everything else correctly.

    """
    if len(enthalpy) != len(P_experiment):
        raise ParameterError('''enthalpy and P_experiment must be same length.''')

    RTT = R * T_experiment * T_predict
    T_difference = T_predict - T_experiment
    if T_difference > 50:
        logger.warning(
            f'''
            Difference in experimental and prediction temperatures is more than
            50 K ({T_difference} K). This method may not be reliable for
            predicting a new isotherm.
            '''
        )

    P_predict = [
        numpy.exp(((H*T_difference)/RTT) + numpy.log(P)) for
        H, P in zip(enthalpy, P_experiment)
    ]

    return P_predict
