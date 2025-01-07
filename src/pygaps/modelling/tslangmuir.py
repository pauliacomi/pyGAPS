"""Triple Site Langmuir isotherm model."""

import numpy
from scipy import optimize

from pygaps.modelling.base_model import IsothermBaseModel
from pygaps.utilities.exceptions import CalculationError


class TSLangmuir(IsothermBaseModel):
    r"""
    Triple-site Langmuir (TSLangmuir) adsorption isotherm

    .. math::

        n(p) = n_{m_1} \frac{K_1 p}{1+K_1 p} +  n_{m_2} \frac{K_2 p}{1+K_2 p} + n_{m_3} \frac{K_3 p}{1+K_3 p}

    Notes
    -----
    An extension to the Langmuir model is to consider the experimental isotherm
    to be the sum of several Langmuir-type isotherms with different monolayer
    capacities and affinities [#]_. The assumption is that the adsorbent
    material presents several distinct types of homogeneous adsorption sites,
    and that separate Langmuir equations should be applied to each. This is
    particularly applicable in cases where the structure of the adsorbent
    suggests that different types of sites are present, such as in crystalline
    materials of variable chemistry like zeolites and MOFs. The resulting
    isotherm equation is:

    .. math::

        n(p) = \sum_i n_{m_i}\frac{K_i p}{1+K_i p}

    In practice, up to three adsorption sites are considered.
    This model is the triple-site model (:math:`i=3`).

    References
    ----------
    .. [#] Langmuir, I., The adsorption of gases on plane surfaces of glass, mica and platinum.
       J. Am. Chem. Soc. 1918, 40, 1361-1402.

    """

    # Model parameters
    name = 'TSLangmuir'
    formula = r"n(p) = n_{m_1} \frac{K_1 p}{1+K_1 p} + n_{m_2} \frac{K_2 p}{1+K_2 p} + n_{m_3} \frac{K_3 p}{1+K_3 p}"
    calculates = 'loading'
    param_names = ["n_m1", "n_m2", "n_m3", "K1", "K2", "K3"]
    param_default_bounds = (
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
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
        k1p = self.params["K1"] * pressure
        k2p = self.params["K2"] * pressure
        k3p = self.params["K3"] * pressure
        return self.params["n_m1"] * k1p / (1.0 + k1p) + \
            self.params["n_m2"] * k2p / (1.0 + k2p) + \
            self.params["n_m3"] * k3p / (1.0 + k3p)

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the TS Langmuir model, the pressure will
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

        The integral for the Triple Site Langmuir model is solved analytically.

        .. math::

            \pi = n_{m_1} \log{1 + K_1 p} +  n_{m_2} \log{1 + K_2 p} + n_{m_3} \log{1 + K_3 p}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["n_m1"] * numpy.log(1.0 + self.params["K1"] * pressure) +\
            self.params["n_m2"] * numpy.log(1.0 + self.params["K2"] * pressure) +\
            self.params["n_m3"] * numpy.log(1.0 + self.params["K3"] * pressure)

    def toth_correction(self, pressure):
        r"""
        Calculate T\'oth correction, $\Psi$ to the Polanyi adsorption
        potential, $\varepsilon_{ads}$ at specified pressure.

        .. math::
            \varepsilon_{ads} = RT \ln{\frac{\Psi P_{sat}{P}}} \\
            \Psi = \left. \frac{n}{P} \frac{\mathrm{d}P}{\mathrm{d}n} \right| - 1

        For Multi-Site Langmuir models;
            .. math::
                \Psi = \left[ \sum_i{\frac{n_{m_i}K_i}{1 + K_i P}} \right] \left[ \sum_i{\frac{n_{m_i} K_i}{(1 + K_i P)^2}} \right]^{-1} - 1

        Model parameters must be derived from isotherm with pressure in Pa.

        Parameters
        ---------
        pressure : float
            The pressure at which to calculate the T\'oth correction

        Returns
        ------
            The T\'oth correction, $\Psi$
        """

        nm1K1 = self.params["n_m1"] * self.params["K1"]
        K1P = self.params["K1"] * pressure
        nm2K2 = self.params["n_m2"] * self.params["K2"]
        K2P = self.params["K2"] * pressure
        nm3K3 = self.params["n_m3"] * self.params["K3"]
        K3P = self.params["K3"] * pressure

        n_P = (nm1K1 / (1 + K1P)) + (nm2K2 / (1 + K2P)) + (nm3K3 / (1 + K3P))

        def dn_dP_singlesite(n_m, K):
            return (
                (n_m * K) / (1 + (K * pressure))**2
            )

        dP_dn = 1 / (
            dn_dP_singlesite(self.params["n_m1"], self.params["K1"]) +
            dn_dP_singlesite(self.params["n_m2"], self.params["K2"]) +
            dn_dP_singlesite(self.params["n_m3"], self.params["K3"])
        )

        return (n_P * dP_dn) - 1

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

        guess = {
            "n_m1": 0.4 * saturation_loading,
            "K1": 0.2 * langmuir_k,
            "n_m2": 0.4 * saturation_loading,
            "K2": 0.4 * langmuir_k,
            "n_m3": 0.2 * saturation_loading,
            "K3": 0.4 * langmuir_k
        }
        guess = self.initial_guess_bounds(guess)
        return guess
