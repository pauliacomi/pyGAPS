"""ChemiPhysisorption (CP) isotherm model."""

import numpy
from scipy import constants
from scipy import integrate
from scipy import optimize

from pygaps.modelling.base_model import IsothermBaseModel
from pygaps.utilities.exceptions import CalculationError


class ChemiPhysisorption(IsothermBaseModel):
    r"""
    ChemiPhysisorption isotherm model.

    .. math::

        n(p) = n_{m_1}\frac{K_1 p}{\sqrt[t_1]{1+(K_1 p)^{t_1}}} +
        \right[ n_{m_2}\frac{K_2 p}{1+K_2 p} ]\left \exp(\frac{-Ea}{RT})

    Notes
    -----
    A recently (2023) proposed model by the Petit group. It is an adaptation of
    the Dual-Site Toth model, and can be distinguished by the fact that the
    exponent (t) is 1 for the chemisorption portion (i.e. it is a Langmuir
    isotherm)[#]_. Further, the model assumes that at a given activation
    energy, E_a, molecules will have sufficient energy to take part in
    chemisorption, thus the chemisorption term is multiplied by an Arrhenius
    term;

    .. math::
        n(p) = n_{m_1}\frac{K_1 p}{\sqrt[t_1]{1+(K_1 p)^{t_1}}} +
        \right[ n_{m_2}\frac{K_2 p}{1+K_2 p} ]\left \exp(\frac{-Ea}{RT})

    This was applied by the Petit group to CO_2 isotherms measured at
    temperatures in the range 288-393 K, and pressures up to 1 bar.

    References
    ----------
    .. [#] Low, M-Y A.; Danaci, D.; Azzan, H.; Woodward, R. T.; Petit, C.
       (2023). Measurement of Physicochemical Properties and CO2, N2, Ar, O2 and
       H2O Unary Adsorption Isotherms of Purolite A110 and Lewatit VP OC 1065 for
       Application in Direct Air Capture. J. Chem. Eng. Data.
    """

    # Model parameters
    name = 'ChemiPhysisorption'
    formula = r"n_{m_1}\frac{K_1 p}{\sqrt[t_1]{1+(K_1 p)^{t_1}}} + \right[n_{m_2}\frac{K_2 p}{1+K_2 p} ]\left \exp(\frac{-Ea}{RT})"
    calculates = 'loading'
    param_names = (
        "n_m1",
        "K1",
        "t1",
        "n_m2",
        "K2",
        "Ea",
    )
    param_default_bounds = (
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
        (0., numpy.inf),
    )
    rt = 1000

    def __init_parameters__(self, params):
        "Initialise model parameters from isotherm data"
        self.rt = constants.gas_constant * params['temperature']

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
        t1 = self.params["t1"]
        Ea = self.params["Ea"]
        return ((self.params['n_m1'] * K1p / (1.0 + (K1p)**t1)**(1 / t1)) +
                ((self.params['n_m2'] * K2p / (1.0 + K2p)) * (numpy.exp(-Ea / self.rt))))

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the Dual Site Toth model, the pressure will be computed numerically
        An analytical inversion of this equation may be possible.

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
                    \right] - 1

        For the ChemiPhysisorption model, this inclues an extra term, $\gamma =
        \exp{\frac{-E_a}{RT}}$, so the expression becomes

            ..math::
                \Psi = \left[
                \frac{
                \frac{n_{m_1}K_1}{\left(1+(K_1 P)^t\right)^{\frac{1}{t}}}
                + \frac{\gamma n_{m_2} K_2}{1+KP}
                }{
                \frac{n_{m_1 K_1}}{\left(1 + (K_1 P)^t \right)^{\frac{t+1}{t}}} +  \frac{\gamma n_{m_2} K_2}{\left(1+KP\right)^2}
                }
                \right] - 1

        Model parameters must be derived from isotherm with pressure in Pa.

        Parameters
        ---------
        pressure : float
            The pressure at which to calculate the T\'oth correction

        Returns
        ------
            The T\'oth correction, $\Psi$
        """

        def dn_dP_singlesite(gamma, nm, K, t):
            Kpt = (K * pressure)**t
            gammanmK = gamma * nm * K
            return gammanmK / ((1 + Kpt))**((t + 1) / t)

        gamma = numpy.exp(- self.params["Ea"] / self.rt)

        dP_dn = 1 / (
            dn_dP_singlesite(
                1,
                self.params["n_m1"],
                self.params["K1"],
                self.params["t"]
            ) +
            dn_dP_singlesite(
                gamma,
                self.params["n_m2"],
                self.params["K2"],
                1
            )
        )

        return ((self.loading(pressure) / pressure) / dP_dn) - 1

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
            "Ea": self.rt * numpy.exp(1),
        }
        guess = self.initial_guess_bounds(guess)
        return guess
