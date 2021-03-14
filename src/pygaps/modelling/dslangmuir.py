"""Double Site Langmuir isotherm model."""

import numpy

from .base_model import IsothermBaseModel


class DSLangmuir(IsothermBaseModel):
    r"""
    Dual-site Langmuir adsorption isotherm.

    .. math::

        n(p) = n_{m_1}\frac{K_1 p}{1+K_1 p} +  n_{m_2}\frac{K_2 p}{1+K_2 p}

    Notes
    -----
    An extension to the Langmuir model is to consider the experimental isotherm to be
    the sum of several Langmuir-type isotherms with different monolayer capacities and
    affinities [#]_. The assumption is that the adsorbent presents several distinct
    types of homogeneous adsorption sites, and that separate Langmuir equations
    should be applied to each. This is particularly applicable in cases where the
    structure of the adsorbent suggests that different types of sites are present,
    such as in crystalline materials of variable chemistry like zeolites and MOFs.
    The resulting isotherm equation is:

    .. math::

        n(p) = \sum_i n_{m_i} \frac{K_i p}{1+K_i p}

    In practice, up to three adsorption sites are considered.
    This model is the dual-site model (:math:`i=2`)

    References
    ----------
    .. [#] Langmuir, I., The adsorption of gases on plane surfaces of glass, mica and platinum.
       J. Am. Chem. Soc. 1918, 40, 1361-1402.

    """

    # Model parameters
    name = 'DSLangmuir'
    calculates = 'loading'
    param_names = ["n_m1", "K1", "n_m2", "K2"]
    param_bounds = {
        "n_m1": [0., numpy.inf],
        "n_m2": [0., numpy.inf],
        "K1": [0., numpy.inf],
        "K2": [0., numpy.inf],
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
        k1p = self.params["K1"] * pressure
        k2p = self.params["K2"] * pressure
        return self.params["n_m1"] * k1p / (1.0 + k1p) + \
            self.params["n_m2"] * k2p / (1.0 + k2p)

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the Double Site Langmuir model, an analytical inversion is possible.
        See function code for implementation.

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        a = self.params['n_m1']
        b = self.params['K1']
        c = self.params['n_m2']
        d = self.params['K2']

        x = (a + c - loading) * b * d
        y = (a * b + c * d - loading * (b + d))

        res = (-y + numpy.sqrt(y**2 - 4 * x * (-loading))) / (2 * x)

        if numpy.isnan(res).any():
            res = numpy.nan_to_num(res, copy=False)

        return res

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the Double Site Langmuir model is solved analytically.

        .. math::

            \pi = n_{m_1} \log{1 + K_1 p} +  n_{m_2} \log{1 + K_2 p}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["n_m1"] * numpy.log(
            1.0 + self.params["K1"] * pressure) +\
            self.params["n_m2"] * numpy.log(
            1.0 + self.params["K2"] * pressure)

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

        guess = {
            "n_m1": 0.5 * saturation_loading,
            "K1": 0.4 * langmuir_k,
            "n_m2": 0.5 * saturation_loading,
            "K2": 0.6 * langmuir_k
        }

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess
