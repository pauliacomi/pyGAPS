"""
Temkin Approximation isotherm model
"""

import numpy

from .model import IsothermModel
import scipy
from ...utilities.exceptions import CalculationError


class TemkinApprox(IsothermModel):
    """
    Asymptotic approximation to the Temkin Isotherm
      (see DOI: 10.1039/C3CP55039G)

    .. math::

        L(P) = M\\frac{KP}{1+KP} + M \\theta (\\frac{KP}{1+KP})^2 (\\frac{KP}{1+KP} -1)

    """
    #: Name of the class as static
    name = 'TemkinApprox'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M": numpy.nan, "K": numpy.nan, "theta": numpy.nan}

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
        langmuir_fractional_loading = self.params["K"] * pressure / \
            (1.0 + self.params["K"] * pressure)
        return self.params["M"] * (langmuir_fractional_loading +
                                   self.params["theta"] * langmuir_fractional_loading ** 2 *
                                   (langmuir_fractional_loading - 1))

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
        def fun(x):
            return self.loading(x) - loading

        opt_res = scipy.optimize.root(fun, 1, method='hybr')

        if not opt_res.success:
            raise CalculationError("""
            Root finding for value {0} failed.
            """.format(loading))

        return opt_res.x

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
        one_plus_kp = 1.0 + self.params["K"] * pressure
        return self.params["M"] * (numpy.log(one_plus_kp) +
                                   self.params["theta"] * (2.0 * self.params["K"] * pressure + 1.0) /
                                   (2.0 * one_plus_kp ** 2))

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
        dict
            Dictionary of initial guesses for the parameters.
        """
        saturation_loading, langmuir_k = super(TemkinApprox, self).default_guess(
            data, loading_key, pressure_key)

        return {"M": saturation_loading, "K": langmuir_k, "theta": 0.0}
