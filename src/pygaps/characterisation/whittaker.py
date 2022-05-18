import numpy as np
import scipy.constants
from CoolProp.CoolProp import PropsSI
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import CalculationError


def heat_vap(
    p: float,
    sorptive: str,
):
    r"""
    Determines the enthalpy of vaporsiation, :math:`\lambda_{p}` for a
    specie at a given pressure.

    Parameters
    ----------
    p : float
    Pressure to calculate at
    sorptive : string
        Specie in question

    Returns
    -------
    lambda_p : float
        Enthalpy of vaporisation
    """
    lambda_V = PropsSI('HMOLAR', 'P',
                       p, 'Q', 1,
                       sorptive)
    lambda_L = PropsSI('HMOLAR', 'P',
                       p, 'Q', 0,
                       sorptive)
    lambda_p = lambda_V - lambda_L

    return lambda_p


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

def whittaker(
    isotherm: "ModelIsotherm",
    loading: list = None,
):
    r"""

    Calculate the isosteric heat of adsorption using a single isotherm via the
    Whittaker method.

    Parameters
    ----------
    isotherm : ModelIsotherm
        The model isotherm used. Must be either Toth or Langmuir
    p_sat : float
        The saturation pressure of the sorptive, either 'real' or derived from
        pseudo-saturation
    loading : list[float]
        The loadings for which to calculate the isosteric heat of adsorption

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

    The Whittaker method, sometimes known as the Toth potential uses variables
    derived from fitting of a model isotherm (Langmuir or Toth) to derive the
    isosteric enthalpy of adsorption :math:`q_{st}`. The general form of the
    equation is;

    .. math::
        q_{st} = \Delta \lambda + \lambda_{p} + RT

    Where :math:`\Delta \lambda` is the adsorption potential, and
    :math:`\lambda_{p} is the latent heat of the liquid-vapour change at
    equilibrium pressure.

    Whittaker determined :math:`\Delta \lambda` as;

    .. math::
        \Delta \lambda = RT\ln{\left[\left(\frac{p^{sat}}{b^{\frac{1}{t}}\right)\left(\frac{\Theta^{t}}{1-\Theta^{t}}\right) \right]}

    Where :math:`p^{sat}` is the saturation pressure, :math:`\Theta` is the
    fractional coverage, and :math:`b` is derived from the equilbrium constant,
    :math:`K` as :math:`b = \frac{1}{K^t}`. In the case that the adsorptive is
    above is supercrictial, the pseudo saturation pressure is used;
    :math:`p^{sat} = p_c \left(\frac{T}{T_c}\right)^2`. 

    The exponent :math:`t` is only relevant to the Toth version of the method,
    as for the Langmuir model it reduces to 1. Thus, :math:`\Delta \lambda`
    becomes

    .. math::
        \Delta \lambda = RT\ln{\left(\frac{p^{sat}}{b^{\frac{1}{t}}\right)
    """

    if isotherm.model.name not in ['Langmuir', 'Toth']:
        raise ParameterError('''Whittaker method requires either a Langmuir or Toth
                         model isotherm''')
    R = scipy.constants.R
    n_m = isotherm.model.params['n_m']
    K = isotherm.model.params['K']
    T = isotherm.temperature
    try:
        p_sat = isotherm.adsorbate.saturation_pressure(temp=298, unit='kPa')
    except CalculationError:
        print(f"{isotherm.adsorbate} does not have saturation pressure "
              f"at {isotherm.temperature} K. Calculating psduedo-saturation "
              f"pressure...")
        p_c = isotherm.adsorbate.p_critical
        T_c = isotherm.adsorbate.t_critical
        p_sat = p_c * ((T / T_c)**2)

    if isotherm.model.name == 'Langmuir':
        t = 1
    else:
        t = isotherm.model.params['t']  # equivalent to m in Whittaker

        b = 1 / (K**t)

    whittaker_enth = []

    first_bracket = p_sat / (b**(1 / t))  # don't need to calculate every time
    for n in loading:
        p = isotherm.pressure_at(n) * 1000 
        sorptive = str(isotherm.adsorbate.backend_name)

        # check that it is possible to calculate lambda_p
        if p < p_c or p > isotherm.adsorbate.p_triple or np.isnan(p):
            loading = np.delete(loading, np.where(loading == n))
            pass

        else:
            lambda_p = heat_vap(p, sorptive)

            theta = n / n_m  # second bracket of d_lambda
            theta_t = theta**t
            second_bracket = (theta_t / (1 - theta_t))**((t - 1) / t)
            d_lambda = R * T * np.log(first_bracket * second_bracket)

            h_st = d_lambda + lambda_p + (R * T)

            whittaker_enth.append(h_st)

    return {
        'loading': loading,
        'whittaker_enthalpy': whittaker_enth,
    }
