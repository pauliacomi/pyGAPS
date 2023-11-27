"""Jensen-Seaton isotherm model."""

import numpy
from scipy import integrate
from scipy import optimize

from pygaps.modelling.base_model import IsothermBaseModel
from pygaps.utilities.exceptions import CalculationError


class JensenSeaton(IsothermBaseModel):
    r"""
    Jensen-Seaton isotherm model.

    .. math::

        n(p) = K p \Big[1 + \Big(\frac{K p}{(n_m (1 + k p)}\Big)^t\Big]^{-1/t}

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

    Here :math:`K` is the Henry constant, :math:`k` is the compressibility of the
    adsorbed phase and :math:`t` an empirical constant.

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
       Pressures in Microporous Adsorbents. Langmuir 1996, 12, 2866-2867.

    """

    # Model parameters
    name = 'JensenSeaton'
    formula = r"n(p) = K p [1 + (\frac{K p}{(n_m (1 + k p)})^t]^{-1/t}"
    calculates = 'loading'
    param_names = ("K", "n_m", "k", "t")
    param_default_bounds = (
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
        (1e-3, numpy.inf),
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
        Kp = self.params["K"] * pressure
        n_m = self.params["n_m"]
        k = self.params["k"]
        t = self.params["t"]
        return Kp / (1 + (Kp / (n_m * (1 + k * pressure)))**t)**(1 / t)

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
        guess = {"K": langmuir_k, "n_m": saturation_loading, "k": 0.1, "t": 1}
        guess = self.initial_guess_bounds(guess)
        print(guess)
        return guess
