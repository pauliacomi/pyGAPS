"""
Triple Site Langmuir isotherm model
"""

import numpy

from .model import IsothermModel


class TSLangmuir(IsothermModel):
    """
    Triple-site Langmuir (TSLangmuir) adsorption isotherm

    .. math::

        L(P) = M_1\\frac{K_1 P}{1+K_1 P} +  M_2\\frac{K_2 P}{1+K_2 P} + M_3\\frac{K_3 P}{1+K_3 P}
    """
    #: Name of the class as static
    name = 'TSLangmuir'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M1": numpy.nan, "K1": numpy.nan,
                       "M2": numpy.nan, "K2": numpy.nan,
                       "M3": numpy.nan, "K3": numpy.nan}

    def loading(self, pressure):
        """
        Function that calculates loading
        """
        # K_i P
        k1p = self.params["K1"] * pressure
        k2p = self.params["K2"] * pressure
        k3p = self.params["K3"] * pressure
        return self.params["M1"] * k1p / (1.0 + k1p) + \
            self.params["M2"] * k2p / (1.0 + k2p) + \
            self.params["M3"] * k3p / (1.0 + k3p)

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        raise NotImplementedError

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        return self.params["M1"] * numpy.log(
            1.0 + self.params["K1"] * pressure) +\
            self.params["M2"] * numpy.log(
            1.0 + self.params["K2"] * pressure) +\
            self.params["M3"] * numpy.log(
            1.0 + self.params["K3"] * pressure)

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        return {"M1": 0.5 * saturation_loading, "K1": 0.4 * langmuir_k,
                "M2": 0.5 * saturation_loading, "K2": 0.6 * langmuir_k,
                "M3": 0.5 * saturation_loading, "K3": 0.8 * langmuir_k}
