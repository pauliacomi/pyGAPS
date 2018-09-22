"""
Toth isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class Toth(IsothermModel):
    """
    The Toth isotherm model

    .. math::

        n(p) = n_M \\frac{K p}{(1 + (K p)^t)^(1/t)}

    Notes
    -----

    The Toth model is an empirical modification to the Langmuir equation.
    The parameter :math:`t` is a measure of the system heterogeneity.

    Thanks to this additional parameter, the Toth equation can accurately describe a
    large number of adsorbent/adsorbate systems and is recommended as the first
    choice of isotherm equation for fitting isotherms of many adsorbents such as
    hydrocarbons, carbon oxides, hydrogen sulphide and alcohols on activated carbons
    but also zeolites.

    """
    #: Name of the model
    name = 'Toth'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"n_M": numpy.nan, "K": numpy.nan, "t": numpy.nan}

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
        return self.params["n_M"] * self.params["K"] * pressure / \
            (1.0 + (self.params["K"] * pressure)**self.params["t"]) \
            ** (1 / self.params["t"])

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the Toth model, the pressure will
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

        The integral for the Toth model cannot be solved analytically
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
        return scipy.integrate.quad(lambda x: self.loading(x) / x, 0, pressure)[0]

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
        saturation_loading, langmuir_k = super(Toth, self).default_guess(
            data, loading_key, pressure_key)

        return {"n_M": saturation_loading, "K": langmuir_k, "t": 1}
