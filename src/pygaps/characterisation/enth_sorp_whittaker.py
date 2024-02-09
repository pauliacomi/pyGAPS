"""Module implementing the Whittaker method for isosteric enthalpy calculations."""

import numpy as np
import scipy.constants
import warnings

import pygaps.modelling as pgm
from pygaps import logger
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.core.adsorbate import Adsorbate
from pygaps.graphing.calc_graphs import isosteric_enthalpy_plot


def enthalpy_sorption_whittaker(
    isotherm: BaseIsotherm,
    branch: str = 'ads',
    model: str = 'Toth',
    loading: list = None,
    verbose: bool = False,
    dographs: bool = True,
    **kwargs,
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
        The model to use to fit the PointIsotherm, must be either one of
        _WHITTAKER_MODELS.
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
        - ``model_isotherm`` (ModelIsotherm): the model isotherm used to
        calculate the enthalpies.

    Raises
    ------
    ParameterError
        When incorrect type of model isotherm is used.

    Notes
    -----

    The Whittaker method, [#]_ sometimes known as a modified Tóth potential uses
    variables derived from fitting of a Toth-like model isotherm to
    derive the isosteric enthalpy of adsorption :math:`\Delta H_{st}`.
    Toth-like isotherms take the general form;

    n(P) = \sum_{i} n_{m_i} \frac{K_i P}{\sqrt[t_i]{1+(K_i P)^{t_i}}}

    And apart from Toth, include the multi- and single site Langmuir model
    (where all t_i are 1), and the chemiphysisorption model.

    The general form of the Whittaker potential is;

    .. math::

        \Delta H_{st} = \Delta \lambda + \Delta H_{vap} + RT

    Where :math:`\Delta \lambda` is the adsorption potential, and
    :math:`\Delta H_{vap}` is the latent heat of the liquid-vapour change at
    equilibrium pressure.

    For loadings below the triple point pressure, :math:`\Delta H_{vap}`  is meaningless. In this case, :math:`\Delta H_{vap}` is estimated as that at the triple point.

    :math:`\Delta \lambda` is determined from the model isotherm parameters as :

    .. math::

        \Delta \lambda = R T \sum_{i} \ln{\left[ P_o K_i \left( \frac{\theta_i^{t_i}}{1 - \theta_i^{t_i}} \right )^{\frac{1-t_i}{t_i}} \right ]}

    Where :math:`P_0` is the saturation pressure, :math:`\theta` is the
    fractional coverage, and :math:`K` is the equilibrium constant. In the case
    that the adsorptive is supercritical, the Dubinin pseudo-saturation pressure is used;
    ..math::
        `p^0 = p_c \left(\frac{T}{T_c}\right)^2`.

    The exponent :math:`t` is not relevent for Langmuir models it reduces to 1. Thus, :math:`\Delta \lambda`
    becomes

    .. math::

        \Delta \lambda = RT \sum_{i} \ln{ \left( \frac{P_0}{K_i} \right) }

    As such, the Whittaker method predicts constant isosteric enthalpies of
    adsorption when Langmuir models are used.

    References
    ----------
    .. [#] "Predicting isosteric heats for gas adsorption.", Peter B.
      Whittaker, Xiaolin Wang, Klaus Regenauer-Lieb and Hui Tong Chua,
      Phys. Chem. Chem. Phys., 15.2, 473-482, (2013)

    """

    if isinstance(isotherm, ModelIsotherm):
        if isotherm.units['pressure_unit'] != 'Pa':
            raise ParameterError('''Model isotherms should be in Pa.''')

    elif isinstance(isotherm, PointIsotherm):
        isotherm.convert_pressure(unit_to='Pa', mode_to='absolute', pseudo=True)
        isotherm.convert_temperature(unit_to='K')

        if model == 'guess':
            model = pgm._WHITTAKER_MODELS

        max_nfev = kwargs.get('max_nfev', None)
        isotherm = pgm.model_iso(
            isotherm,
            branch=branch,
            model=model,
            verbose=verbose,
            optimization_params=dict(max_nfev=max_nfev)
        )

    else:
        raise ParameterError(
            f'''
            Isotherm must be ModelIsotherm or BasIsotherm.
            You have input a {type(isotherm)}.
            '''
        )

    model = isotherm.model.name

    if not pgm.is_model_whittaker(model):
        raise ParameterError(
            f'''
            Whittaker method requires modelling with a Toth-type model, i.e.
            {*pgm._WHITTAKER_MODELS,}
            '''
        )

    if loading is None:
        loading = np.linspace(
            isotherm.model.loading_range[0], isotherm.model.loading_range[1],
            100
        )

    # Local constants and model parameters
    T = isotherm.temperature
    params = isotherm.model.params
    n_m_list = [v for k, v in params.items() if 'n_m' in k]
    K_list = [v for k, v in params.items() if 'K' in k]
    t_list = [v for k, v in params.items() if 't' in k]
    if model.lower() == 'chemiphysisorption':
        t_list.append(1)
    if len(t_list) == 0:
        t_list = [1 for i in range(len(K_list))]

    # Critical, triple and saturation pressure
    p_c = isotherm.adsorbate.p_critical()
    p_t = isotherm.adsorbate.p_triple()
    p_sat = isotherm.adsorbate.saturation_pressure(
        temp=isotherm.temperature,
        pseudo=True,
    )

    pressure = [pressure_at(isotherm, n) for n in loading]
    enthalpy = enthalpy_sorption_whittaker_raw(
        pressure, loading,
        p_sat, p_c, p_t,
        K_list, n_m_list, t_list,
        T,
        isotherm.adsorbate,
    )

    stderr = stderr_estimate(
        count_variables(n_m_list, K_list, t_list),
        isotherm.model.rmse,
        enthalpy
    )

    if verbose and dographs:
        isosteric_enthalpy_plot(
            loading,
            enthalpy,
            stderr,
            isotherm.units,
        )

    return {
        'loading': loading,
        'enthalpy_sorption': enthalpy,
        'model_isotherm': isotherm,
        'std_errs': stderr,
    }


def pressure_at(
    isotherm: BaseIsotherm,
    n: list[float],
):
    """
    Wrapper for `isotherm.pressure_at()` which returns NAN on a
    `CalculationError`.

    Parameters
    ----------
    isotherm: BaseIsotherm
        isotherm to use
    n: float
        Loading from which to derive pressure

    Returns
    ------
    pressure at `n` if possible
    or `np.NAN` if not.
    """
    try:
        return isotherm.pressure_at(n)
    except CalculationError:
        return np.NAN


def count_variables(
    n_m_list: list[float],
    K_list: list[float],
    t_list: list[float],
):
    r"""
    Counts the number of appearances of each of the isotherm model parameters
    in the Whittaker equation.
    Per summation,  for every `i` in;

    .. math::

        \Delta \lambda = R T \sum_{i} \ln{\left[ P_o K_i \left( \frac{\theta_i^{t_i}}{1 - \theta_i^{t_i}} \right )^{\frac{1-t_i}{t_i}} \right ]}

    Thus, `n_m_i` is counted twice, K_i counted once and `t_i` counted four
    times. t_i term is ignored if equal to 1 (as in the chemiphysisorption
    model).

    Parameters
    ---------
    n_m_list: list of floats
    K_list: list of floats
    t_list: list of floats

    Returns
    ------
    Total number of instances of terms.
    """
    t_list = [term for term in t_list if term != 1]
    total = (2 * len(n_m_list)) + len(K_list) + (4 * len(t_list))
    return total


def stderr_estimate(
    n_terms: int,
    rmse: float,
    enthalpy: list[float],
):
    absolute_uncertainty = 0.434 * (np.sqrt(n_terms * (rmse**2)))
    return [abs(absolute_uncertainty) * H for H in enthalpy]


def enthalpy_sorption_whittaker_raw(
    pressure: list[float],
    loading: list[float],
    p_sat: float,
    p_c: float,
    p_t: float,
    K_list: list[float],
    n_m_list: list[float],
    t_list: list[float],
    T: float,
    adsorbate: Adsorbate,
):
    """
    Calculate the isosteric enthalpy of adsorption using model parameters from
    fitting a Toth-like model isotherm via the Whittaker method.

    This is a 'bare-bones' function to calculate isosteric enthalpy which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    pressure: list[float]
        A list of pressures. Must be in Pa.
    loading: list[float] = None,
        Loadings corresponding to above pressures. Units are irrelevant as long
        as they are the same as `n_m`
    p_sat: float = None,
        Saturation pressure of adsorbate at isotherm temperature, `T`. Must be
        in Pa. Tip: if adsorbate is above its critical temperature, you can
        calculate a Dubinin psuedo-saturation pressure using the convenience
        function in the adsorbate class.
    p_c: float = None,
        Critical pressure of adsorbate. Units must be Pa.
    p_t: float = None,
        Triple-point pressure of adsorbate. Units must be Pa.
    K_list: list[float] = None,
        List of equilibrium constants, K from model fitting. Must be derived
        from fitting to model with pressure units of Pa.
    n_m_list: list[float] = None,
        List of monolayer loadings, K from model fitting. Must be derived
        from fitting to model with pressure units of Pa. Must have same units
        as loading.
    t_list: list[float] = None,
        List of exponents, t from model fitting. Must be derived
        from fitting to model with pressure units of Pa.
    T: float = None,
        Temperature of isotherm. Units must be K.
    adsorbate: Adsorbate = None,
        Adsorbate used.

    Returns
    -------
    loading: list[float]
        Loadings as input in function arguments.
    enthalpy: list[float]
        Isosteric enthalpies of adsorption, in kJ/mol.
    """

    if not (len(K_list) == len(n_m_list) == len(t_list)):
        raise ParameterError('''Different length model parameter lists''')

    if len(pressure) != len(loading):
        raise ParameterError(
            '''Loading and pressure lists must be same length!'''
        )

    RT = scipy.constants.R * T
    log_bracket = []
    for K, t, n_m, in zip(K_list, t_list, n_m_list,):
        exponent = (t - 1) / t
        with warnings.catch_warnings(record=True) as w:  # need to log warnings
            warnings.simplefilter("ignore")
            theta_t = [(n / n_m)**t for n in loading]
            theta_bracket = [
                np.log(p_sat * K * ((tt) / (1 - tt))**exponent)
                for tt in theta_t
            ]
            log_bracket.append(theta_bracket)
            if len(w) > 0:
                print(w)

    d_lambda = [RT * sum(x) for x in zip(*log_bracket)]

    h_vap = []
    for p in pressure:
        if np.isnan(p) or p < 0 or p > p_c or p > p_sat:
            h_vap.append(np.NAN)
            continue
        p = max(p, p_t)
        h_vap.append(adsorbate.enthalpy_vaporisation(press=p, ) * 1000)

    enthalpy = [(x + y + RT) / 1000 for x, y in zip(d_lambda, h_vap)]
    return enthalpy
