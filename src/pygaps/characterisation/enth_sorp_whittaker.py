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

_WHITTAKER_MODELS = [
    'langmuir', 'dslangmuir', 'tslangmuir',
    'toth', 'dstoth', 'chemiphysisorption',
]


def pressure_at(isotherm, n):
    try:
        return isotherm.pressure_at(n)
    except CalculationError:
        return np.NAN


def enthalpy_sorption_whittaker(
    isotherm: "BaseIsotherm",
    model: str = 'Toth',
    loading: list = None,
    verbose: bool = False,
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

        \Delta H_{st} = \Delta \lambda + \Delta H_{vap} + RT

    Where :math:`\Delta \lambda` is the adsorption potential, and
    :math:`\Delta H_{vap}` is the latent heat of the liquid-vapour change at
    equilibrium pressure.

    For loadings below the triple point pressure, :math:`\Delta H_{vap}` is meaningless.
    In this case, :math:`\Delta H_{vap}` is estimated as that at the triple point.

    Whittaker determined :math:`\Delta \lambda` as:

    .. math::

        \Delta \lambda = RT
        \ln{\left[\left(\frac{p^0}{b^{1/t}}\right)\left(\frac{\theta^{t}}{1-\theta^{t}}\right)^{\frac{1-t}{t}} \right]}

    Where :math:`p^0` is the saturation pressure, :math:`\theta` is the
    fractional coverage, and :math:`b` is derived from the equilibrium constant,
    :math:`K` as :math:`b = \frac{1}{K^t}`. In the case that the adsorptive is
    supercritical, the pseudo saturation pressure is used;
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
        max_nfev = kwargs.get('max_nfev', None)
        if model == 'guess':
            isotherm = pgm.model_iso(
                isotherm,
                branch='ads',
                model=_WHITTAKER_MODELS,
                verbose=verbose,
                optimization_params=dict(max_nfev=max_nfev)
            )
            model = isotherm.model.name
        else:
            isotherm = pgm.model_iso(
                isotherm,
                branch='ads',
                model=model,
                verbose=verbose,
                optimization_params=dict(max_nfev=max_nfev)
            )

    if model.lower() not in _WHITTAKER_MODELS:
        raise ParameterError(
            '''Whittaker method requires modelling with one of ''',
            *_WHITTAKER_MODELS
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
    if model in ['dstoth', 'toth', 'chemiphysisorption']:
        t_list = [v for k, v in params.items() if 't' in k]
        if model == 'chemiphysisorption':
            t_list.append(1)
    else:
        t_list = [1 for i in range(len(K_list))]

    # Critical, triple and saturation pressure
    p_c = isotherm.adsorbate.p_critical()
    p_t = isotherm.adsorbate.p_triple()
    p_sat = isotherm.adsorbate.saturation_pressure(
        temp=isotherm.temperature,
        pseudo=True,
    )

    pressure = [pressure_at(isotherm, n) for n in loading]
    loading, enthalpy = enthalpy_sorption_whittaker_raw(
        pressure, loading,
        p_sat, p_c, p_t,
        K_list, n_m_list, t_list,
        T,
        isotherm.adsorbate,
    )

    if verbose:
        from pygaps.graphing.calc_graphs import isosteric_enthalpy_plot
        isosteric_enthalpy_plot(
            loading,
            enthalpy,
            [0 for n in loading],
            isotherm.units,
        )

    return {
        'loading': loading,
        'enthalpy_sorption': enthalpy,
        'model_isotherm': isotherm,
    }


def enthalpy_sorption_whittaker_raw(
    pressure: list[float] = None,
    loading: list[float] = None,
    p_sat: float = None,
    p_c: float = None,
    p_t: float = None,
    K_list: list[float] = None,
    n_m_list: list[float] = None,
    t_list: list[float] = None,
    T: float = None,
    adsorbate: Adsorbate = None,
):
    """
    """

    if not (
        len(K_list) == len(n_m_list) == len(t_list)
    ):
        raise ParameterError('''Different length parameter lists''')

    RT = scipy.constants.R * T
    log_bracket = []
    for K, t, n_m, in zip(K_list, t_list, n_m_list,):
        with warnings.catch_warnings(): # need to log warnings
            warnings.simplefilter("ignore")
            theta_t = [(n / n_m)**t for n in loading]
            theta_bracket = [
                np.log(p_sat * K * ((tt) / (1-tt))**((t-1)/t))
                for tt in theta_t
            ]
            log_bracket.append(theta_bracket)
    d_lambda = [RT * sum(x) for x in zip(*log_bracket)]

    h_vap = []
    for p in pressure:
        if np.isnan(p) or p < 0 or p > p_c or p > p_sat:
            h_vap.append(np.NAN)
            continue
        p = max(p, p_t)
        h_vap.append(adsorbate.enthalpy_vaporisation(press=p, ) * 1000)

    enthalpy = [(x + y + RT) / 1000 for x, y in zip(d_lambda, h_vap)]
    return loading, enthalpy
