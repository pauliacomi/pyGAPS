"""
BET isotherm model
"""

import numpy

from .model import IsothermModel


class BET(IsothermModel):
    """
    Brunauer-Emmett-Teller (BET) adsorption isotherm

    .. math::

        L(P) = M\\frac{K_A P}{(1-K_B P)(1-K_B P+ K_A P)}
    """
    #: Name of the class as static
    name = 'BET'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M": numpy.nan, "Ka": numpy.nan, "Kb": numpy.nan}

    def loading(self, pressure):
        """
        Function that calculates loading
        """
        return self.params["M"] * self.params["Ka"] * pressure / (
            (1.0 - self.params["Kb"] * pressure) *
            (1.0 - self.params["Kb"] * pressure +
             self.params["Ka"] * pressure))

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        raise NotImplementedError

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        return self.params["M"] * numpy.log(
            (1.0 - self.params["Kb"] * pressure +
             self.params["Ka"] * pressure) /
            (1.0 - self.params["Kb"] * pressure))

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        # BET = Langmuir when Kb = 0.0. This is our default assumption.
        return {"M": saturation_loading, "Ka": langmuir_k,
                "Kb": langmuir_k * 0.01}
