"""GAB isotherm model."""

import numpy

from pygaps.modelling.base_model import IsothermBaseModel


class GAB(IsothermBaseModel):
    r"""
    Guggenheim-Anderson-de Boer (GAB) adsorption isotherm.

    .. math::

        n(p) = n_m \frac{C K p}{(1 - K p)(1 - K p + C K p)}

    Notes
    -----
    An extension of the BET model which introduces a constant
    K, accounting for a different enthalpy of adsorption of
    the adsorbed phase when compared to liquefaction enthalpy of
    the bulk phase.

    It is often used to fit adsorption and desorption isotherms of
    water in the food industry. [#]_

    References
    ----------
    .. [#] “Water Activity: Theory and Applications to Food”, Kapsalis. J. G., 1987
    """

    # Model parameters
    name = 'GAB'
    formula = r"n(p) = n_m \frac{C K p}{(1 - K p)(1 - K p + K C p)}"
    calculates = 'loading'
    param_names = ("n_m", "C", "K")
    param_default_bounds = (
        (0, numpy.inf),
        (0, numpy.inf),
        (0, 1),
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
        nm = self.params['n_m']
        C = self.params['C']
        Kp = self.params['K'] * pressure
        return nm * C * Kp / ((1.0 - Kp) * (1.0 - Kp + C * Kp))

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the BET model, an analytical inversion is possible.
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
        nm = self.params['n_m']
        C = self.params['C']
        K = self.params['K']

        x = loading * (1 - C) * K**2
        y = (loading * (C - 2) - nm * C) * K

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

        The integral for the GAB model is solved analytically.

        .. math::

            \pi = n_m \ln{\frac{1 - K p + C K p}{1- K p}}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        nm = self.params['n_m']
        C = self.params['C']
        Kp = self.params['K'] * pressure
        return nm * numpy.log((1.0 - Kp + C * Kp) / (1.0 - Kp))

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
        guess = {"n_m": saturation_loading, "C": 10 * langmuir_k, "K": 0.01}
        guess = self.initial_guess_bounds(guess)
        return guess
