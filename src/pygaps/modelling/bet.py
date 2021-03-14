"""BET isotherm model."""

import numpy

from .base_model import IsothermBaseModel


class BET(IsothermBaseModel):
    r"""
    Brunauer-Emmett-Teller (BET) adsorption isotherm.

    .. math::

        n(p) = n_m \frac{C p}{(1 - N p)(1 - N p + C p)}

    Notes
    -----
    Like the Langmuir model, the BET model [#]_
    assumes that adsorption is kinetically driven and takes place on
    adsorption sites at the material surface. However, each adsorbed
    molecule becomes, in itself, a secondary adsorption site, such
    that incremental layers are formed. The conditions imagined by
    the BET model are:

        * The adsorption sites are equivalent, and therefore the surface is heterogeneous
        * There are no lateral interactions between adsorbed molecules
        * The adsorption occurs in layers, with adsorbed molecules acting
          as adsorption sites for new molecules
        * The adsorption energy of a molecule on the second and higher
          layers equals the condensation energy of the adsorbent :math:`E_L`.

    A particular surface percentage :math:`\theta_x` is occupied with x layers.
    For each layer at equilibrium, the adsorption and desorption rates must be
    equal. We can then apply the Langmuir theory for each layer. It is assumed
    that the adsorption energy of a molecule on the second and higher layers is
    just the condensation energy of the adsorbent :math:`E_{i>1} = E_L`.

    .. math::

        k_{a_1} p \theta_0 &= k_{d_1} \theta_1 \exp{(-\frac{E_1}{R_gT})}

        k_{a_2} p \theta_1 &= k_{d_2} \theta_2 \exp{(-\frac{E_L}{R_gT})}

        ...

        k_{a_i} p \theta_{i-1} &= k_{d_i} \theta_i \exp{-\frac{E_L}{R_gT}}

    Since we are assuming that all layers beside the first have the same properties,
    we can define :math:`g= \frac{k_{d_2}}{k_{a_2}} = \frac{k_{d_3}}{k_{a_3}} = ...`.
    The coverages :math:`\theta` can now be expressed in terms of :math:`\theta_0`.

    .. math::

        \theta_1 &= y \theta_0 \quad where \quad y = \frac{k_{a_1}}{k_{d_1}} p \exp{(-\frac{E_1}{R_gT})}

        \theta_2 &= x \theta_1 \quad where \quad x = \frac{p}{g} \exp{(-\frac{E_L}{R_gT})}

        \theta_3 &= x \theta_2 = x^2 \theta_1

        ...

        \theta_i &= x^{i-1} \theta_1 = y x^{i-1} \theta_0

    A constant C may be defined such that

    .. math::

        C = \frac{y}{x} = \frac{k_{a_1}}{k_{d_1}} g \exp{(\frac{E_1 - E_L}{R_gT})}

        \theta_i = C x^i \theta_0

    For all the layers, the equations can be summed:

    .. math::

        \frac{n}{n_m} = \sum_{i=1}^{\infty} i \theta^i = C \sum_{i=1}^{\infty} i x^i \theta_0

    Since

    .. math::

        \theta_0 = 1 - \sum_{1}^{\infty} \theta_i

        \sum_{i=1}^{\infty} i x^i = \frac{x}{(1-x)^2}

    Then we obtain the BET equation

    .. math::

        n(p) = \frac{n}{n_m} = n_m\frac{C p}{(1-N p)(1-N p+ C p)}

    The BET constant C is exponentially proportional to the
    difference between the surface adsorption energy and the
    intermolecular attraction, and can be seen to influence the knee
    a BET-type isotherm has at low pressure, before statistical
    monolayer formation.

    References
    ----------
    .. [#] “Adsorption of Gases in Multimolecular Layers”, Stephen Brunauer,
       P. H. Emmett and Edward Teller, J. Amer. Chem. Soc., 60, 309(1938)

    """

    # Model parameters
    name = 'BET'
    calculates = 'loading'
    param_names = ["n_m", "C", "N"]
    param_bounds = {
        "n_m": [0, numpy.inf],
        "C": [0, numpy.inf],
        "N": [0, numpy.inf],
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
        return self.params["n_m"] * self.params["C"] * pressure / (
            (1.0 - self.params["N"] * pressure) *
            (1.0 - self.params["N"] * pressure + self.params["C"] * pressure)
        )

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
        a = self.params['n_m']
        b = self.params['N']
        c = self.params['C']

        x = loading * b * (b - c)
        y = loading * c - 2 * loading * b - a * c

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

        The integral for the BET model is solved analytically.

        .. math::

            \pi = n_m \ln{\frac{1 - N p + C p}{1- N p}}

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
            (1.0 - self.params["N"] * pressure + self.params["C"] * pressure) /
            (1.0 - self.params["N"] * pressure)
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

        guess = {"n_m": saturation_loading, "C": langmuir_k, "N": 0.01}

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess
