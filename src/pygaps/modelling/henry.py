"""Henry isotherm model."""

import numpy

from pygaps.modelling.base_model import IsothermBaseModel


class Henry(IsothermBaseModel):
    r"""
    Henry's law. Assumes a linear dependence of adsorbed amount with pressure.

    .. math::

        n(p) = K_H p

    Notes
    -----
    The simplest method of describing adsorption on a
    surface is Henry’s law. It assumes only interactions
    with the adsorbate surface and is described by a
    linear dependence of adsorbed amount with
    increasing pressure.

    It is derived from the Gibbs isotherm, by substituting
    a two dimensional analogue to the ideal gas law.
    From a physical standpoint, Henry's law is unrealistic as
    adsorption sites
    will saturate at higher pressures. However, the constant kH,
    or Henry’s constant, can be thought of as a measure of the strength
    of the interaction of the probe gas with the surface. At very
    low concentrations of gas there is a
    thermodynamic requirement for the applicability of Henry's law.
    Therefore, most models reduce to the Henry equation
    as :math:`\lim_{p \to 0} n(p)`.

    Usually, Henry's law is unrealistic because the adsorption sites
    will saturate at higher pressures.
    Only use if your data is linear.

    """

    # Model parameters
    name = 'Henry'
    formula = r"n(p) = K_H p"
    calculates = 'loading'
    param_names = ("K")
    param_default_bounds = ((0., numpy.inf), )

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
        return self.params["K"] * pressure

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        For the Henry model, a direct relationship can be found
        by rearranging the function.

        .. math::

            p = n / K_H

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return loading / self.params["K"]

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the Henry model is solved analytically.

        .. math::

            \pi = K_H p

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["K"] * pressure

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
        return 0

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
        guess = {"K": saturation_loading * langmuir_k}
        guess = self.initial_guess_bounds(guess)
        return guess
