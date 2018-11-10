"""
GAB isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class GAB(IsothermModel):
    """
    Guggenheim-Anderson-de Boer (GAB) adsorption isotherm

    .. math::

        n(p) = n_m \\frac{C K p}{(1 - K p)(1 - K p + K C p)}

    Notes
    -----

    An extension of the BET model which introduces a constant
    K, accounting for a different enthalpy of adsorption of
    the adsorbed phase when compared to liquefaction enthalpy of
    the bulk phase.

    It is often used to fit adsorption and desorption isotherms of
    water in the food industry.[#]_

    References
    ----------
    .. [#] “Water Activity: Theory and Applications to Food”, Kapsalis. J. G., 1987
    """

    #: Name of the model
    name = 'GAB'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"n_m": numpy.nan, "K": numpy.nan,  "C": numpy.nan}

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
        return self.params["n_m"] * self.params["K"] * self.params["C"] * pressure / (
            (1.0 - self.params["K"] * pressure) *
            (1.0 - self.params["K"] * pressure +
             self.params["K"] * self.params["C"] * pressure))

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the GAB model, the pressure will
        be computed numerically as no analytical inversion is possible.

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

        opt_res = scipy.optimize.root(fun, 0, method='hybr')

        if not opt_res.success:
            raise CalculationError("""
            Root finding for value {0} failed.
            """.format(loading))

        return opt_res.x

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \\pi = \\int_{0}^{p_i} \\frac{n_i(p_i)}{p_i} dp_i

        The integral for the GAB model is solved analytically.

        .. math::

            \\pi = n_m \\ln{\\frac{1 - K p + C K p}{1- K p}}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["n_m"] * numpy.log(
            (1.0 - self.params["K"] * pressure +
             self.params["K"] * self.params["C"] * pressure) /
            (1.0 - self.params["K"] * pressure))

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
        saturation_loading, langmuir_k = super(GAB, self).default_guess(
            data, loading_key, pressure_key)

        return {"n_m": saturation_loading, "C": langmuir_k, "K": 1.00}
