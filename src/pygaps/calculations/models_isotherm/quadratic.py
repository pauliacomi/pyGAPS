"""
Quadratic isotherm model
"""

import numpy

from .model import IsothermModel
import scipy
from ...utilities.exceptions import CalculationError


class Quadratic(IsothermModel):
    """
    Quadratic isotherm model

    .. math::

        L(P) = M \\frac{(K_a + 2 K_b P)P}{1+K_aP+K_bP^2}
    """
    #: Name of the class as static
    name = 'Quadratic'

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
        return self.params["M"] * (self.params["Ka"] +
                                   2.0 * self.params["Kb"] * pressure) * pressure / (
            1.0 + self.params["Ka"] * pressure +
            self.params["Kb"] * pressure ** 2)

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
        return self.params["M"] * numpy.log(1.0 + self.params["Ka"] * pressure +
                                            self.params["Kb"] * pressure ** 2)

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
        saturation_loading, langmuir_k = super(Quadratic, self).default_guess(
            data, loading_key, pressure_key)

        return {"M": saturation_loading / 2.0, "Ka": langmuir_k,
                "Kb": langmuir_k ** 2.0}
