"""
Temkin Approximation isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class TemkinApprox(IsothermModel):
    """
    Asymptotic approximation to the Temkin Isotherm

    .. math::

        n(p) = n_M \\frac{K p}{1 + K p} + n_M \\theta (\\frac{K p}{1 + K p})^2 (\\frac{K p}{1 + K p} -1)

    Notes
    -----

    The Temkin adsorption isotherm [#]_, like the Langmuir model, considers
    a surface with n_M identical adsorption sites, but takes into account adsorbate-
    adsorbate interactions by assuming that the heat of adsorption is a linear
    function of the coverage. The Temkin isotherm is derived [#]_ using a
    mean-field argument and used an asymptotic approximation
    to obtain an explicit equation for the loading.

    Here, :math:`n_M` and K have the same physical meaning as in the Langmuir model.
    The additional parameter :math:`\\theta` describes the strength of the adsorbate-adsorbate
    interactions (:math:`\\theta < 0` for attractions).

    References
    ----------
    .. [#]  V. P. M.I. Tempkin, Kinetics of ammonia synthesis on promoted iron
       catalyst, Acta Phys. Chim. USSR 12 (1940) 327–356.
    .. [#] Phys. Chem. Chem. Phys., 2014,16, 5499-5513

    """
    #: Name of the model
    name = 'TemkinApprox'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"n_M": numpy.nan, "K": numpy.nan, "tht": numpy.nan}

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
        langmuir_fractional_loading = self.params["K"] * pressure / \
            (1.0 + self.params["K"] * pressure)
        return self.params["n_M"] * (langmuir_fractional_loading +
                                     self.params["tht"] * langmuir_fractional_loading ** 2 *
                                     (langmuir_fractional_loading - 1))

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the TemkinApprox model, the pressure will
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

        The integral for the TemkinApprox model is solved analytically.

        .. math::

            \\pi = n_M (\\ln{1+ K p} \\frac{\\theta (2 K p +1)}{2(1 + K p)^2})

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        one_plus_kp = 1.0 + self.params["K"] * pressure
        return self.params["n_M"] * (numpy.log(one_plus_kp) +
                                     self.params["tht"] * (2.0 * self.params["K"] * pressure + 1.0) /
                                     (2.0 * one_plus_kp ** 2))

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
        saturation_loading, langmuir_k = super(TemkinApprox, self).default_guess(
            data, loading_key, pressure_key)

        return {"n_M": saturation_loading, "K": langmuir_k, "tht": 0.0}
