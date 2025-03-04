"""Langmuir isotherm model."""

import numpy

from pygaps.modelling.base_model import IsothermBaseModel


class Langmuir(IsothermBaseModel):
    r"""
    Langmuir isotherm model.

    .. math::

        n(p) = n_m\frac{K p}{1 + K p}

    Notes
    -----
    The Langmuir theory [#]_, proposed at the start of the 20th century, states that
    adsorption takes place on specific sites on a surface, until
    all sites are occupied.
    It was originally derived from a kinetic model of gas adsorption and
    is based on several assumptions.

    * All sites are equivalent and have the same chance of being occupied
    * Each adsorbate molecule can occupy one adsorption site
    * There are no interactions between adsorbed molecules
    * The rates of adsorption and desorption are proportional to the number of
      sites currently free and currently occupied, respectively
    * Adsorption is complete when all sites are filled.

    Using these assumptions we can define rates for both adsorption and
    desorption. The adsorption rate :math:`r_a`
    will be proportional to the number of sites available on
    the surface, as well as the number of molecules in the gas,
    which is given by pressure.
    The desorption rate :math:`r_d`, on the other hand, will
    be proportional to the number of occupied sites and the energy
    of adsorption. It is also useful to define
    :math:`\theta = n_{ads}/n_{ads}^m` as the fractional
    surface coverage, the number of sites occupied divided by the total
    sites. At equilibrium, the rate of adsorption and the rate of
    desorption are equal, therefore the two equations can be combined.
    The equation can then be arranged to obtain an expression for the
    loading called the Langmuir model. Mathematically:

    .. math::

        r_a = k_a p (1 - \theta)

        r_d = k_d \theta \exp{\Big(-\frac{E_{ads}}{R_g T}\Big)}

    At equilibrium, the rate of adsorption and the rate of
    desorption are equal, therefore the two equations can be combined.

    .. math::

        k_a p (1 - \theta) = k_d \theta \exp{\Big(-\frac{E_{ads}}{R_gT}\Big)}

    Rearranging to get an expression for the loading, the Langmuir equation becomes:

    .. math::

        n(p) = n_m \frac{K p}{1 + K p}

    Here, :math:`n_m` is the moles adsorbed at the completion of the
    monolayer, and therefore the maximum possible loading.
    The Langmuir constant is the product of the individual desorption
    and adsorption constants :math:`k_a` and :math:`k_d` and exponentially
    related to the energy of adsorption
    :math:`\exp{(-\frac{E}{RT})}`.

    References
    ----------
    .. [#] I. Langmuir, J. American Chemical Society 38, 2219(1916); 40, 1368(1918)

    """

    # Model parameters
    name = 'Langmuir'
    formula = r"n(p) = n_m\frac{K p}{1 + K p}"
    calculates = 'loading'
    param_names = ("K", "n_m")
    param_default_bounds = (
        (0., numpy.inf),
        (0., numpy.inf),
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
        kp = self.params["K"] * pressure
        return self.params["n_m"] * kp / (1.0 + kp)

    def pressure(self, loading):
        r"""
        Calculate pressure at specified loading.

        For the Langmuir model, a direct relationship can be found
        by rearranging the function.

        .. math::

            p = \frac{n}{K (n_m - n)}

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return loading / (self.params["K"] * (self.params["n_m"] - loading))

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the Langmuir model is solved analytically.

        .. math::

            \pi = n_m \log{1 + K p}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["n_m"] * numpy.log(1.0 + self.params["K"] * pressure)

    def toth_correction(self, pressure):
        r"""
        Calculate T\'oth correction, $\Psi$ to the Polanyi adsorption
        potential, $\varepsilon_{ads}$ at specified pressure.

        .. math::
            \varepsilon_{ads} = RT \ln{\frac{\Psi P_{sat}{P}}} \\
            \Psi = \left. \frac{n}{P} \frac{\mathrm{d}P}{\mathrm{d}n} \right| - 1

        For the Langmuir model;
            .. math::
                \Psi = KP

        Model parameters must be derived from isotherm with pressure in Pa.

        Parameters
        ---------
        pressure : float
            The pressure at which to calculate the T\'oth correction

        Returns
        ------
            The T\'oth correction, $\Psi$
        """
        return self.params["K"] * pressure

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
        guess = {"n_m": saturation_loading, "K": langmuir_k}
        guess = self.initial_guess_bounds(guess)
        return guess
