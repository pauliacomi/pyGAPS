"""Virial isotherm model."""

import warnings

import matplotlib.pyplot as plt
import numpy
import scipy.optimize as opt

from ...utilities.exceptions import CalculationError
from .base_model import IsothermBaseModel


class Virial(IsothermBaseModel):
    r"""
    A virial isotherm model with 3 factors.

    .. math::

        p = n \exp{(-\ln{K_H} + An + Bn^2 + Cn^3)}

    Notes
    -----
    A virial isotherm model attempts to fit the measured data to a factorized
    exponent relationship between loading and pressure.

    .. math::

        p = n \exp{(K_1n^0 + K_2n^1 + K_3n^2 + K_4n^3 + ... + K_i n^{i-1})}

    It has been applied with success to describe the behaviour of standard as
    well as supercritical isotherms. The factors are usually empirical,
    although some relationship with physical can be determined:
    the first constant is related to the Henry constant at zero loading, while
    the second constant is a measure of the interaction strength with the surface.

    .. math::

        K_1 = -\ln{K_{H,0}}

    In practice, besides the first constant, only 2-3 factors are used.

    """

    # Model parameters
    name = 'Virial'
    calculates = 'pressure'
    param_names = ["K", "A", "B", "C"]
    param_bounds = {
        "K": [0, numpy.inf],
        "A": [-numpy.inf, numpy.inf],
        "B": [-numpy.inf, numpy.inf],
        "C": [-numpy.inf, numpy.inf],
    }

    def loading(self, pressure):
        """
        Calculate loading at specified pressure.

        Careful!
        For the Virial model, the loading has to
        be computed numerically.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """
        def fun(x):
            return (self.pressure(x) - pressure)**2

        opt_res = opt.minimize(fun, pressure, method='Nelder-Mead')

        if not opt_res.success:
            raise CalculationError("""
            Root finding for failed. Error: \n\t{}
            """.format(opt_res.message))

        return opt_res.x

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        The Virial model calculates the pressure directly.

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return loading * numpy.exp(-numpy.log(self.params['K']) + self.params['A'] * loading
                                   + self.params['B'] * loading**2 + self.params['C'] * loading**3)

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the Virial model cannot be solved analytically
        and must be calculated numerically.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        raise NotImplementedError

    def default_guess(self, pressure, loading):
        """
        Return initial guess for fitting.

        Parameters
        ----------
        pressure : ndarray
            Pressure data.
        loading : ndarray
            Loading data.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        """
        saturation_loading, langmuir_k = super().default_guess(pressure, loading)

        return {"K": saturation_loading * langmuir_k,
                "A": 0, "B": 0, "C": 0}

    def fit(self, pressure, loading, param_guess, optimization_params=None, verbose=False):
        """
        Fit model to data using nonlinear optimization with least squares loss function.

        Resulting parameters are assigned to self.

        Parameters
        ----------
        pressure : ndarray
            The pressures of each point.
        loading : ndarray
            The loading for each point.
        optimization_params : dict
            Custom parameters to pass to SciPy.optimize.least_squares.
        verbose : bool, optional
            Prints out extra information about steps taken.
        """
        if verbose:
            print("Attempting to model using {}".format(self.name))

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params]
        guess = numpy.array([param_guess[param] for param in param_names])
        bounds = [[self.param_bounds[param][0] for param in param_names],
                  [self.param_bounds[param][1] for param in param_names]]

        # remove invalid values in function
        zero_values = ~numpy.logical_and(pressure > 0, loading > 0)
        if any(zero_values):
            warnings.warn('Removed points which are equal to 0.')
            pressure = pressure[~zero_values]
            loading = loading[~zero_values]

        # define fitting function as polynomial transformed input
        ln_p_over_n = numpy.log(numpy.divide(pressure, loading))

        # add point
        add_point = False
        added_point = False
        if optimization_params:
            add_point = optimization_params.pop('add_point', None)
        fractional_loading = loading / max(loading)
        if len(fractional_loading[fractional_loading < 0.5]) < 3:
            if not add_point:
                raise CalculationError(
                    """
                    The isotherm recorded has very few points below 0.5
                    fractional loading. If a virial model fit is attempted
                    the resulting polynomial will likely be unstable in the
                    low loading region.

                    You can pass ``add_point=True`` in ``optimization_params``
                    to attempt to add a point in the low pressure region or
                    record better isotherms.
                    """
                )
            added_point = True
            ln_p_over_n = numpy.hstack([ln_p_over_n[0], ln_p_over_n])
            loading = numpy.hstack([1e-1, loading])

        def fit_func(x, l, ln_p_over_n):
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = x[i]
            return self.params['C'] * l**3 + self.params['B'] * l**2 \
                + self.params['A'] * l - numpy.log(self.params['K']) - ln_p_over_n

        kwargs = dict(
            bounds=bounds,                      # supply the bounds of the parameters
            # loss='huber',                     # use a loss function against outliers
            # f_scale=0.1,                      # scale of outliers
        )
        if optimization_params:
            kwargs.update(optimization_params)

        # minimize RSS
        opt_res = opt.least_squares(
            fit_func, guess,                    # provide the fit function and initial guess
            args=(loading, ln_p_over_n),        # supply the extra arguments to the fit function
            **kwargs
        )
        if not opt_res.success:
            raise CalculationError(
                "\n\tMinimization of RSS for {0} isotherm fitting failed with error:"
                "\n\t\t{1}"
                "\n\tTry a different starting point in the nonlinear optimization"
                "\n\tby passing a dictionary of parameter guesses, param_guess, to the constructor."
                "\n\tDefault starting guess for parameters:"
                "\n\t{2}".format(self.name, opt_res.message, param_guess))

        # assign params
        for index, _ in enumerate(param_names):
            self.params[param_names[index]] = opt_res.x[index]

        self.rmse = numpy.sqrt(numpy.sum((opt_res.fun)**2) / len(loading))

        if verbose:
            print("Model {0} success, rmse is {1}".format(
                self.name, self.rmse))
            n_load = numpy.linspace(1e-2, numpy.amax(loading), 100)
            plt.plot(loading, ln_p_over_n, '.')
            plt.plot(n_load, numpy.log(numpy.divide(self.pressure(n_load), n_load)), '-')
            if added_point:
                plt.plot(1e-1, ln_p_over_n[0], '.r')
            plt.title("Virial fit")
            plt.xlabel("Loading")
            plt.ylabel("ln(p/n)")
            plt.show()
