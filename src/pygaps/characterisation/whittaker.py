"""Module implementing the Whittaker method for isosteric enthalpy calculations."""

import numpy as np
import scipy.constants

from pygaps import logger
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


def whittaker_enthalpy(
    isotherm: "ModelIsotherm",
    loading: list = None,
):
    r"""

    Calculate the isosteric heat of adsorption using a single isotherm via the
    Whittaker method.

    Parameters
    ----------
    isotherm : ModelIsotherm
        The model isotherm used. Must be either Toth or Langmuir.
    loading : list[float]
        The loadings for which to calculate the isosteric heat of adsorption.

    Returns
    -------
    df : DataFrame
        DataFrame of isosteric heat of adsorption at input loadings.

    Raises
    ------
    ParameterError
        When incorrect type of model isotherm is used.

    Notes
    -----

    The Whittaker method, [#]_ sometimes known as the Toth potential uses
    variables derived from fitting of a model isotherm (Langmuir or Toth) to
    derive the isosteric enthalpy of adsorption :math:`q_{st}`. The general form
    of the equation is;

    .. math::
        q_{st} = \Delta \lambda + \lambda_{p} + RT

    Where :math:`\Delta \lambda` is the adsorption potential, and
    :math:`\lambda_{p} is the latent heat of the liquid-vapour change at
    equilibrium pressure.

    Whittaker determined :math:`\Delta \lambda` as;

    .. math::
        \Delta \lambda = RT\ln{\left[\left(\frac{p^{sat}}{b^{\frac{1}{t}}\right)\left(\frac{\Theta^{t}}{1-\Theta^{t}}\right) \right]}

    Where :math:`p^{sat}` is the saturation pressure, :math:`\Theta` is the
    fractional coverage, and :math:`b` is derived from the equilibrium constant,
    :math:`K` as :math:`b = \frac{1}{K^t}`. In the case that the adsorptive is
    above is supercritical, the pseudo saturation pressure is used;
<<<<<<< HEAD
    :math:`p^{sat} = p_c \left(\frac{T}{T_c}\right)^2.
=======
    :math:`p^{sat} = p_c \left(\frac{T}{T_c}\right)^2`.
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533

    The exponent :math:`t` is only relevant to the Toth version of the method,
    as for the Langmuir model it reduces to 1. Thus, :math:`\Delta \lambda`
    becomes

    .. math::
        \Delta \lambda = RT\ln{\left(\frac{p^{sat}}{b^{\frac{1}{t}}\right)

    References
    ----------
    .. [#] REFERENCE HERE

    """

    if isotherm.model.name not in ['Langmuir', 'Toth']:
        raise ParameterError(
            '''Whittaker method requires either a Langmuir or Toth
                         model isotherm'''
        )

    # Local constants and model parameters
    R = scipy.constants.R
    T = isotherm.temperature
    RT = R * T
    n_m = isotherm.model.params['n_m']
    K = isotherm.model.params['K']
    if isotherm.model.name == 'Langmuir':
        t = 1
    else:
        t = isotherm.model.params['t']  # equivalent to m in Whittaker
    b = 1 / (K**t)

    # Critical, triple and saturation pressure
    p_c = isotherm.adsorbate.p_critical()
    p_t = isotherm.adsorbate.p_triple()
    try:
        p_sat = isotherm.adsorbate.saturation_pressure(temp=isotherm.temperature)
    except CalculationError:
        logger.warning(
            f"{isotherm.adsorbate} does not have saturation pressure "
            f"at {isotherm.temperature} K. Calculating pseudo-saturation "
            f"pressure..."
        )
<<<<<<< HEAD
        T_c = isotherm.adsorbate.backend.t_critical()
=======
        T_c = isotherm.adsorbate.t_critical()
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533
        p_sat = p_c * ((T / T_c)**2)

    loading_final = []
    whittaker_enth = []

    first_bracket = p_sat / (b**(1 / t))  # don't need to calculate every time
    for n in loading:
<<<<<<< HEAD
        p = isotherm.pressure_at(n,
                                 pressure_unit='bar')  # TODO what units are we considering here?
=======
        p = isotherm.pressure_at(n) * 1000  # TODO what units are we considering here?
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533

        # check that it is possible to calculate lambda_p
        if p < p_c or p > p_t or np.isnan(p):
            continue

        lambda_p = isotherm.adsorbate.enthalpy_vaporisation(press=p)

        theta = n / n_m  # second bracket of d_lambda
        theta_t = theta**t
        second_bracket = (theta_t / (1 - theta_t))**((t - 1) / t)
        d_lambda = RT * np.log(first_bracket * second_bracket)

        h_st = d_lambda + lambda_p + RT

        loading_final.append(n)
        whittaker_enth.append(h_st)

    return {
        'loading': loading_final,
        'whittaker_enthalpy': whittaker_enth,
    }


def whittaker_raw(
    p: float = None,
    p_sat: float = None,
    K: float = None,
    n: float = None,
    n_m: float = None,
):
    """
    not using yet, placeholder for function that may be helpful for DSLangmuir
    version.
    """
    pass