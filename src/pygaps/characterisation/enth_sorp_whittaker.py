"""Module implementing the Whittaker method for isosteric enthalpy calculations."""

import numpy as np
import scipy.constants

import pygaps.modelling as pgm
from pygaps import logger
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


def enthalpy_sorption_whittaker(
    isotherm: "BaseIsotherm",
    model: str = 'Toth',
    loading: list = None,
    verbose: bool = False,
):
    r"""

    Calculate the isosteric heat of adsorption, `\Delta H_{st}` using a single
    isotherm via the Whittaker method. Pass either a ModelIsotherm of a suitable
    model (Toth or Langmuir) or the model itself. Parameters of the model fit
    are then used to determine :math:`\Delta H_{st}`.

    Parameters
    ----------
    isotherm : BaseIsotherm
        The PointIsotherm or ModelIsotherm to be used. If ModelIsotherm, units must be in Pascal
    model : str
        The model to use to fit the PointIsotherm, must be either 'Langmuir' or 'Toth'.
    loading : list[float]
        The loadings for which to calculate the isosteric heat of adsorption.
    verbose : bool
        Whether to print out extra information and generate a graph.

    Returns
    -------
    result_dict : dict
        A dictionary with the isosteric enthalpies per loading, with the form:

        - ``enthalpy_sorption`` (array) : the isosteric enthalpy of adsorption in kJ/mol
        - ``loading`` (array) : the loading for each point of the isosteric
          enthalpy, in mmol/g

    Raises
    ------
    ParameterError
        When incorrect type of model isotherm is used.

    Notes
    -----

    The Whittaker method, [#]_ sometimes known as a modified Tóth potential uses
    variables derived from fitting of a model isotherm (Langmuir or Toth) to
    derive the isosteric enthalpy of adsorption :math:`\Delta H_{st}`. The general form
    of the equation is;

    .. math::

        \Delta H_{st} = \Delta \lambda + \H_{vap} + RT

    Where :math:`\Delta \lambda` is the adsorption potential, and
    :math:`\H_{vap}` is the latent heat of the liquid-vapour change at
    equilibrium pressure.

    For loadings below the triple point pressure, :math:`\H_{vap}` is meaningless.
    In this case, :math:`\H_{vap}` is estimated as that at the triple point.

    Whittaker determined :math:`\Delta \lambda` as:

    .. math::

        \Delta \lambda = RT \ln{\left[\left(\frac{p^0}{b^{1/t}}\right)\left(\frac{\Theta^{t}}{1-\Theta^{t}}\right) \right]}

    Where :math:`p^0` is the saturation pressure, :math:`\Theta` is the
    fractional coverage, and :math:`b` is derived from the equilibrium constant,
    :math:`K` as :math:`b = \frac{1}{K^t}`. In the case that the adsorptive is
    above is supercritical, the pseudo saturation pressure is used;
    :math:`p^0 = p_c \left(\frac{T}{T_c}\right)^2`.

    The exponent :math:`t` is only relevant to the Toth version of the method,
    as for the Langmuir model it reduces to 1. Thus, :math:`\Delta \lambda`
    becomes

    .. math::

        \Delta \lambda = RT \ln{ \left( \frac{p^0}{b} \right) }

    References
    ----------
    .. [#] "Predicting isosteric heats for gas adsorption.", Peter B.
      Whittaker, Xiaolin Wang, Klaus Regenauer-Lieb and Hui Tong Chua,
      Phys. Chem. Chem. Phys., 15.2, 473-482, (2013)

    """

    if isinstance(isotherm, ModelIsotherm):
        if isotherm.units['pressure_unit'] != 'Pa':
            raise ParameterError('''Model isotherms should be in Pa.''')
        model = isotherm.model.name
    elif isinstance(isotherm, PointIsotherm):
        isotherm.convert_pressure(unit_to='Pa')
        isotherm = pgm.model_iso(
            isotherm,
            branch='ads',
            model=model,
            verbose=verbose,
        )

    if model.lower() not in ['langmuir', 'toth']:
        raise ParameterError('''Whittaker method requires modelling with either Langmuir or Toth''')

    if loading is None:
        loading = np.linspace(isotherm.model.loading_range[0], isotherm.model.loading_range[1], 100)

    # Local constants and model parameters
    T = isotherm.temperature
    RT = scipy.constants.R * T
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
            f"{isotherm.adsorbate} does not have a saturation pressure "
            f"at {isotherm.temperature} K. Calculating pseudo-saturation "
            f"pressure..."
        )
        T_c = isotherm.adsorbate.t_critical()
        p_sat = p_c * ((T / T_c)**2)

    loading_final = []
    whittaker_enth = []

    first_bracket = p_sat / (b**(1 / t))  # don't need to calculate every time
    for n in loading:
        if n == 0:
            continue

        p = isotherm.pressure_at(n, pressure_unit='Pa')
        # check that it is possible to calculate h_vap
        if np.isnan(p) or p < 0 or p > p_c or p > p_sat:
            continue

        # Cap pressure for h_vap determination to the triple point pressure
        p = max(p, p_t)

        # equation requires enthalpies in J
        h_vap = isotherm.adsorbate.enthalpy_vaporisation(press=p, ) * 1000

        theta = n / n_m  # second bracket of d_lambda
        theta_t = theta**t
        second_bracket = (theta_t / (1 - theta_t))**((t - 1) / t)
        d_lambda = RT * np.log(first_bracket * second_bracket)

        h_st = d_lambda + h_vap + RT

        loading_final.append(n)
        whittaker_enth.append(h_st / 1000)  # return enthalpies to kJ

    if verbose:
        from pygaps.graphing.calc_graphs import isosteric_enthalpy_plot
        isosteric_enthalpy_plot(
            loading_final,
            whittaker_enth,
            [0 for n in loading_final],
            isotherm.units,
        )

    return {
        'loading': loading_final,
        'enthalpy_sorption': whittaker_enth,
        'model_params': isotherm.model.params,
    }


def enthalpy_sorption_whittaker_raw(
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
