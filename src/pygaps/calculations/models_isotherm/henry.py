"""
Henry isotherm model
"""

import numpy

from .model import IsothermModel


class Henry(IsothermModel):
    """
    Henry's law. Only use if your data is linear, and do not necessarily trust
      IAST results from Henry's law if the result required an extrapolation
      of your data; Henry's law is unrealistic because the adsorption sites
      will saturate at higher pressures.

    .. math::

        L(P) = K_H P

    """
    #: Name of the class as static
    name = 'Henry'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"KH": numpy.nan}

    def loading(self, pressure):
        """
        Function that calculates loading
        """
        return self.params["KH"] * pressure

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        return loading / self.params["KH"]

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        return self.params["KH"] * pressure

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        return {"KH": saturation_loading * langmuir_k}
