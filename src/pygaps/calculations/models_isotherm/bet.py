"""
BET isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class BET(IsothermModel):
    """
    Brunauer-Emmett-Teller (BET) adsorption isotherm

    .. math::

        L(P) = M\\frac{C P}{(1-K_B P)(1-K_B P+ C P)}

    Notes
    -----

    The BET model [#]_ assumes that adsorption happens on the surface of the material in
    incremental layers according to several assumptions:

        * The adsorption sites are equivalent, and therefore the surface is heterogeneous
        * There are no lateral interactions between adsorbed molecules
        * The adsorption happens in layers, with adsorbed molecules acting as adsorption
          sites for new molecules
        * The adsorption energy of a molecule on the second and higher layers equals
          the condensation energy of the adsorbent :math:`E_L`.

    A particular surface percentage :math:`\\theta_x` is occupied with x layers.
    For each layer at equilibrium, the adsorption and desorption rates must be equal. We can
    then apply the Langmuir theory for each layer.

    .. math::

        k_{a_1} p \\theta_0 &= k_{d_1} \\theta_1 \\exp{(-\\frac{E_1}{RT})}

        k_{a_2} p \\theta_1 &= k_{d_2} \\theta_2 \\exp{(-\\frac{E_L}{RT})}

        ...

        k_{a_i} p \\theta_{i-1} &= k_{d_i} \\theta_i \\exp{-\\frac{E_L}{RT}}

    Since we are assuming that all layers beside the first have the same properties,
    we can define :math:`g= \\frac{k_{d_2}}{k_{a_2}} = \\frac{k_{d_3}}{k_{a_3}} = ...`.
    The coverages :math:`\\theta` can now be expressed in terms of :math:`\\theta_0`.

    .. math::

        \\theta_1 &= y \\theta_0 \\quad where \\quad y = \\frac{k_{a_1}}{k_{d_1}} p \\exp{(-\\frac{E_1}{RT})}

        \\theta_2 &= x \\theta_1 \\quad where \\quad x = \\frac{p}{g} \\exp{(-\\frac{E_L}{RT})}

        \\theta_3 &= x \\theta_2 = x^2 \\theta_1

        ...

        \\theta_i &= x^{i-1} \\theta_1 = y x^{i-1} \\theta_0

    A constant C may be defined such that

    .. math::

        C = \\frac{y}{x} = \\frac{k_{a_1}}{k_{d_1}} g \\exp{(\\frac{E_1 - E_L}{RT})}

        \\theta_i = C x^i \\theta_0

    For all the layers, the equations can be summed:

    .. math::

        \\frac{n}{n_m} = \\sum_{i=1}^{\\infty} i \\theta^i = C \\sum_{i=1}^{\\infty} i x^i \\theta_0

    Since

    .. math::

        \\theta_0 = 1 - \\sum_{1}^{\\infty} \\theta_i

        \\sum_{i=1}^{\\infty} i x^i = \\frac{x}{(1-x)^2}

    Then we obtain the BET equation

    .. math::

        L(P) = \\frac{n}{n_m} = M\\frac{C P}{(1-K_B P)(1-K_B P+ C P)}

    References
    ----------
    .. [#] “Adsorption of Gases in Multimolecular Layers”, Stephen Brunauer,
       P. H. Emmett and Edward Teller, J. Amer. Chem. Soc., 60, 309(1938)

    """
    #: Name of the model
    name = 'BET'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M": numpy.nan, "C": numpy.nan, "Kb": numpy.nan}

    def loading(self, pressure):
        """
        Function that calculates loading

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """
        return self.params["M"] * self.params["C"] * pressure / (
            (1.0 - self.params["Kb"] * pressure) *
            (1.0 - self.params["Kb"] * pressure +
             self.params["C"] * pressure))

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the BET model, the pressure will
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

        opt_res = scipy.optimize.root(fun, 0, method='hybr')

        if not opt_res.success:
            raise CalculationError("""
            Root finding for value {0} failed.
            """.format(loading))

        return opt_res.x

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \\pi = \\int_{0}^{P_i} \\frac{n_i(P_i)}{P_i} dP_i

        The integral for the BET model is solved analytically.

        .. math::

            \\pi = M \\ln{\\frac{1 - K_b P + C P}{1- K_b P}}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["M"] * numpy.log(
            (1.0 - self.params["Kb"] * pressure +
             self.params["C"] * pressure) /
            (1.0 - self.params["Kb"] * pressure))

    def default_guess(self, data, loading_key, pressure_key):
        """
        Returns initial guess for fitting

        Parameters
        ----------
        data : pandas.DataFrame
            Data of the isotherm.
        loading_key : str
            Column with the loading.
        pressure_key : str
            Column with the pressure.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        """
        saturation_loading, langmuir_k = super(BET, self).default_guess(
            data, loading_key, pressure_key)

        # BET = Langmuir when Kb = 0.0. This is our default assumption.
        return {"M": saturation_loading, "C": langmuir_k,
                "Kb": langmuir_k * 0.01}
