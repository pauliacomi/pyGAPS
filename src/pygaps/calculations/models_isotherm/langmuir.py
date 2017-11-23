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
        """
        return self.params["M"] * self.params["K"] * pressure / \
            (1.0 + self.params["K"] * pressure)

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        return loading / \
            (self.params["K"] * (self.params["M"] - loading))

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        return self.params["M"] * \
            numpy.log(1.0 + self.params["K"] * pressure)

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        return {"M": saturation_loading, "K": langmuir_k}
