"""Jensen-Seaton isotherm model."""

import numpy

from .. import scipy
from ..utilities.exceptions import CalculationError
from .base_model import IsothermBaseModel


class JensenSeaton(IsothermBaseModel):
    r"""
    Jensen-Seaton isotherm model.

    .. math::

        n(p) = K p \Big[1 + \Big(\frac{K p}{(a (1 + b p)}\Big)^c\Big]^{-1/c}

    Notes
    -----
    When modelling adsorption in micropores, a requirement was highlighted by
    Jensen and Seaton in 1996 [#]_, that at sufficiently high pressures the
    adsorption isotherm should not reach a horizontal plateau corresponding
    to saturation but that this asymptote should continue to rise due to
    the compression of the adsorbate in the pores. They came up with a
    semi-empirical equation to describe this phenomenon based on a function
    that interpolates between two asymptotes: the Henry’s law asymptote
    at low pressure and an asymptote reflecting the compressibility of the
    adsorbate at high pressure.

    Here :math:`K` is the Henry constant, :math:`b` is the compressibility of the
    adsorbed phase and :math:`c` an empirical constant.

    The equation can be used to model both absolute and excess adsorption as
    the pore volume can be incorporated into the definition of :math:`b`,
    although this can lead to negative adsorption slopes for the
    compressibility asymptote. This equation has been found to provide a
    better fit for experimental data from microporous solids than the Langmuir
    or Toth equation, in particular for adsorbent/adsorbate systems with
    high Henry’s constants where the amount adsorbed increases rapidly at
    relatively low pressures and then slows down dramatically.

    References
    ----------
    .. [#] Jensen, C. R. C.; Seaton, N. A., An Isotherm Equation for Adsorption to High
       Pressures in Microporous Adsorbents. Langmuir 1996, 12, (Copyright (C) 2012
       American Chemical Society (ACS). All Rights Reserved.), 2866-2867.

    """

    # Model parameters
    name = 'JensenSeaton'
    calculates = 'loading'
    param_names = ["K", "a", "b", "c"]
    param_bounds = {
        "K": [0., numpy.inf],
        "a": [0., numpy.inf],
        "b": [0., numpy.inf],
        "c": [0., numpy.inf],
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
        return self.params["K"] * pressure / \
            (1 + (self.params["K"] * pressure /
                  (self.params["a"] * (1 + self.params["b"] * pressure))
                  )**self.params['c'])**(1 / self.params['c'])

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the Jensen-Seaton model, the pressure will
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

        opt_res = scipy.optimize.root(fun, 0, method='hybr')

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

        The integral for the Jensen-Seaton model cannot be solved analytically
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

        guess = {"K": saturation_loading * langmuir_k, "a": 1, "b": 1, "c": 1}

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess
