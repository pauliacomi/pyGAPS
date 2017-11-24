"""
Langmuir isotherm model
"""

import numpy

from .model import IsothermModel


class Langmuir(IsothermModel):
    """
    Langmuir isotherm model

    .. math::

        L(P) = M\\frac{KP}{1+KP},
    """
    #: Name of the class as static
    name = 'Langmuir'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M": numpy.nan, "K": numpy.nan}

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
        return self.params["M"] * self.params["K"] * pressure / \
            (1.0 + self.params["K"] * pressure)

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
        return loading / \
            (self.params["K"] * (self.params["M"] - loading))

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
        return self.params["M"] * \
            numpy.log(1.0 + self.params["K"] * pressure)

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
        return {"M": saturation_loading, "K": langmuir_k}
