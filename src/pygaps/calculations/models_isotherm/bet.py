"""
BET isotherm model
"""

import numpy
import scipy

from .model import IsothermModel
from ...utilities.exceptions import CalculationError


class BET(IsothermModel):
    """
    Brunauer-Emmett-Teller (BET) adsorption isotherm

    .. math::

        L(P) = M\\frac{K_A P}{(1-K_B P)(1-K_B P+ K_A P)}
    """
    #: Name of the class as static
    name = 'BET'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M": numpy.nan, "Ka": numpy.nan, "Kb": numpy.nan}

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
        return self.params["M"] * self.params["Ka"] * pressure / (
            (1.0 - self.params["Kb"] * pressure) *
            (1.0 - self.params["Kb"] * pressure +
             self.params["Ka"] * pressure))

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
        return self.params["M"] * numpy.log(
            (1.0 - self.params["Kb"] * pressure +
             self.params["Ka"] * pressure) /
            (1.0 - self.params["Kb"] * pressure))

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting

        Parameters
        ----------
        saturation_loading : float
            Loading at the saturation plateau.
        langmuir_k : float
            Langmuir calculated constant.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        """
        # BET = Langmuir when Kb = 0.0. This is our default assumption.
        return {"M": saturation_loading, "Ka": langmuir_k,
                "Kb": langmuir_k * 0.01}
