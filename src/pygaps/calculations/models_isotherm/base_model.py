"""Base class for all isotherm models."""

import abc

import numpy
import scipy.optimize as opt

from ...utilities.exceptions import CalculationError


class IsothermBaseModel():
    """Base class for all isotherm models."""

    __metaclass__ = abc.ABCMeta

    name = None
    calculates = None  # loading/pressure
    param_names = []
    param_bounds = None

    def __init__(self):
        """Instantiate parameters."""
        self.params = {param: numpy.nan for param in self.param_names}

    def __str__(self):
        """Print model name."""
        return self.name

    @abc.abstractmethod
    def loading(self, pressure):
        """
        Calculate loading at specified pressure.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """
        return

    @abc.abstractmethod
    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return

    @abc.abstractmethod
    def spreading_pressure(self, pressure):
        """
        Calculate spreading pressure at specified gas pressure.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return

    def default_guess(self, pressure, loading):
        """
        Return initial guess for fitting.

        Parameters
        ----------
        loading_key : str
            Loading data.
        pressure_key : str
            Pressure data.

        Returns
        -------
        saturation_loading : float
            Loading at the saturation plateau.
        langmuir_k : float
            Langmuir calculated constant.

        """
        # guess saturation loading to 10% more than highest loading
        saturation_loading = 1.1 * max(loading)

        # guess Langmuir K using the guess for saturation loading and lowest
        # pressure point (but not zero)
        idx_min = numpy.nonzero(loading)[0][0]
        langmuir_k = loading[idx_min] / pressure[idx_min] / (saturation_loading - pressure[idx_min])

        return saturation_loading, langmuir_k

    def fit(self, pressure, loading, param_guess, optimization_params=dict(method="Nelder-Mead"), verbose=False):
        """
        Fit model to data using nonlinear optimization with least squares loss function.

        Resulting parameters are assigned to self.

        Parameters
        ----------
        pressure : ndarray
            The pressures of each point.
        loading : ndarray
            The loading for each point.
        func : ndarray
            The pressures of each point.
        param_guess : ndarray
            The initial guess for the fitting function.
        optimization_params : dict
            Dictionary to be passed to the minimization function to use in fitting model to data.
        verbose : bool, optional
            Prints out extra information about steps taken.
        """
        if verbose:
            print("Attempting to model using {0}".format(self.name))

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params]
        guess = numpy.array([param_guess[param] for param in param_names])
        bounds = [[self.param_bounds[param][0] for param in param_names],
                  [self.param_bounds[param][1] for param in param_names]]

        def fun(x, p, l):
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = x[i]
            return self.loading(p) - l

        # minimize RSS
        opt_res = opt.least_squares(
            fun, guess,
            args=(pressure, loading),
            bounds=bounds)
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

        rmse = numpy.sqrt(numpy.sum(numpy.abs(opt_res.fun)) / len(loading))

        if verbose:
            print("Model {0} success, RMSE is {1:.3f}".format(self.name, rmse))

        return rmse
