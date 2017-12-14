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
        saturation_loading, langmuir_k = super(Langmuir, self).default_guess(
            data, loading_key, pressure_key)

        return {"M": saturation_loading, "K": langmuir_k}
