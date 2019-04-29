"""Dubinin-Radushkevitch isotherm model."""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .base_model import IsothermBaseModel


class DR(IsothermModel):
    r"""
    Dubinin-Radushkevitch (DR) adsorption isotherm.

    .. math::

        n(p) = n_t \exp\Big[\Big(-\frac{RT\ln(p_0/p)}{\varepsilon}\Big)^{2}\Big]

    Notes
    -----


    References
    ----------
    .. [#] B. P. Bering, M. M. Dubinin, and V. V. Serpinsky,
       “Theory of volume filling for vapor adsorption,”
       Journal of Colloid and Interface Science, vol. 21, no. 4, pp. 378–393, Apr. 1966.

    """
    #: Name of the model
    name = 'DR'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"n_m": numpy.nan, "C": numpy.nan, "N": numpy.nan}

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
        return self.params["n_m"] * self.params["C"] * pressure / (
            (1.0 - self.params["N"] * pressure) *
            (1.0 - self.params["N"] * pressure +
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
        r"""
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
            (1.0 - self.params["N"] * pressure +
             self.params["C"] * pressure) /
            (1.0 - self.params["N"] * pressure))

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

        # BET = Langmuir when N = 0.0. This is our default assumption.
        return {"n_m": saturation_loading, "C": langmuir_k,
                "N": langmuir_k * 0.01}
