"""
This module calculates the initial enthalpy of adsorption based on an isotherm.
"""

import numpy
import scipy

from ..classes.adsorbate import Adsorbate
from ..graphing.calcgraph import initial_enthalpy_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError


def initial_enthalpy_comp(isotherm, enthalpy_key, branch='ads', verbose=False):
    """
    Calculates an initial enthalpy based on a compound
    method with three separate contributions:

        * A constant contribution
        * An 'active site' decaying exponential contribution
        * A power contribution to model adsorbate-adsorbate interactions

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
    float
        Initial enthalpy.
    """

    # Read data in
    loading = isotherm.loading(branch=branch,
                               loading_unit='mmol',
                               loading_basis='molar')
    enthalpy = isotherm.other_data(enthalpy_key, branch=branch)

    if not enthalpy:
        raise ParameterError('Could not find enthalpy column in isotherm')

    # get adsorbate properties
    adsorbate = Adsorbate.from_list(isotherm.adsorbate)
    enth_liq = adsorbate.enthalpy_liquefaction(isotherm.t_exp)

    params = {
        'const': (enth_liq, (enth_liq, None)),
        'preexp': (enthalpy[0] - enth_liq, (None, None)),
        'exp': (0, (None, None)),
        'prepow': (0, (None, None)),
        'pow': (1, (None, None))
    }
    param_names = [param for param in params]
    guess = numpy.array([params[param][0] for param in param_names])
    bounds = [params[param][1] for param in param_names]

    def enthalpy_approx(loading_):

        term_constant = params['const']
        term_exponential = params['preexp'] * \
            numpy.exp(params['exp'] * loading_)
        term_power = params['prepow'] * loading_ ** params['pow']

        return term_constant + term_exponential + term_power

    def residual_sum_of_squares(params_):
        for i, _ in enumerate(param_names):
            params[param_names[i]] = params_[i]

        calc_enth = enthalpy_approx(loading)

        return numpy.sum(((enthalpy - calc_enth) / enthalpy) ** 2)

    options = {'disp': verbose,
               'maxiter': 1e7,
               #            'ftol': 0.0001,
               }

    opt_res = scipy.optimize.minimize(residual_sum_of_squares, guess, bounds=bounds,
                                      method='SLSQP', options=options)

    if not opt_res.success:
        raise CalculationError(
            "\n\tMinimization of RSS fitting failed with error:"
            "\n\t\t{0}".format(opt_res.message))

    initial_enthalpy = enthalpy_approx(0)

    if verbose:
        print("The initial enthalpy of adsorption is: \n\tE =",
              round(initial_enthalpy, 2))

        print("The constant contribution is \n\t{:.2}".format(
            params['const']))
        print("The exponential contribution is \n\t{:.2E} * exp({:.2E} * n)".format(
            params['preexp'], params['exp']))
        print("The power contribution is \n\t{:.2E} * n^{:.2}".format(
            params['prepow'], params['pow']))

        initial_enthalpy_plot(loading, enthalpy, enthalpy_approx(loading))

    return initial_enthalpy


def initial_enthalpy_point(isotherm, enthalpy_key, branch='ads', verbose=False):
    """
    Calculates the initial enthalpy of adsorption by assuming it is the same
    as the first point in the curve.

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
    float
        Initial enthalpy.
    """

    # Read data in
    enthalpy = isotherm.other_data(enthalpy_key, branch=branch)

    if not enthalpy:
        raise ParameterError('Could not find enthalpy column in isotherm')

    initial_enthalpy = enthalpy[0]

    if verbose:
        print("The initial enthalpy of adsorption is: \n\tE =",
              round(initial_enthalpy, 2))

    return initial_enthalpy
