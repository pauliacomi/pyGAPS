"""Toth isotherm model."""

import numpy

from .. import scipy
from .base_model import IsothermBaseModel


class Toth(IsothermBaseModel):
    r"""
    Toth isotherm model.

    .. math::

        n(p) = n_m \frac{K p}{\sqrt[t]{1 + (K p)^t}}

    Notes
    -----
    The Toth model is an empirical modification to the Langmuir equation.
    The parameter :math:`t` is a measure of the system heterogeneity.

    Thanks to this additional parameter, the Toth equation can accurately describe a
    large number of adsorbent/adsorbate systems and is such as
    hydrocarbons, carbon oxides, hydrogen sulphide and alcohols on
    activated carbons and zeolites.

    """

    # Model parameters
    name = 'Toth'
    calculates = 'loading'
    param_names = ["n_m", "K", "t"]
    param_bounds = {
        "n_m": [0, numpy.inf],
        "K": [0, numpy.inf],
        "t": [0, numpy.inf],
    }

    def loading(self, pressure):
        """
        Calculate loading at specified pressure.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """
        return self.params["n_m"] * self.params["K"] * pressure / \
            (1.0 + (self.params["K"] * pressure)**self.params["t"]) \
            ** (1 / self.params["t"])

    def pressure(self, loading):
        r"""
        Calculate pressure at specified loading.

        For the Toth model, a direct relationship can be found
        analytically:

        .. math::

            p = \frac{n/(n_m K)}{\sqrt[t]{1-(n/n_m)^t)}}

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return (loading / (self.params["n_m"] * self.params["K"])) / \
            (1 - (loading / self.params["n_m"])**self.params["t"])**(1 / self.params["t"])

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

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
        return scipy.integrate.quad(
            lambda x: self.loading(x) / x, 0, pressure
        )[0]

    def initial_guess(self, pressure, loading):
        """
        Return initial guess for fitting.

        Parameters
        ----------
        pressure : ndarray
            Pressure data.
        loading : ndarray
            Loading data.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        """
        saturation_loading, langmuir_k = super().initial_guess(
            pressure, loading
        )

        guess = {"n_m": saturation_loading, "K": langmuir_k, "t": 1}

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess
