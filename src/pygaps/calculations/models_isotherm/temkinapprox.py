"""
Temkin Approximation isotherm model
"""

import numpy

from .model import IsothermModel


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
        """
        langmuir_fractional_loading = self.params["K"] * pressure / \
            (1.0 + self.params["K"] * pressure)
        return self.params["M"] * (langmuir_fractional_loading +
                                   self.params["theta"] * langmuir_fractional_loading ** 2 *
                                   langmuir_fractional_loading)

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        raise NotImplementedError

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        one_plus_kp = 1.0 + self.params["K"] * pressure
        return self.params["M"] * (numpy.log(one_plus_kp) +
                                   self.params["theta"] * (2.0 * self.params["K"] * pressure + 1.0) /
                                   (2.0 * one_plus_kp ** 2))

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        return {"M": saturation_loading, "K": langmuir_k, "theta": 0.0}
