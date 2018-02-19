"""
Jensen-Seaton isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class JensenSeaton(IsothermModel):
    """
    Jensen-Seaton isotherm model

    .. math::

        L(P) = K_H P (1 + \\frac{K_H P}{(a (1+(b p))))^c})^{(-1/c)}

    Notes
    -----

    When modelling adsorption in micropores, a requirement was highlighted by
    Jensen and Seaton in 1996 [#]_, that at sufficiently high pressures the adsorption
    isotherm should not reach a horizontal plateau corresponding to saturation but
    that this asymptote should continue to rise due to the compression of the adsorbate
    in the pores. They came up with a semi-empirical equation to describe this phenomenon
    based on a function that interpolates between two asymptotes: the Henry’s law asymptote
    at low pressure and an asymptote reflecting the compressibility of the adsorbate at
    high pressure.

    Here :math:`K_H` is the Henry constant, :math:`b` is the compressibility of the
    adsorbed phase and :math:`c` an empirical constant.

    The equation can be used to model both absolute and excess adsorption as the pore
    volume can be incorporated into the definition of :math:`b`, although this can lead
    to negative adsorption slopes for the compressibility asymptote.
    This equation has been found to provide a better fit for experimental data
    from microporous solids than the Langmuir or Toth equation, in particular for
    adsorbent/adsorbate systems with high Henry’s constants where the amount adsorbed
    increases rapidly at relatively low pressures and then slows down dramatically.

    References
    ----------
    .. [#] Jensen, C. R. C.; Seaton, N. A., An Isotherm Equation for Adsorption to High
       Pressures in Microporous Adsorbents. Langmuir 1996, 12, (Copyright (C) 2012
       American Chemical Society (ACS). All Rights Reserved.), 2866-2867.

    """
    #: Name of the model
    name = 'Jensen-Seaton'
    calculates = 'loading'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"KH": numpy.nan, 'a': numpy.nan,
                       'b': numpy.nan, 'c': numpy.nan}

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
        return self.params["KH"] * pressure * \
            (1 + (self.params["KH"] * pressure /
                  (self.params["a"] * (1 + self.params["b"] * pressure))
                  )**self.params['c'])**(- 1 / self.params['c'])

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.
        For the Jensen-Seaton model, the pressure will
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

        The integral for the Jensen-Seaton model cannot be solved analytically
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
        return scipy.integrate.quad(lambda x: self.loading(x) / x, 0, pressure)[0]

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
        saturation_loading, langmuir_k = super(JensenSeaton, self).default_guess(
            data, loading_key, pressure_key)

        return {"KH": saturation_loading * langmuir_k,
                "a": 1,
                "b": 1,
                "c": 1, }
