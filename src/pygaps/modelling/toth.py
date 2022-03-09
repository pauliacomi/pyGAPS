"""Toth isotherm model."""

import numpy
from scipy import integrate

from pygaps.modelling.base_model import IsothermBaseModel


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
    formula = r"n(p) = n_m \frac{K p}{\sqrt[t]{1 + (K p)^t}}"
    calculates = 'loading'
    param_names = ("n_m", "K", "t")
    param_default_bounds = (
        (0, numpy.inf),
        (0, numpy.inf),
        (0, numpy.inf),
    )

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
        n_m = self.params["n_m"]
        Kp = self.params["K"] * pressure
        t = self.params["t"]
        return n_m * Kp / (1.0 + (Kp)**t)**(1 / t)

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
        n_m = self.params["n_m"]
        K = self.params["K"]
        t = self.params["t"]
        return (loading / (n_m * K)) / (1 - (loading / n_m)**t)**(1 / t)

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
        return integrate.quad(lambda x: self.loading(x) / x, 0, pressure)[0]

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
        saturation_loading, langmuir_k = super().initial_guess(pressure, loading)
        guess = {"n_m": saturation_loading, "K": langmuir_k, "t": 1}
        guess = self.initial_guess_bounds(guess)
        return guess
