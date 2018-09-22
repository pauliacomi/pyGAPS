"""
Quadratic isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class Quadratic(IsothermModel):
    """
    Quadratic isotherm model

    .. math::

        n(p) = n_M \\frac{(K_a + 2 K_b p)p}{1 + K_{a p} + K_{b p}^2}

    Notes
    -----

    The quadratic adsorption isotherm exhibits an inflection point; the loading
    is convex at low pressures but changes concavity as it saturates, yielding
    an S-shape. The S-shape can be explained by adsorbate-adsorbate attractive
    forces; the initial convexity is due to a cooperative
    effect of adsorbate-adsorbate attractions aiding in the recruitment of
    additional adsorbate molecules [#]_.

    The parameter :math:`K_a` can be interpreted as the Langmuir constant; the
    strength of the adsorbate-adsorbate attractive forces is embedded in :math:`K_b`.
    It is often useful in systems where the
    energy of guest-guest interactions is actually higher than
    the energy of adsorption, such as when adsorbing water
    on a hydrophobic surface.

    References
    ----------
    .. [#]  T. L. Hill, An introduction to statistical thermodynamics, Dover
       Publications, 1986.

    """
    #: Name of the model
    name = 'Quadratic'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"n_M": numpy.nan, "Ka": numpy.nan, "Kb": numpy.nan}

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
        return self.params["n_M"] * (self.params["Ka"] +
                                     2.0 * self.params["Kb"] * pressure) * pressure / (
            1.0 + self.params["Ka"] * pressure +
            self.params["Kb"] * pressure ** 2)

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the Quadratic model, the pressure will
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

            \\pi = \\int_{0}^{p_i} \\frac{n_i(p_i)}{p_i} dp_i

        The integral for the Quadratic model is solved analytically.

        .. math::

            \\pi = n_M \\ln{1+K_a p + K_b p^2}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["n_M"] * numpy.log(1.0 + self.params["Ka"] * pressure +
                                              self.params["Kb"] * pressure ** 2)

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
        saturation_loading, langmuir_k = super(Quadratic, self).default_guess(
            data, loading_key, pressure_key)

        return {"n_M": saturation_loading / 2.0, "Ka": langmuir_k,
                "Kb": langmuir_k ** 2.0}
