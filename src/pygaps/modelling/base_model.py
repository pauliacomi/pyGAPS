"""Base class for all isotherm models."""

import abc
import logging

logger = logging.getLogger('pygaps')

import numpy

from .. import scipy
from ..utilities.exceptions import CalculationError


class IsothermBaseModel():
    """Base class for all isotherm models."""

    __metaclass__ = abc.ABCMeta

    # Class specific
    name = None
    calculates = None  # loading/pressure
    param_names = []
    param_bounds = None

    # Instance specific
    rmse = numpy.nan
    pressure_range = [numpy.nan, numpy.nan]
    loading_range = [numpy.nan, numpy.nan]

    def __init__(self, params=None):
        """Instantiate parameters."""

        if params:
            self.rmse = params.pop('rmse', numpy.nan)
            self.pressure_range = params.pop(
                'pressure_range', [numpy.nan, numpy.nan]
            )
            self.loading_range = params.pop(
                'loading_range', [numpy.nan, numpy.nan]
            )
            self.params = {}
            for param in self.param_names:
                try:
                    self.params[param] = params['parameters'][param]
                except KeyError as err:
                    raise KeyError(
                        f"""The isotherm model is missing parameter '{param}'."""
                    ) from err

        else:
            self.params = {param: numpy.nan for param in self.param_names}

    def __init_parameters__(self, parameters):
        """Initialize model parameters from isotherm data."""

    def __repr__(self):
        """Print model name."""
        return f"pyGAPS Isotherm Model, '{self.name}' type"

    def __str__(self):
        """Print model name and parameters."""
        ret_string = (
            f"{self.name} isotherm model.\n"
            f"RMSE = {self.rmse:.4f}\n"
            "Model parameters:\n"
        )
        for param, val in self.params.items():
            ret_string += f"\t{param} = {val:.2f}\n"
        ret_string += (
            "Model applicable range:\n" +
            f"\tPressure range: {self.pressure_range[0]:.2f} - {self.pressure_range[1]:.2f}\n"
            f"\tLoading range: {self.loading_range[0]:.2f} - {self.loading_range[1]:.2f}\n"
        )

        return ret_string

    def to_dict(self):
        """Convert model to a dictionary."""
        return {
            'name': self.name,
            'rmse': self.rmse,
            'parameters': self.params,
            'pressure_range': tuple(map(float, self.pressure_range)),
            'loading_range': tuple(map(float, self.loading_range)),
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

    def initial_guess(self, pressure, loading):
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
        # ensure arrays of at least 1 dimension
        loading = numpy.atleast_1d(loading)
        pressure = numpy.atleast_1d(pressure)

        # remove invalid values in function
        zero_values = ~numpy.logical_and(pressure > 0, loading > 0)
        if any(zero_values):
            pressure = pressure[~zero_values]
            loading = loading[~zero_values]

        # guess saturation loading to 10% more than highest loading
        saturation_loading = 1.1 * max(loading)
        # guess langmuir constant from the starting point
        langmuir_k = loading[0] / pressure[0] / (
            saturation_loading - loading[0]
        )

        return saturation_loading, langmuir_k

    def fit(
        self,
        pressure,
        loading,
        param_guess,
        optimization_params=None,
        verbose=False
    ):
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
            logger.info(f"Attempting to model using {self.name}.")

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params]
        guess = numpy.array([param_guess[param] for param in param_names])
        bounds = [[self.param_bounds[param][0] for param in param_names],
                  [self.param_bounds[param][1] for param in param_names]]

        def fit_func(x, p, L):
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = x[i]
            return self.loading(p) - L

        kwargs = dict(
            bounds=bounds,  # supply the bounds of the parameters
        )
        if optimization_params:
            kwargs.update(optimization_params)

        # minimize RSS
        try:
            opt_res = scipy.optimize.least_squares(
                fit_func,
                guess,  # provide the fit function and initial guess
                args=(pressure, loading
                      ),  # supply the extra arguments to the fit function
                **kwargs
            )
        except ValueError as e:
            raise CalculationError(
                f"Fitting routine for {self.name} failed with error:"
                f"\n\t{e}"
            )
        if not opt_res.success:
            raise CalculationError(
                f"Fitting routine for {self.name} failed with error:"
                f"\n\t{opt_res.message}"
                f"\nTry a different starting point in the nonlinear optimization"
                f"\nby passing a dictionary of parameter guesses, param_guess, to the constructor."
                f"\nDefault starting guess for parameters:"
                f"\n{param_guess}\n"
            )

        # assign params
        for index, _ in enumerate(param_names):
            self.params[param_names[index]] = opt_res.x[index]

        # calculate RMSE
        self.rmse = numpy.sqrt(numpy.sum((opt_res.fun)**2) / len(loading))

        if verbose:
            logger.info(f"Model {self.name} success, RMSE is {self.rmse:.3f}")
