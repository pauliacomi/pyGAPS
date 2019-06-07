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
    rmse = None
    pressure_range = None
    loading_range = None

    def __init__(self):
        """Instantiate parameters."""
        self.params = {param: numpy.nan for param in self.param_names}

    def __init_parameters__(self, parameters):
        """Initialize model parameters from isotherm data."""
        pass

    def __repr__(self):
        """Print model name."""
        return "pyGAPS Model, type {}".format(self.name)

    def __str__(self):
        """Print model name and parameters."""
        ret_string = (
            "{0} isotherm model.\n".format(self.name) +
            "RMSE = {:.4f}\n".format(self.rmse) +
            "Model parameters:\n"
        )
        for param, val in self.params.items():
            ret_string += "\t%s = %f\n" % (param, val)
        ret_string += (
            "Model applicable range:\n" +
            "\tPressure range: {:.2f} - {:.2f}\n".format(
                self.pressure_range[0], self.pressure_range[1]) +
            "\tLoading range: {:.2f} - {:.2f}\n".format(
                self.loading_range[0], self.loading_range[1])
        )

        return ret_string

    def to_dict(self):
        return {
            'model': self.name,
            'rmse': self.rmse,
            'parameters': self.params,
            'pressure_range': self.pressure_range,
            'loading_range': self.loading_range,
        }

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
        pressure : array
            Pressure data.
        loading : array
            Loading data.

        Returns
        -------
        saturation_loading : float
            Loading at the saturation plateau.
        langmuir_k : float
            Langmuir calculated constant.

        """
        # ensure arrays
        loading = numpy.asarray(loading)
        pressure = numpy.asarray(pressure)

        # remove invalid values in function
        zero_values = ~numpy.logical_and(pressure > 0, loading > 0)
        if any(zero_values):
            pressure = pressure[~zero_values]
            loading = loading[~zero_values]

        # guess saturation loading to 10% more than highest loading
        saturation_loading = 1.1 * max(loading)
        langmuir_k = loading[0] / pressure[0] / (saturation_loading - pressure[0])

        return saturation_loading, langmuir_k

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
        param_guess : ndarray
            The initial guess for the fitting function.
        optimization_params : dict
            Custom parameters to pass to SciPy.optimize.least_squares.
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

        def fit_func(x, p, l):
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = x[i]
            return self.loading(p) - l

        kwargs = dict(
            bounds=bounds,                      # supply the bounds of the parameters
        )
        if optimization_params:
            kwargs.update(optimization_params)

        # minimize RSS
        opt_res = opt.least_squares(
            fit_func, guess,                    # provide the fit function and initial guess
            args=(pressure, loading),           # supply the extra arguments to the fit function
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
            print("Model {0} success, RMSE is {1:.3f}".format(self.name, self.rmse))
