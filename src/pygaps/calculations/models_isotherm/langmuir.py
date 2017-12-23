"""
Langmuir isotherm model
"""

import numpy

from .model import IsothermModel


class Langmuir(IsothermModel):
    """
    Langmuir isotherm model

    .. math::

        L(P) = M\\frac{KP}{1+KP}

    Notes
    -----

    The Langmuir theory [#]_, proposed at the start of the 20th century, states that
    adsorption happens on active sites on a surface in a single layer. It is
    derived based on several assumptions.

        * All sites are equivalent and have the same chance of being occupied
        * Each adsorbate molecule can occupy one adsorption site
        * There are no interactions between adsorbed molecules
        * The rates of adsorption and desorption are proportional to the number
          of sites currently free and currently occupied, respectively
        * Adsorption is complete when all sites are filled.

    Using the following assumptions we can define rates for both the adsorption and
    desorption. The adsorption rate will be proportional to the number of sites available
    on the surface, as well as the number of molecules in the gas, which is represented by
    the pressure. The desorption rate, on the other hand, will be proportional to the
    number of occupied sites and the energy of adsorption.
    It is also useful to define :math:`\\theta = \\frac{n_a}{M}` as the surface coverage,
    the number of sites occupied divided by the total sites. Mathematically:

    .. math::

        v_a = k_a p (1 - \\theta)

        v_d = k_d \\theta \\exp{-\\frac{E}{RT}}

    Here, :math:`M` is the moles adsorbed at the completion of the monolayer, and therefore
    the maximum possible loading. At equilibrium, the rate of adsorption and the rate of
    desorption are equal, therefore the two equations can be combined.

    .. math::

        k_a p (1 - \\theta) = k_d \\theta \\exp{-\\frac{E}{RT}}

    Rearranging to get an expression for the loading, the Langmuir equation becomes:

    .. math::

        L(P) = M\\frac{KP}{1+KP}

    The Langmuir constant is the product of the individual desorption and adsorption constants
    :math:`k_a` and :math:`k_d` and exponentially related to the energy of adsorption
    :math:`\\exp{-\\frac{E}{RT}}`.

    References
    ----------
    .. [#] I. Langmuir, J. American Chemical Society 38, 2219(1916); 40, 1368(1918)

    """

    #: Name of the class as static
    name = 'Langmuir'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"M": numpy.nan, "K": numpy.nan}

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
        return self.params["M"] * self.params["K"] * pressure / \
            (1.0 + self.params["K"] * pressure)

    def pressure(self, loading):
        """
        Function that calculates pressure

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return loading / \
            (self.params["K"] * (self.params["M"] - loading))

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return self.params["M"] * \
            numpy.log(1.0 + self.params["K"] * pressure)

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
        saturation_loading, langmuir_k = super(Langmuir, self).default_guess(
            data, loading_key, pressure_key)

        return {"M": saturation_loading, "K": langmuir_k}
