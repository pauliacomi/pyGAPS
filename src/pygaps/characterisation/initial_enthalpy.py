"""Module calculating the initial enthalpy of adsorption."""

import logging

logger = logging.getLogger('pygaps')
import warnings

import numpy

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import initial_enthalpy_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError


def initial_enthalpy_comp(
    isotherm, enthalpy_key, branch='ads', verbose=False, **param_guess
):
    r"""
    Given an isotherm with previous differential adsorption enthalpy data,
    calculate the enthalpy of adsorption at zero loading with a fitting
    method with separate contributions:

        * A constant contribution
        * An 'active site' decaying exponential contribution
        * A power contribution to model adsorbate-adsorbate attraction
        * A power contribution to model adsorbate-adsorbate repulsion

    It can be represented by the following equation:

    .. math::

        \Delta H(n) = K_{const}+\frac{K_{exp}}{1+\exp(E*(n-n_{loc})))}+K_{pa}*n^{p_a}+K_{pr}*n^{p_r}

    Enthalpy data should be in KJ/mmol and positive.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to use for the calculation.
    enthalpy_key : str
        The column which stores the enthalpy data.
    branch : str
        The isotherm branch to use for the calculation. Default is adsorption branch.
    verbose : bool, optional
        Whether to print out extra information.

    Other Parameters
    ----------------
    const_min : float
        Lower limit for constant contribution.
    const_max : float
        Upper limit for constant contribution.

    exp_min : float
        Lower limit for exponential contribution.
    exp_max : float
        Upper limit for exponential contribution.
    preexp_min : float
        Lower limit for exponential contribution coefficient.
    preexp_max : float
        Upper limit for exponential contribution coefficient.
    exploc_min : float
        Lower limit for location of inflexion point.
    exploc_max : float
        Upper limit for location of inflexion point.

    powa_min : float
        Lower limit for power attraction contribution.
    powa_max : float
        Upper limit for power attraction contribution.
    prepowa_min : float
        Lower limit for power attraction contribution coefficient.
    prepowa_max : float
        Upper limit for power attraction contribution coefficient.
    powr_min : float
        Lower limit for power repulsion contribution.
    powr_max : float
        Upper limit for power repulsion contribution.
    prepowr_min : float
        Lower limit for power repulsion contribution coefficient.
    prepowr_max : float
        Upper limit for power repulsion contribution coefficient.


    Returns
    -------
    dict
        Dict containing ``initial_enthalpy`` and fitting parameters.

    """
    # Read data in
    loading = isotherm.loading(
        branch=branch, loading_unit='mmol', loading_basis='molar'
    )
    loading = loading / max(loading)
    enthalpy = isotherm.other_data(enthalpy_key, branch=branch)

    if enthalpy is None:
        raise ParameterError('Could not find enthalpy column in isotherm')

    # Clean up data
    index = []
    for i, point in enumerate(enthalpy):
        if point < 0 or point > 400:
            index.append(i)
    if index:
        loading = numpy.delete(loading, index)
        enthalpy = numpy.delete(enthalpy, index)

    ##################################
    ##################################
    # First define the parameters

    param_names = [
        'const',
        'preexp',
        'exp',
        'exploc',
        'prepowa',
        'powa',
        'prepowr',
        'powr',
    ]
    params = {name: numpy.nan for name in param_names}

    # Then the functions
    def constant_term(loading):
        return params['const']

    def exponential_term(loading):
        return params['preexp'] * 1 / (
            1 + numpy.exp(params['exp'] * (loading - params['exploc']))
        )

    def power_term_repulsive(loading):
        return params['prepowr'] * loading**params['powr']

    def power_term_attractive(loading):
        return params['prepowa'] * loading**params['powa']

    def enthalpy_approx(loading):
        return constant_term(loading) + exponential_term(
            loading
        ) + power_term_repulsive(loading) + power_term_attractive(loading)

    def residual_sum_of_squares(params_):
        for i, _ in enumerate(param_names):
            params[param_names[i]] = params_[i]

        return numpy.sum(((enthalpy - enthalpy_approx(loading)) / enthalpy)**2)

    ##################################
    ##################################
    # We need to set some limits for the parameters to make sure
    # the solver returns realistic values

    bounds = {}
    ##################################
    # The constant term

    # We calculate the standard deviation
    enth_avg = numpy.average(enthalpy)
    enth_stdev = numpy.std(enthalpy)

    # The minimum should be at least the enthalpy of liquefaction
    # although it depends on the strength of the interaction with the
    # active site.

    # We check enthalpy of liquefaction
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    try:
        enth_liq = adsorbate.enthalpy_liquefaction(isotherm.temperature)
    except (ParameterError, CalculationError):
        enth_liq = 0
        warnings.warn(
            "Could not calculate liquid enthalpy, perhaps in supercritical regime"
        )

    bounds['const_min'] = max(enth_liq, enth_avg) - 2 * enth_stdev

    # The maximum constant contribution is taken similar to the minimum
    const_avg = max(enth_avg, bounds['const_min'])
    bounds['const_max'] = const_avg + 2 * enth_stdev

    ##################################
    # The exponential term

    # The constant term is meant to model the active sites or defects
    # in the material. It is represented as a logistic function.

    # The contribution should always lead to a decreasing
    # enthalpy of adsorption. Therefore:
    # The exponential term cannot be positive
    bounds['exp_min'] = 0
    bounds['exp_max'] = numpy.inf

    # The preexponential term cannot be negative
    bounds['preexp_min'] = 0
    # At zero loading, the enthalpy of adsorption is going to
    # be the preexponential factor + the constant factor.
    # Physically, there must be a limit for this interaction
    # even for chemisorption. We set a conservative limit.
    bounds['preexp_max'] = 150

    # Since the pressure is scaled, the location can only be between 0 and 1
    # We set the maximum at 0.5 do this to avoid weird behaviour at high loadings
    bounds['exploc_min'] = 0
    bounds['exploc_max'] = 0.5

    ##################################
    # The power term

    # The power term is supposed to model the guest-guest interactions
    # with two components: the power and the coefficient
    # The power should be at least 1 (1-1 interactions)
    bounds['powa_min'] = 1
    bounds['powr_min'] = 1
    # We set a realistic upper limit on the power of interactions
    bounds['powa_max'] = 20
    bounds['powr_max'] = 20

    # We set the attraction term between 0 and a reasonable final constant
    bounds['prepowa_min'] = 0
    bounds['prepowa_max'] = 50
    # We set the repulsion term between 0 and a reasonable final constant
    bounds['prepowr_min'] = -50
    bounds['prepowr_max'] = 0

    # ###############
    # Update with user values
    bounds.update(param_guess)

    # Generate bounds tuple
    bounds_arr = (
        (bounds.get('const_min'), bounds.get('const_max')),
        (bounds.get('preexp_min'), bounds.get('preexp_max')),
        (bounds.get('exp_min'), bounds.get('exp_max')),
        (bounds.get('exploc_min'), bounds.get('exploc_max')),
        (bounds.get('prepowa_min'), bounds.get('prepowa_max')),
        (bounds.get('powa_min'), bounds.get('powa_max')),
        (bounds.get('prepowr_min'), bounds.get('prepowr_max')),
        (bounds.get('powr_min'), bounds.get('powr_max')),
    )

    if verbose:
        logger.info(f"Bounds: \n\tconst = {bounds_arr[0]}")
        logger.info(
            f"\tpreexp = {bounds_arr[1]}, exp = {bounds_arr[2]}, exploc = {bounds_arr[3]}"
        )
        logger.info(f"\tprepowa = {bounds_arr[4]}, powa = {bounds_arr[5]}")
        logger.info(f"\tprepowr = {bounds_arr[6]}, powr = {bounds_arr[7]}")

    ##################################
    ##################################
    # Constraints on the parameters
    def maximize_constant(params_):
        return params_[0] - params_[1] * 1 / (1 + numpy.exp(params[2] * (loading - params[3]))) \
            - params_[4] * loading ** params_[5] - \
            params_[6] * loading ** params_[7]

    def repulsion_dominates(params_):
        return params_[7] - params_[5]

    constr = (
        # {'type': 'ineq', 'fun': maximize_constant},
        {
            'type': 'ineq',
            'fun': repulsion_dominates
        },
    )

    ##################################
    ##################################
    # We will do an optimisation with different starting guesses
    # then check which one fits best

    # Get a value for the departure of the first point:
    dep_first = min(max(enthalpy[0], 0), 150) - const_avg
    dep_last = min(max(enthalpy[-1], 0), 150) - const_avg
    guesses = (
        # Starting from a constant value
        numpy.array([const_avg, 0, 0, 0, 0, 1, 0, 1]),
        # Starting from an adjusted start and end
        numpy.array([
            0.5 * const_avg, dep_first, 0, 0,
            max(dep_last, 0), 1,
            min(dep_last, 0), 1
        ]),
        # Starting from a large exponent and gentle power increase
        numpy.array([const_avg, 1.5 * dep_first, 10, 0.1, 0.01, 3, 0, 1]),
        # Starting from no exponent and gentle power decrease
        numpy.array([const_avg, 0, 0, 0.1, 0, 3, -0.01, 3]),
    )

    options = {
        'disp': verbose,
        'maxiter': 100000,
        'ftol': 1e-8,
    }

    min_fun = numpy.inf
    final_guess = None
    best_fit = None

    for i, guess in enumerate(guesses):
        if verbose:
            logger.info('\n')
            logger.info(f"Minimizing routine number {i +1}")
            logger.info(f"Initial guess: \n\tconst = {guess[0]}")
            logger.info(
                f"\tpreexp = {guess[1]}, exp = {guess[2]}, exploc = {guess[3]}"
            )
            logger.info(f"\tprepowa = {guess[4]}, powa = {guess[5]}")
            logger.info(f"\tprepowr = {guess[6]}, powr = {guess[7]}")

        opt_res = scipy.optimize.minimize(
            residual_sum_of_squares,
            guess,
            bounds=bounds_arr,
            constraints=constr,
            method='SLSQP',
            options=options
        )

        if opt_res.fun < min_fun:
            final_guess = opt_res.x
            best_fit = opt_res.fun

    if final_guess is None:
        raise CalculationError(
            "\n\tMinimization of RSS fitting failed with all guesses"
        )
    if verbose:
        logger.info('\n')
        logger.info(f'Final best fit {best_fit}.')

    for i, _ in enumerate(param_names):
        params[param_names[i]] = final_guess[i]

    initial_enthalpy = enthalpy_approx(0)
    if abs(initial_enthalpy - enthalpy[0]) > 50:
        warnings.warn(
            "Probable offshoot for exponent, reverting to point method"
        )
        initial_enthalpy = initial_enthalpy_point(
            isotherm, enthalpy_key, branch=branch, verbose=verbose
        ).get('initial_enthalpy')

    if verbose:
        logger.info('\n')
        logger.info(
            f"The initial enthalpy of adsorption is: \n\tE = {initial_enthalpy:.2f}"
        )
        logger.info(f"The constant contribution is \n\t{params['const']:.2f}")
        if params['const'] < enth_liq:
            warnings.warn(
                'CARE: Base enthalpy of adsorption is lower than enthalpy of liquefaction.'
            )
        logger.info(
            "The exponential contribution is \n\t"
            f"{params['preexp']:.2f} * exp({params['exp']:.2E} * n)"
            f"with the limit at {params['exploc']:.2f}"
        )
        logger.info(
            "The guest-guest attractive contribution is \n\t"
            f"{params['prepowa']:.2g} * n^{params['powa']:.2}"
        )
        logger.info(
            "The guest-guest repulsive contribution is \n\t"
            f"{params['prepowr']:.2g} * n^{params['powr']:.2}"
        )

        x_axis = numpy.linspace(0, 1)
        baseline = constant_term(x_axis)
        extras = (
            (x_axis, [baseline for x in x_axis], 'constant'),
            (x_axis, baseline + exponential_term(x_axis), 'exponential'),
            (x_axis, baseline + power_term_attractive(x_axis), 'power attr'),
            (x_axis, baseline + power_term_repulsive(x_axis), 'power rep'),
        )

        title = f'{isotherm.material} {isotherm.adsorbate}'
        initial_enthalpy_plot(
            loading,
            enthalpy,
            enthalpy_approx(loading),
            title=title,
            extras=extras
        )

    params.update({'initial_enthalpy': initial_enthalpy})

    return params


def initial_enthalpy_point(
    isotherm, enthalpy_key, branch='ads', verbose=False
):
    """
    Given an isotherm with previous differential adsorption enthalpy data,
    calculate the enthalpy of adsorption at zero loading by taking the
    first point of the curve.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to use for the calculation.
    enthalpy_key : str
        The column which stores the enthalpy data.
    branch : str
        The isotherm branch to use for the calculation. Default is adsorption branch.
    verbose : bool, optional
        Whether to print out extra information.

    Returns
    -------
    dict
        Dict containing ``initial_enthalpy`` and other parameters.

    """
    # Read data in
    enthalpy = isotherm.other_data(enthalpy_key, branch=branch)

    if enthalpy is None:
        raise ParameterError('Could not find enthalpy column in isotherm')

    initial_enthalpy = enthalpy[0]

    if verbose:
        logger.info(
            f"The initial enthalpy of adsorption is: \n\tE = {initial_enthalpy:.2f}",
        )

        loading = isotherm.loading(
            branch=branch, loading_unit='mmol', loading_basis='molar'
        )
        title = f'{isotherm.material} {isotherm.adsorbate}'
        initial_enthalpy_plot(
            loading,
            enthalpy, [initial_enthalpy for i in loading],
            title=title
        )

    return {'initial_enthalpy': initial_enthalpy}
