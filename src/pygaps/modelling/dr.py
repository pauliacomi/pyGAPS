"""Dubinin-Radushkevitch isotherm model."""

import numpy

from .. import scipy
from .base_model import IsothermBaseModel


class DR(IsothermBaseModel):
    r"""
    Dubinin-Radushkevitch (DR) adsorption isotherm.

    .. math::

        n(p) = n_t \exp\Big[-\Big(\frac{-RT\ln(p/p_0)}{\varepsilon}\Big)^{2}\Big]

    The pressure passed should be in a relative basis.

    Notes
    -----
    The Dubinin-Radushkevich isotherm model [#]_ extends the potential theory
    of Polanyi, which asserts that molecules
    near a surface are subjected to a potential field.
    The adsorbate at the surface is in a liquid state and
    its local pressure is conversely equal to the vapour pressure
    at the adsorption temperature. The Polanyi theory attempts to
    relate the surface coverage with the Gibbs free energy of adsorption,
    :math:`\Delta G^{ads} = - R T \ln p/p_0` and the total coverage
    :math:`\theta`.

    There are two parameters which define the model:

        * The total amount adsorbed (`n_t`), analogous to the monolayer
          capacity in the Langmuir model.
        * A potential energy term `e`.

    It describes adsorption in a single uniform type of pores. To note
    that the model does not reduce to Henry's law at low pressure
    and is therefore not strictly physical.

    References
    ----------
    .. [#] B. P. Bering, M. M. Dubinin, and V. V. Serpinsky,
       “Theory of volume filling for vapor adsorption,”
       Journal of Colloid and Interface Science, vol. 21, no. 4, pp. 378–393, Apr. 1966.

    """
    # Model parameters
    name = 'DR'
    calculates = 'loading'
    param_names = ["n_m", "e"]
    param_bounds = {
        "n_m": [0, numpy.inf],
        "e": [0, numpy.inf],
    }
    minus_rt = -1000  # base value

    def __init_parameters__(self, parameters):
        """Initialize model parameters from isotherm data."""
        self.minus_rt = -scipy.const.gas_constant * parameters['temperature']

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
        return self.params["n_m"] * \
            numpy.exp(-(self.minus_rt * numpy.log(pressure) / self.params["e"]) ** 2)

    def pressure(self, loading):
        r"""
        Calculate pressure at specified loading.

        For the DR model, a direct relationship can be found analytically.

        .. math::

            p/p_0 = \exp\Big( -\frac{\varepsilon}{RT}\sqrt{-\ln n/n_m} \Big)

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.

        """
        return numpy.exp(
            self.params['e'] / self.minus_rt *
            numpy.sqrt(-numpy.log(loading / self.params['n_m']))
        )

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

        The integral for the DR model cannot be solved analytically
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
        return scipy.integrate.quad(
            lambda x: self.loading(x) / x, 0, pressure
        )[0]

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

        guess = {"n_m": saturation_loading, "e": -self.minus_rt}

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess
