"""Wilson-VST isotherm model."""

import logging

logger = logging.getLogger('pygaps')

import numpy

from .. import scipy
from ..utilities.exceptions import CalculationError
from .base_model import IsothermBaseModel


class WVST(IsothermBaseModel):
    r"""
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
        * The entire system including the material are in thermal equilibrium
          however only the gas and adsorbed phases are in thermodynamic equilibrium.
        * The equilibrium of the system is maintained by the spreading pressure
          which arises from a potential field at the surface

    It is possible to derive expressions for the vacancy chemical potential in both
    the adsorbed phase and the gas phase, which when equated give the following equation
    of state for the adsorbed phase:

    .. math::

        \pi = - \frac{R_g T}{\sigma_v} \ln{y_v x_v}

    where :math:`y_v` is the activity coefficient and  :math:`x_v` is the mole fraction of
    the vacancy in the adsorbed phase.
    This can then be introduced into the Gibbs equation to give a general isotherm equation
    for the Vacancy Solution Theory where :math:`K_H` is the Henry’s constant and
    :math:`f(\theta)` is a function that describes the non-ideality of the system based
    on activity coefficients:

    .. math::

        p = \frac{n_{ads}}{K_H} \frac{\theta}{1-\theta} f(\theta)

    The general VST equation requires an expression for the activity coefficients.
    The Wilson equation can be used, which expresses the activity coefficient in terms
    of the mole fractions of the two species (adsorbate and vacancy) and two constants
    :math:`\Lambda_{1v}` and :math:`\Lambda_{1v}`. The equation becomes:

    .. math::

        p = \bigg( \frac{n_{ads}}{K_H} \frac{\theta}{1-\theta} \bigg)
            \bigg( \Lambda_{1v} \frac{1-(1-\Lambda_{v1})\theta}{\Lambda_{1v}+(1-\Lambda_{1v})\theta} \bigg)
            \exp{\bigg( -\frac{\Lambda_{v1}(1-\Lambda_{v1})\theta}{1-(1-\Lambda_{v1})\theta}
            -\frac{(1 - \Lambda_{1v})\theta}{\Lambda_{1v} + (1-\Lambda_{1v}\theta)} \bigg)}

    References
    ----------
    .. [#] Suwanayuen, S.; Danner, R. P., Gas-Adsorption Isotherm Equation Based On
       Vacancy Solution Theory. AIChE Journal 1980, 26, (1), 68-76.

    """

    # Model parameters
    name = 'WVST'
    calculates = 'pressure'
    param_names = ["n_m", "K", "L1v", "Lv1"]
    param_bounds = {
        "n_m": [0, numpy.inf],
        "K": [0, numpy.inf],
        "L1v": [-numpy.inf, numpy.inf],
        "Lv1": [-numpy.inf, numpy.inf],
    }

    def loading(self, pressure):
        """
        Calculate loading at specified pressure.

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
            raise CalculationError(
                f"Root finding for value {pressure} failed."
            )

        return opt_res.x

    def pressure(self, loading):
        """
        Calculate pressure at specified loading.

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
        cov = loading / self.params["n_m"]

        coef = self.params["L1v"] * (1 - (1 - self.params["Lv1"]) * cov) / \
            (self.params["L1v"] + (1 - self.params["L1v"]) * cov)

        expcoef = -((self.params["Lv1"] * (1 - self.params["Lv1"]) * cov) /
                    (1 - (1 - self.params["Lv1"]) * cov)) \
                  - ((1 - self.params["L1v"]) * cov /
                     (self.params["L1v"] + (1 - self.params["L1v"]) * cov))

        res = (self.params["n_m"] / self.params["K"] * cov / (1 - cov)) * \
            coef * numpy.exp(expcoef)

        return res

    def spreading_pressure(self, pressure):
        r"""
        Calculate spreading pressure at specified gas pressure.

        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \pi = \int_{0}^{p_i} \frac{n_i(p_i)}{p_i} dp_i

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

    def initial_guess(self, pressure, loading):
        """
        Return initial guess for fitting.

        Parameters
        ----------
        pressure : ndarray
            Pressure data.
        loading : ndarray
            Loading data.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        """
        saturation_loading, langmuir_k = super().initial_guess(
            pressure, loading
        )

        guess = {
            "n_m": saturation_loading,
            "K": langmuir_k,
            "L1v": 1,
            "Lv1": 1
        }

        for param in guess:
            if guess[param] < self.param_bounds[param][0]:
                guess[param] = self.param_bounds[param][0]
            if guess[param] > self.param_bounds[param][1]:
                guess[param] = self.param_bounds[param][1]

        return guess

    def fit(
        self,
        pressure,
        loading,
        param_guess,
        optimization_params=None,
        verbose=False
    ):
        """
        Fit model to data using nonlinear optimization with least squares loss function.

        Resulting parameters are assigned to self.

        Parameters
        ----------
        pressure : ndarray
            The pressures of each point.
        loading : ndarray
            The loading for each point.
        optimization_params : dict
            Custom parameters to pass to SciPy.optimize.least_squares.
        verbose : bool, optional
            Prints out extra information about steps taken.
        """
        if verbose:
            logger.info(f"Attempting to model using {self.name}")

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params]
        guess = numpy.array([param_guess[param] for param in param_names])
        bounds = [[self.param_bounds[param][0] for param in param_names],
                  [self.param_bounds[param][1] for param in param_names]]

        def fit_func(x, p, L):
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = x[i]
            return self.pressure(L) - p

        kwargs = dict(
            bounds=bounds,  # supply the bounds of the parameters
        )
        if optimization_params:
            kwargs.update(optimization_params)

        # minimize RSS
        opt_res = scipy.optimize.least_squares(
            fit_func,
            guess,  # provide the fit function and initial guess
            args=(pressure,
                  loading),  # supply the extra arguments to the fit function
            **kwargs
        )
        if not opt_res.success:
            raise CalculationError(
                f"\nFitting routine with model {self.name} failed with error:"
                f"\n\t{opt_res.message}"
                f"\nTry a different starting point in the nonlinear optimization"
                f"\nby passing a dictionary of parameter guesses, param_guess, to the constructor."
                f"\nDefault starting guess for parameters:"
                f"\n{param_guess}\n"
            )

        # assign params
        for index, _ in enumerate(param_names):
            self.params[param_names[index]] = opt_res.x[index]

        self.rmse = numpy.sqrt(numpy.sum((opt_res.fun)**2) / len(loading))

        if verbose:
            logger.info(f"Model {self.name} success, RMSE is {self.rmse:.3f}")
