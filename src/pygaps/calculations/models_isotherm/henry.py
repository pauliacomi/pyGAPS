"""
Henry isotherm model
"""

import numpy

from .model import IsothermModel


class Henry(IsothermModel):
    """
    Henry's law. Assumes a linear dependence of adsorbed amount with
    pressure.

    Usually, Henry's law is unrealistic because the adsorption sites
    will saturate at higher pressures.
    Only use if your data is linear.

    .. math::

        L(P) = K_H P

    """
    #: Name of the model
    name = 'Henry'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"K": numpy.nan}

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
        return self.params["K"] * pressure

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the Henry model, a direct relationship can be found
        by rearranging the function.

        .. math::

            \\P = L / P

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
        """
        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \\pi = \\int_{0}^{P_i} \\frac{n_i(P_i)}{P_i} dP_i

        The integral for the Henry model is solved analytically.

        .. math::

            \\pi = K_H P

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
        saturation_loading, langmuir_k = super(Henry, self).default_guess(
            data, loading_key, pressure_key)

        return {"K": saturation_loading * langmuir_k}
