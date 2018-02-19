"""
Double Site Langmuir isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class DSLangmuir(IsothermModel):
    """
    Dual-site Langmuir (DSLangmuir) adsorption isotherm

    .. math::

        L(P) = M_1\\frac{K_1 P}{1+K_1 P} +  M_2\\frac{K_2 P}{1+K_2 P}

    Notes
    -----

    An extension to the Langmuir model is to consider the experimental isotherm to be
    the sum of several Langmuir-type isotherms with different monolayer capacities and affinities [#]_.
    The assumption is that the adsorbent presents several distinct types of homogeneous adsorption
    sites, and that separate Langmuir equations should be applied to each. This is particularly
    applicable in cases where the structure of the adsorbent suggests that different types of
    sites are present, such as in crystalline materials of variable chemistry like zeolites and MOFs.
    The resulting isotherm equation is:

    .. math::

        L(P) = \\sum_i M_i\\frac{K_i P}{1+K_i P}

    In practice, up to three adsorption sites are considered.
    This model is the dual-site model (:math:`i=2`)

    References
    ----------
    .. [#] Langmuir, I., The adsorption of gases on plane surfaces of glass, mica and platinum.
       J. Am. Chem. Soc. 1918, 40, 1361-1402.

    """
    #: Name of the model
    name = 'DSLangmuir'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M1": numpy.nan, "K1": numpy.nan,
                       "M2": numpy.nan, "K2": numpy.nan}

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
        # K_i P
        k1p = self.params["K1"] * pressure
        k2p = self.params["K2"] * pressure
        return self.params["M1"] * k1p / (1.0 + k1p) + \
            self.params["M2"] * k2p / (1.0 + k2p)

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the Double Site Langmuir model, the pressure will
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

        The integral for the Double Site Langmuir model is solved analytically.

        .. math::

            \\pi = M_1 \\log{1 + K_1 P} +  M_2 \\log{1 + K_2 P}

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["M1"] * numpy.log(
            1.0 + self.params["K1"] * pressure) +\
            self.params["M2"] * numpy.log(
            1.0 + self.params["K2"] * pressure)

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
        saturation_loading, langmuir_k = super(DSLangmuir, self).default_guess(
            data, loading_key, pressure_key)

        return {"M1": 0.5 * saturation_loading, "K1": 0.4 * langmuir_k,
                "M2": 0.5 * saturation_loading, "K2": 0.6 * langmuir_k}
