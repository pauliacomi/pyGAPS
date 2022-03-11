"""Temkin Approximation isotherm model."""

import numpy
from scipy import optimize

from pygaps.modelling.base_model import IsothermBaseModel
from pygaps.utilities.exceptions import CalculationError


class TemkinApprox(IsothermBaseModel):
    r"""
    Asymptotic approximation to the Temkin isotherm.

    .. math::

        n(p) = n_m \frac{K p}{1 + K p} + n_m \theta (\frac{K p}{1 + K p})^2 (\frac{K p}{1 + K p} -1)

    Notes
    -----
    The Temkin adsorption isotherm [#]_, like the Langmuir model, considers
    a surface with n_m identical adsorption sites, but takes into account adsorbate-
    adsorbate interactions by assuming that the enthalpy of adsorption is a linear
    function of the coverage. The Temkin isotherm is derived [#]_ using a
    mean-field argument and used an asymptotic approximation
    to obtain an explicit equation for the loading.

    Here, :math:`n_m` and K have the same physical meaning as in the Langmuir model.
    The additional parameter :math:`\theta` describes the strength of the adsorbate-adsorbate
    interactions (:math:`\theta < 0` for attractions).

    References
    ----------
    .. [#]  V. P. M.I. Tempkin, Kinetics of ammonia synthesis on promoted iron
       catalyst, Acta Phys. Chim. USSR 12 (1940) 327–356.
    .. [#] Phys. Chem. Chem. Phys., 2014,16, 5499-5513

    """

    # Model parameters
    name = 'TemkinApprox'
    formula = r"n(p) = n_m \frac{K p}{1 + K p} + n_m \theta (\frac{K p}{1 + K p})^2 (\frac{K p}{1 + K p} -1)"
    calculates = 'loading'
    param_names = ("n_m", "K", "tht")
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
        tht = self.params["tht"]
        lang_load = Kp / (1.0 + Kp)
        return n_m * (lang_load + tht * lang_load**2 * (lang_load - 1))

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the TemkinApprox model, the pressure will
        be computed numerically as no analytical inversion is possible.

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        def fun(x):
            return self.loading(x) - loading

        opt_res = optimize.root(fun, numpy.zeros_like(loading), method='hybr')

        if not opt_res.success:
            raise CalculationError(f"Root finding for value {loading} failed.")

        return opt_res.x

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the TemkinApprox model is solved analytically.

        .. math::

            \pi = n_m \Big( \ln{(1 + K p)} + \frac{\theta (2 K p + 1)}{2(1 + K p)^2}\Big)

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        n_m = self.params["n_m"]
        Kp = self.params["K"] * pressure
        tht = self.params["tht"]
        one_plus_kp = 1.0 + Kp
        return n_m * (numpy.log(one_plus_kp) + tht * (2.0 * Kp + 1.0) / (2.0 * one_plus_kp**2))

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
        guess = {"n_m": saturation_loading, "K": langmuir_k, "tht": 0.0}
        guess = self.initial_guess_bounds(guess)
        return guess
