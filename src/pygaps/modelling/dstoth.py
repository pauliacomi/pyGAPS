"""Double Site Toth isotherm model."""

import numpy
from scipy import integrate
from scipy import optimize

from pygaps.modelling.base_model import IsothermBaseModel
from pygaps.utilities.exceptions import CalculationError


class DSToth(IsothermBaseModel):
    r"""
    Dual-site Toth adsorption isotherm.

    .. math::

        n(p) = n_{m_1}\frac{K_1 p}{\sqrt[t_1]{1 + (K_1 p)^{t_1}}} +
        n_{m_2}\frac{K_2 p}{\sqrt[t_2]{1+(K_2 p)^{t_2}}}

    Notes
    -----
    An extension to the Toth model to consider two adsorption sites, with
    different monolayer capacities, affinities, and exponents[#]_. This was
    first proposed by Serna-Guerrero, Balmabkhout, and Sayari to model ambient
    temperature CO2 isotherms up to 20 bar, with the two sites representing
    chemical and physical adsorption, respectively[#]_.

    .. math::

        n(p) = \sum_i n_{m_i} \frac{K_i p}{\sqrt[t_i]{1+(K_i p)**{t_i}}}

    In practice, thus far only two adsorption sites (chemical and physical
    adsorption) are considered.

    .. math::
        n(p) = n_{m_1}\frac{K_1 p}{\sqrt[t_1]{1+(K_1 p)^{t_1}}} +
        n_{m_2}\frac{K_2 p}{\sqrt[t_2]{1+(K_2 p)^{t_2}}}

    In Serna-Guerrero et al.'s original work, the physical part of the equation
    is determined by measurement of a CO_2 isotherm on an adsorbent which should
    be expected to have no chemical adsorption component. It nonetheless appears
    to give a good fit to CO_2 isotherms when each of the sites are determined
    independently.

    References
    ----------
    .. [#] Serna-Guerrero, R., Belmabkhout, Y., & Sayari, A. (2010). Modeling
       CO2 adsorption on amine-functionalized mesoporous silica: 1. A
       semi-empirical equilibrium model. Chemical Engineering Journal, 161(1-2), 173-181.
    """

    # Model parameters
    name = 'DSToth'
    formula = r"n(p) = n_{m_1}\frac{K_1 p}{\sqrt[t_1]{1+(K_1 p)^{t_1}}} + n_{m_2}\frac{K_2 p}{\sqrt[t_2]{1+(K_2 p)^{t_2}}}"
    calculates = 'loading'
    param_names = ("n_m1", "K1", "t1", "n_m2", "K2", "t2")
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
        K1p = self.params["K1"] * pressure
        K2p = self.params["K2"] * pressure
        t1 = self.params['t1']
        t2 = self.params['t2']
        return ((self.params['n_m1'] * K1p / (1.0 + (K1p)**t1)**(1 / t1)) +
                (self.params['n_m2'] * K2p / (1.0 + (K2p)**t2)**(1 / t2)))

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the Dual Site Toth model, an analytical inversion of this
        equation is be possible; see code.


        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        def single_site(loading, n_m, K, t):
            theta = loading / n_m
            return theta / (K * ((1 - (theta**t))**(1 / t)))

        return (
            single_site(
                loading,
                self.params["n_m1"], self.params["K1"], self.params["t1"]
            ) +
            single_site(
                loading,
                self.params["n_m2"], self.params["K2"], self.params["t2"]
            )
        )

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the DSToth model cannot be solved analytically
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

    def toth_correction(self, pressure):
        r"""
        Calculate T\'oth correction, $\Psi$ to the Polanyi adsorption
        potential, $\varepsilon_{ads}$ at specified pressure.

        .. math::
            \varepsilon_{ads} = RT \ln{\frac{\Psi P_{sat}{P}}} \\
            \Psi = \left. \frac{n}{P} \frac{\mathrm{d}P}{\mathrm{d}n} \right| - 1

        For the Multi-Site T\'oth model;
            .. math::
                \Psi &= \left[\frac{
                \sum_i{\frac{n_{m_i} K_i }{\left(1+(K_i P)^{t_i}\right)^{\frac{1}{t}}}}}
                {\sum_i{
                \frac{n_{m_i} K_i}{ \left(1+(K_i P)^{t_i}\right)^{\frac{t-1}{t}} }   }
                }
                    \right]
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
        K1Pt1 = (self.params["K1"] * pressure)**self.params["t1"]
        nm2K2 = self.params["n_m2"] * self.params["K2"]
        K2Pt2 = (self.params["K2"] * pressure)**self.params["t2"]

        n_P = (
            (nm1K1 / ((1 + K1Pt1)**self.params["t1"])) +
            (nm2K2 / ((1 + K2Pt2)**self.params["t2"]))
        )

        def dn_dP_singlesite(nm, K, t):
            Kpt = (K * pressure)**t
            nmK = nm * K
            return nmK / ((1 + Kpt)**((t + 1) / t))

        dP_dn = 1 / (
            dn_dP_singlesite(
                self.params["n_m1"],
                self.params["K1"],
                self.params["t1"]
            ) +
            dn_dP_singlesite(
                self.params["n_m2"],
                self.params["K2"],
                self.params["t2"]
            )
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
            "n_m1": 0.5 * saturation_loading,
            "K1": 0.4 * langmuir_k,
            "n_m2": 0.5 * saturation_loading,
            "K2": 0.6 * langmuir_k,
            "t1": 1,
            "t2": 1,
        }
        guess = self.initial_guess_bounds(guess)
        return guess
