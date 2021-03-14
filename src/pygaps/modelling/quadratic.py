"""Quadratic isotherm model."""

import numpy

from .base_model import IsothermBaseModel


class Quadratic(IsothermBaseModel):
    r"""
    Quadratic isotherm model.

    .. math::

        n(p) = n_m \frac{p (K_a + 2 K_b p)}{1 + K_a p + K_b p^2}

    Notes
    -----
    The quadratic adsorption isotherm exhibits an inflection point; the loading
    is convex at low pressures but changes concavity as it saturates, yielding
    an S-shape. The S-shape can be explained by adsorbate-adsorbate attractive
    forces; the initial convexity is due to a cooperative
    effect of adsorbate-adsorbate attractions aiding in the recruitment of
    additional adsorbate molecules [#]_.

    The parameter :math:`K_a` can be interpreted as the Langmuir constant; the
    strength of the adsorbate-adsorbate attractive forces is embedded in :math:`K_b`.
    It is often useful in systems where the
    energy of guest-guest interactions is actually higher than
    the energy of adsorption, such as when adsorbing water
    on a hydrophobic surface.

    References
    ----------
    .. [#]  T. L. Hill, An introduction to statistical thermodynamics, Dover
       Publications, 1986.

    """

    # Model parameters
    name = 'Quadratic'
    calculates = 'loading'
    param_names = ["n_m", "Ka", "Kb"]
    param_bounds = {
        "n_m": [0, numpy.inf],
        "Ka": [-numpy.inf, numpy.inf],
        "Kb": [-numpy.inf, numpy.inf],
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
        return self.params["n_m"] * (
            self.params["Ka"] + 2.0 * self.params["Kb"] * pressure
        ) * pressure / (
            1.0 + self.params["Ka"] * pressure +
            self.params["Kb"] * pressure**2
        )

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the Quadratic model, an analytical inversion is possible.
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
        a = self.params['n_m']
        b = self.params['Ka']
        c = self.params['Kb']

        x = (loading - 2 * a) * c
        y = (loading - a) * b

        res = (-y - numpy.sqrt(y**2 - 4 * x * loading)) / (2 * x)

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

        The integral for the Quadratic model is solved analytically.

        .. math::

            \pi = n_m \ln{1+K_a p + K_b p^2}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["n_m"] * numpy.log(
            1.0 + self.params["Ka"] * pressure +
            self.params["Kb"] * pressure**2
        )

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
            "n_m": saturation_loading / 2.0,
            "Ka": langmuir_k,
            "Kb": langmuir_k**2.0
        }

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess
