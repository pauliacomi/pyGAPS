"""
Base class for all models
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError


class IsothermModel(object):
    """
    Base class for all models
    """

    #: Name of the model
    name = None
    calculates = None  # loading/pressure

    def __init__(self):
        """
        Instantiation function
        """

        self.params = dict()

    def __str__(self):
        """
        Prints model name
        """
        return self.name

    def loading(self, pressure):
        """
        Function that calculates loading

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """
        return None

    def pressure(self, loading):
        """
        Function that calculates pressure

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return None

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return None

    def default_guess(self, data, loading_key, pressure_key):
        """
        Returns initial guess for fitting

        Parameters
        ----------
        data : pandas.DataFrame
            Data of the isotherm.
        loading_key : str
            Column with the loading.
        pressure_key : str
            Column with the pressure.

        Returns
        -------
        saturation_loading : float
            Loading at the saturation plateau.
        langmuir_k : float
            Langmuir calculated constant.
        """

        # guess saturation loading to 10% more than highest loading
        saturation_loading = 1.1 * data[loading_key].max()

        # guess Langmuir K using the guess for saturation loading and lowest
        # pressure point (but not zero)
        df_nonzero = data[data[loading_key] != 0.0]
        idx_min = df_nonzero[loading_key].idxmin()
        langmuir_k = df_nonzero[loading_key].loc[idx_min] / \
            df_nonzero[pressure_key].loc[idx_min] / (
            saturation_loading - df_nonzero[pressure_key].loc[idx_min])

        return saturation_loading, langmuir_k

    def fit(self, loading, pressure, param_guess, optimization_params=dict(method="Nelder-Mead"), verbose=False):
        """
        Fit model to data using nonlinear optimization with least squares loss
        function. Assigns parameters to self

        Parameters
        ----------
        loading : ndarray
            The loading for each point.
        pressure : ndarray
            The pressures of each point.
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
            print("Attempting to model using {}".format(self.name))

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params]
        # guess
        guess = numpy.array([param_guess[param] for param in param_names])

        def residual_sum_of_squares(params_):
            """
            Residual Sum of Squares between model and data in data
            """
            # change params to those in x
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = params_[i]

            return numpy.sum((loading - self.loading(pressure)) ** 2)

        # minimize RSS
        opt_res = scipy.optimize.minimize(residual_sum_of_squares, guess,
                                          **optimization_params)
        if not opt_res.success:
            raise CalculationError(
                "\n\tMinimization of RSS for {0} isotherm fitting failed with error:"
                "\n\t\t{1}"
                "\n\tTry a different starting point in the nonlinear optimization"
                "\n\tby passing a dictionary of parameter guesses, param_guess, to the"
                "\n\tconstructor."
                "\n\tDefault starting guess for parameters:"
                "\n\t{2}".format(self.name, opt_res.message, param_guess))

        # assign params
        for index, _ in enumerate(param_names):
            self.params[param_names[index]] = opt_res.x[index]

        rmse = numpy.sqrt(opt_res.fun / len(loading))

        if verbose:
            print("Model {0} success, rmse is {1}".format(
                self.name, rmse))

        return rmse
