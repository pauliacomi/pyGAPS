"""Dubinin-Astakov isotherm model."""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .base_model import IsothermBaseModel


class DR(IsothermBaseModel):
    r"""
    Dubinin-Astakov (DA) adsorption isotherm.

    .. math::

        n(p) = n_t \exp\Big[\Big(-\frac{RT\ln(p_0/p)}{\varepsilon}\Big)^{m}\Big]

    Notes
    -----


    References
    ----------
    .. [#] M. M. Dubinin, “Physical Adsorption of Gases and Vapors in Micropores,”
       in Progress in Surface and Membrane Science, vol. 9, Elsevier, 1975, pp. 1–70.

    """

    # Model parameters
    name = 'DA'
    calculates = 'loading'
    param_names = ["n_m", "e", "exp"]
    param_bounds = {
        "n_m": [0, numpy.inf],
        "e": [-numpy.inf, numpy.inf],
        "exp": [0, 3],
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
        return self.params["n_m"] * numpy.exp(
            (scipy.constants.r) **
        )

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

        Careful!
        For the DA model, the loading has to
        be computed numerically.

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
