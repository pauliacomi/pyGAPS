"""
Wilson-VST isotherm model
"""

import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class WVST(IsothermModel):
    """

    Wilson Vacancy Solution Theory isotherm model.

    Notes
    -----

    As a part of the Vacancy Solution Theory (VST) family of models, it is based on concept
    of a “vacancy” species, denoted v, and assumes that the system consists of a
    mixture of these vacancies and the adsorbate [#]_.

    The VST model is defined as follows:

        * A vacancy is an imaginary entity defined as a vacuum space
          which acts as the solvent in both the gas and adsorbed phases.
        * The properties of the adsorbed phase are defined as excess properties
          in relation to a dividing surface.
        * The entire system including the adsorbent are in thermal equilibrium
          however only the gas and adsorbed phases are in thermodynamic equilibrium.
        * The equilibrium of the system is maintained by the spreading pressure
          which arises from a potential field at the surface

    It is possible to derive expressions for the vacancy chemical potential in both
    the adsorbed phase and the gas phase, which when equated give the following equation
    of state for the adsorbed phase:

    .. math::

        \\pi = - \\frac{R_g T}{\\sigma_v} \\ln{y_v x_v}

    where :math:`y_v` is the activity coefficient and  :math:`x_v` is the mole fraction of
    the vacancy in the adsorbed phase.
    This can then be introduced into the Gibbs equation to give a general isotherm equation
    for the Vacancy Solution Theory where :math:`K_H` is the Henry’s constant and
    :math:`f(\\theta)` is a function that describes the non-ideality of the system based
    on activity coefficients:

    .. math::

        p = \\frac{n_{ads}}{K_H} \\frac{\\theta}{1-\\theta} f(\\theta)

    The general VST equation requires an expression for the activity coefficients.
    The Wilson equation can be used, which expresses the activity coefficient in terms
    of the mole fractions of the two species (adsorbate and vacancy) and two constants
    :math:`\\Lambda_{1v}` and :math:`\\Lambda_{1v}`. The equation becomes:

    .. math::

        p = \\bigg( \\frac{n_{ads}}{K_H} \\frac{\\theta}{1-\\theta} \\bigg)
            \\bigg( \\Lambda_{1v} \\frac{1-(1-\\Lambda_{v1})\\theta}{\\Lambda_{1v}+(1-\\Lambda_{1v})\\theta} \\bigg)
            \\exp{\\bigg( -\\frac{\\Lambda_{v1}(1-\\Lambda_{v1})\\theta}{1-(1-\\Lambda_{v1})\\theta}
            -\\frac{(1 - \\Lambda_{1v})\\theta}{\\Lambda_{1v} + (1-\\Lambda_{1v}\\theta)} \\bigg)}

    References
    ----------
    .. [#] Suwanayuen, S.; Danner, R. P., Gas-Adsorption Isotherm Equation Based On
       Vacancy Solution Theory. AIChE Journal 1980, 26, (1), 68-76.


    """
    #: Name of the model
    name = 'W-VST'
    calculates = 'pressure'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"n": numpy.nan, "K": numpy.nan,
                       "L1v": numpy.nan, "Lv1": numpy.nan}

    def loading(self, pressure):
        """
        Function that calculates loading.

        Careful!
        For the W-VST model, the loading has to
        be computed numerically.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """

        def fun(x):
            return self.pressure(x) - pressure

        opt_res = scipy.optimize.root(fun, 0, method='hybr')

        if not opt_res.success:
            raise CalculationError("""
            Root finding for value {0} failed.
            """.format(pressure))

        return opt_res.x

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.

        The W-VST model calculates the pressure directly.

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        cov = loading / self.params["n"]

        coef = self.params["L1v"] * (1 - (1 - self.params["Lv1"]) * cov) / \
            (self.params["L1v"] + (1 - self.params["L1v"]) * cov)

        expcoef = -((self.params["Lv1"] * (1 - self.params["Lv1"]) * cov) /
                    (1 - (1 - self.params["Lv1"]) * cov)) \
                  - (((1 - self.params["L1v"]) * cov) /
                     (self.params["L1v"] + (1 - self.params["L1v"]) * cov))

        res = (self.params["n"] / self.params["K"] * cov / (1 - cov)) * \
            coef * numpy.exp(expcoef)

        return res

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \\pi = \\int_{0}^{p_i} \\frac{n_i(p_i)}{p_i} dp_i

        The integral for the W-VST model cannot be solved analytically
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
        return NotImplementedError

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
        saturation_loading, langmuir_k = super(WVST, self).default_guess(
            data, loading_key, pressure_key)

        return {"n": saturation_loading, "K": langmuir_k,
                "L1v": 1, "Lv1": 1}
