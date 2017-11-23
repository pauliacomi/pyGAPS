"""
Quadratic isotherm model
"""

import numpy

from .model import IsothermModel


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
        """
        return self.params["M"] * (self.params["Ka"] +
                                   2.0 * self.params["Kb"] * pressure) * pressure / (
            1.0 + self.params["Ka"] * pressure +
            self.params["Kb"] * pressure ** 2)

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        raise NotImplementedError

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        return self.params["M"] * numpy.log(1.0 + self.params["Ka"] * pressure +
                                            self.params["Kb"] * pressure ** 2)

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        return {"M": saturation_loading / 2.0, "Ka": langmuir_k,
                "Kb": langmuir_k ** 2.0}
