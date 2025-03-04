"""Freundlich isotherm model."""

import numpy

from pygaps.modelling.base_model import IsothermBaseModel


class Freundlich(IsothermBaseModel):
    r"""
    Freundlich adsorption isotherm.

    .. math::

        n(p) = K p^{ 1/m }

    Warning: this model is not physically consistent as it
    does not converge to a maximum plateau.

    Notes
    -----
    The Freundlich [#]_ isotherm model is an empirical attempt to
    modify Henry's law in order to account for adsorption site
    saturation by using a decreasing slope with increased loading.
    It should be noted that the model never converges to a
    "maximum", and therefore is not strictly physically consistent.
    However, it is often good for fitting experimental data before
    complete saturation.

    There are two parameters which define the model:

    * A surface interaction constant `K` denoting the interaction with the
      material surface.
    * An exponential term `m` accounting for the decrease in available
      adsorption sites at higher loading.

    The model can also be derived from a more physical basis,
    using the potential theory of Polanyi, essentially resulting in
    a Dubinin-Astakov model where the exponential is equal to 1.

    References
    ----------
    .. [#] H. Freundlich "Über die Adsorption in Lösungen"
       Zeitschrift für Physikalische Chemie - Stöchiometrie und
       Verwandschaftslehre (1907), Volume 57, Issue 4, pages 385-470.

    """

    # Model parameters
    name = 'Freundlich'
    formula = r"n(p) = K p^{ 1/m }"
    calculates = 'loading'
    param_names = ("K", "m")
    param_default_bounds = (
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
        return self.params["K"] * pressure**(1 / self.params["m"])

    def pressure(self, loading):
        r"""
        Calculate pressure at specified loading.

        For the Freundlich model, a direct relationship can be found analytically.

        .. math::

            p = (n/K)^{m}

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.

        """
        return (loading / self.params['K'])**self.params['m']

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the Freundlich model is solved analytically.

        .. math::

            \pi = m K p^{ 1/m }

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        K = self.params["K"]
        m = self.params["m"]
        return m * K * pressure**(1 / m)

    def toth_correction(self, pressure: float) -> float:
        r"""
        Calculate T\'oth correction, $\Psi$ to the Polanyi adsorption
        potential, $\varepsilon_{ads}$ at specified pressure.

        .. math::
            \varepsilon_{ads} = RT \ln{\frac{\Psi P_{sat}{P}}} \\
            \Psi = \left. \frac{n}{P} \frac{\mathrm{d}P}{\mathrm{d}n} \right| - 1

        For the Henry model,
        ..math::
            \Psi = 0

        As a result $\varepsilon_{ads}$ is undefined.

        Model parameters must be derived from isotherm with pressure in Pa.

        Parameters
        ---------
        pressure : float
            The pressure at which to calculate the T\'oth correction

        Returns
        ------
            The T\'oth correction, $\Psi$
        """
        return self.params["m"] - 1

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
        guess = {"K": saturation_loading * langmuir_k, "m": 1}
        guess = self.initial_guess_bounds(guess)
        return guess
