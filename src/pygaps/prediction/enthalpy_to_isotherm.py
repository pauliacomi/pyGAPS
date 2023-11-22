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
    original_isotherm: PointIsotherm = None,
    enthalpy: list[float] = None,
    T_predict: float = None,
    branch: str ='ads',
    verbose: bool = False,
):

    original_isotherm.convert(
        pressure_unit='Pa', pressure_mode='absolute',
        loading_unit='mol', loading_basis='molar',
        material_unit='kg', material_basis='mass',
    )
    original_isotherm.convert_temperature(unit_to='K')

    T_experiment = original_isotherm.temperature
    P_experiment = original_isotherm.pressure(branch=branch)
    loading = original_isotherm.loading(branch=branch)

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
        pgg.plot_iso([original_isotherm, predicted_isotherm])

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
