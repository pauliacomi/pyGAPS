"""
This module contains objects to characterize the pure-component adsorption
isotherms from experimental or simulated data. These will be fed into the
IAST functions in pyiast.py.
"""
__author__ = 'Cory M. Simon'

import copy

import numpy
import scipy.optimize

from .isotherm import Isotherm

# ! version
_VERSION = "1.4"

# ! list of models implemented in pyIAST
_MODELS = ["Langmuir", "Quadratic", "BET", "Henry", "TemkinApprox",
           "DSLangmuir", "TSLangmuir"]

# ! dictionary of parameters involved in each model
_MODEL_PARAMS = {
    "Langmuir": {"M": numpy.nan, "K": numpy.nan},
    "Quadratic": {"M": numpy.nan, "Ka": numpy.nan, "Kb": numpy.nan},
    "BET": {"M": numpy.nan, "Ka": numpy.nan, "Kb": numpy.nan},
    "DSLangmuir": {"M1": numpy.nan, "K1": numpy.nan,
                   "M2": numpy.nan, "K2": numpy.nan},
    "TSLangmuir": {"M1": numpy.nan, "K1": numpy.nan,
                   "M2": numpy.nan, "K2": numpy.nan,
                   "M3": numpy.nan, "K3": numpy.nan},
    "TemkinApprox": {"M": numpy.nan, "K": numpy.nan, "theta": numpy.nan},
    "Henry": {"KH": numpy.nan}
}


class ModelIsotherm(Isotherm):
    """
    Class to characterize pure-component isotherm data with an analytical model.
    Data fitting is done during instantiation.

    Models supported are as follows. Here, :math:`L` is the gas uptake,
    :math:`P` is pressure (fugacity technically).

    * Langmuir isotherm model

    .. math::

        L(P) = M\\frac{KP}{1+KP},

    * Quadratic isotherm model

    .. math::

        L(P) = M \\frac{(K_a + 2 K_b P)P}{1+K_aP+K_bP^2}

    * Brunauer-Emmett-Teller (BET) adsorption isotherm

    .. math::

        L(P) = M\\frac{K_A P}{(1-K_B P)(1-K_B P+ K_A P)}

    * Dual-site Langmuir (DSLangmuir) adsorption isotherm

    .. math::

        L(P) = M_1\\frac{K_1 P}{1+K_1 P} +  M_2\\frac{K_2 P}{1+K_2 P}

    * Triple-site Langmuir (TSLangmuir) adsorption isotherm

    .. math::

        L(P) = M_1\\frac{K_1 P}{1+K_1 P} +  M_2\\frac{K_2 P}{1+K_2 P} + M_3\\frac{K_3 P}{1+K_3 P}

    * Asymptotic approximation to the Temkin Isotherm
    (see DOI: 10.1039/C3CP55039G)

    .. math::

        L(P) = M\\frac{KP}{1+KP} + M \\theta (\\frac{KP}{1+KP})^2 (\\frac{KP}{1+KP} -1)

    * Henry's law. Only use if your data is linear, and do not necessarily trust
      IAST results from Henry's law if the result required an extrapolation
      of your data; Henry's law is unrealistic because the adsorption sites
      will saturate at higher pressures.

    .. math::

        L(P) = K_H P

    """

    def __init__(self, data,
                 loading_key=None,
                 pressure_key=None,
                 model=None,
                 param_guess=None,
                 optimization_method="Nelder-Mead",
                 mode_adsorbent="mass",
                 mode_pressure="absolute",
                 unit_loading="mmol",
                 unit_pressure="bar",
                 **isotherm_parameters):
        """
        Instantiation. A `ModelIsotherm` class is instantiated by passing it the
        pure-component adsorption isotherm in the form of a Pandas DataFrame.
        The least squares data fitting is done here.

        :param data: DataFrame pure-component adsorption isotherm data
        :param loading_key: String key for loading column in data
        :param pressure_key: String key for pressure column in data
        :param param_guess: Dict starting guess for model parameters in the
            data fitting routine
        :param optimization_method: String method in SciPy minimization function
            to use in fitting model to data.
            See [here](http://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize).

        :return: self
        :rtype: ModelIsotherm
        """
        # Checks
        if model is None:
            raise Exception("Specify a model to fit to the pure-component"
                            " isotherm data. e.g. model=\"Langmuir\"")
        if model not in _MODELS:
            raise Exception("Model {0} not an option in pyIAST. See viable"
                            "models with pyiast._MODELS".format(model))

        # Run base class constructor
        Isotherm.__init__(self,
                          loading_key,
                          pressure_key,
                          mode_adsorbent,
                          mode_pressure,
                          unit_loading,
                          unit_pressure,
                          **isotherm_parameters)

        #: Name of analytical model to fit to pure-component isotherm data
        #: adsorption isotherm
        self.model = model

        # ! root mean square error in fit
        self.rmse = numpy.nan

        # ! Dictionary of parameters as a starting point for data fitting
        self.param_guess = get_default_guess_params(model, data, pressure_key,
                                                    loading_key)

        # Override defaults if user provides param_guess dictionary
        if param_guess is not None:
            for param, guess_val in param_guess.items():
                if param not in self.param_guess.keys():
                    raise Exception("%s is not a valid parameter"
                                    " in the %s model." % (param, model))
                self.param_guess[param] = guess_val

        # ! Dictionary of identified model parameters
        # initialize params as nan
        self.params = copy.deepcopy(_MODEL_PARAMS[model])

        # fit model to isotherm data
        self._fit(data, optimization_method)

    #: Construction from a parent class with the extra data needed
    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data,
                      model, param_guess=None,
                      optimization_method="Nelder-Mead"):
        return cls(isotherm_data,
                   loading_key=isotherm.loading_key,
                   pressure_key=isotherm.pressure_key,
                   model=model,
                   param_guess=param_guess,
                   optimization_method=optimization_method,
                   mode_adsorbent=isotherm.mode_adsorbent,
                   mode_pressure=isotherm.mode_pressure,
                   unit_loading=isotherm.unit_loading,
                   unit_pressure=isotherm.unit_pressure,
                   **isotherm.get_parameters())

    def loading(self, pressure):
        """
        Given stored model parameters, compute loading at pressure P.

        :param pressure: Float or Array pressure (in corresponding units as data
            in instantiation)
        :return: predicted loading at pressure P (in corresponding units as data
            in instantiation) using fitted model params in `self.params`.
        :rtype: Float or Array
        """
        if self.model == "Langmuir":
            return self.params["M"] * self.params["K"] * pressure / \
                (1.0 + self.params["K"] * pressure)

        if self.model == "Quadratic":
            return self.params["M"] * (self.params["Ka"] +
                                       2.0 * self.params["Kb"] * pressure) * pressure / (
                1.0 + self.params["Ka"] * pressure +
                self.params["Kb"] * pressure ** 2)

        if self.model == "BET":
            return self.params["M"] * self.params["Ka"] * pressure / (
                (1.0 - self.params["Kb"] * pressure) *
                (1.0 - self.params["Kb"] * pressure +
                 self.params["Ka"] * pressure))

        if self.model == "DSLangmuir":
            # K_i P
            k1p = self.params["K1"] * pressure
            k2p = self.params["K2"] * pressure
            return self.params["M1"] * k1p / (1.0 + k1p) + \
                self.params["M2"] * k2p / (1.0 + k2p)

        if self.model == "TSLangmuir":
            # K_i P
            k1p = self.params["K1"] * pressure
            k2p = self.params["K2"] * pressure
            k3p = self.params["K3"] * pressure
            return self.params["M1"] * k1p / (1.0 + k1p) + \
                self.params["M2"] * k2p / (1.0 + k2p) + \
                self.params["M3"] * k3p / (1.0 + k3p)

        if self.model == "Henry":
            return self.params["KH"] * pressure

        if self.model == "TemkinApprox":
            langmuir_fractional_loading = self.params["K"] * pressure / \
                (1.0 + self.params["K"] * pressure)
            return self.params["M"] * (langmuir_fractional_loading +
                                       self.params["theta"] * langmuir_fractional_loading ** 2 *
                                       langmuir_fractional_loading)

    def _fit(self, data, optimization_method):
        """
        Fit model to data using nonlinear optimization with least squares loss
            function. Assigns params to self.

        :param K_guess: float guess Langmuir constant (units: 1/pressure)
        :param M_guess: float guess saturation loading (units: loading)
        """
        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params.keys()]
        # guess
        guess = numpy.array([self.param_guess[param] for param in param_names])

        def residual_sum_of_squares(params_):
            """
            Residual Sum of Squares between model and data in data
            :param params_: Array of parameters
            """
            # change params to those in x
            for i in range(len(param_names)):
                self.params[param_names[i]] = params_[i]

            return numpy.sum((data[self.loading_key].values -
                              self.loading(data[self.pressure_key].values)) ** 2)

        # minimize RSS
        opt_res = scipy.optimize.minimize(residual_sum_of_squares, guess,
                                          method=optimization_method)
        if not opt_res.success:
            print(opt_res.message)
            print("\n\tDefault starting guess for parameters:", self.param_guess)
            raise Exception("""Minimization of RSS for %s isotherm fitting
            failed. Try a different starting point in the nonlinear optimization
            by passing a dictionary of parameter guesses, param_guess, to the
            constructor""" % self.model)

        # assign params
        for index, _ in enumerate(param_names):
            self.params[param_names[index]] = opt_res.x[index]

        self.rmse = numpy.sqrt(opt_res.fun / data.shape[0])

    def spreading_pressure(self, pressure):
        """
        Calculate reduced spreading pressure at a bulk gas pressure P.

        The reduced spreading pressure is an integral involving the isotherm
        :math:`L(P)`:

        .. math::

            \\Pi(p) = \\int_0^p \\frac{L(\\hat{p})}{ \\hat{p}} d\\hat{p},

        which is computed analytically, as a function of the model isotherm
        parameters.

        :param pressure: float pressure (in corresponding units as data in
            instantiation)
        :return: spreading pressure, :math:`\\Pi`
        :rtype: Float
        """
        if self.model == "Langmuir":
            return self.params["M"] * numpy.log(1.0 + self.params["K"] * pressure)

        if self.model == "Quadratic":
            return self.params["M"] * numpy.log(1.0 + self.params["Ka"] * pressure +
                                                self.params["Kb"] * pressure ** 2)

        if self.model == "BET":
            return self.params["M"] * numpy.log(
                (1.0 - self.params["Kb"] * pressure +
                 self.params["Ka"] * pressure) /
                (1.0 - self.params["Kb"] * pressure))

        if self.model == "DSLangmuir":
            return self.params["M1"] * numpy.log(
                1.0 + self.params["K1"] * pressure) +\
                self.params["M2"] * numpy.log(
                1.0 + self.params["K2"] * pressure)

        if self.model == "TSLangmuir":
            return self.params["M1"] * numpy.log(
                1.0 + self.params["K1"] * pressure) +\
                self.params["M2"] * numpy.log(
                1.0 + self.params["K2"] * pressure) +\
                self.params["M3"] * numpy.log(
                1.0 + self.params["K3"] * pressure)

        if self.model == "Henry":
            return self.params["KH"] * pressure

        if self.model == "TemkinApprox":
            one_plus_kp = 1.0 + self.params["K"] * pressure
            return self.params["M"] * (numpy.log(one_plus_kp) +
                                       self.params["theta"] * (2.0 * self.params["K"] * pressure + 1.0) /
                                       (2.0 * one_plus_kp ** 2))

    def print_info(self):
        '''
        Prints a short summary of all the isotherm parameters
        '''

        print("%s identified model parameters:" % self.model)
        for param, val in self.params.items():
            print("\t%s = %f" % (param, val))
        print("RMSE = ", self.rmse)


def get_default_guess_params(model, data, pressure_key, loading_key):
    """
    Get dictionary of default parameters for starting guesses in data fitting
    routine.

    The philosophy behind the default starting guess is that (1) the saturation
    loading is close to the highest loading observed in the data, and (2) the
    default assumption is a Langmuir isotherm.

    Reminder: pass your own guess via `param_guess` in instantiation if these
    default guesses do not lead to a converged set of parameters.

    :param model: String name of analytical model
    :param data: DataFrame adsorption isotherm data
    :param pressure_key: String key for pressure column in data
    :param loading_key: String key for loading column in data
    """
    # guess saturation loading to 10% more than highest loading
    saturation_loading = 1.1 * data[loading_key].max()
    # guess Langmuir K using the guess for saturation loading and lowest
    #   pressure point (but not zero)
    df_nonzero = data[data[loading_key] != 0.0]
    idx_min = df_nonzero[loading_key].argmin()
    langmuir_k = df_nonzero[loading_key].loc[idx_min] / \
        df_nonzero[pressure_key].loc[idx_min] / (
        saturation_loading - df_nonzero[pressure_key].loc[idx_min])

    if model == "Langmuir":
        return {"M": saturation_loading, "K": langmuir_k}

    if model == "Quadratic":
        # Quadratic = Langmuir when Kb = Ka^2. This is our default assumption.
        # Also, M is half of the saturation loading in the Quadratic model.
        return {"M": saturation_loading / 2.0, "Ka": langmuir_k,
                "Kb": langmuir_k ** 2.0}

    if model == "BET":
        # BET = Langmuir when Kb = 0.0. This is our default assumption.
        return {"M": saturation_loading, "Ka": langmuir_k,
                "Kb": langmuir_k * 0.01}

    if model == "DSLangmuir":
        return {"M1": 0.5 * saturation_loading, "K1": 0.4 * langmuir_k,
                "M2": 0.5 * saturation_loading, "K2": 0.6 * langmuir_k}

    if model == "TSLangmuir":
        return {"M1": 0.5 * saturation_loading, "K1": 0.4 * langmuir_k,
                "M2": 0.5 * saturation_loading, "K2": 0.6 * langmuir_k,
                "M3": 0.5 * saturation_loading, "K3": 0.6 * langmuir_k}

    if model == "Henry":
        return {"KH": saturation_loading * langmuir_k}

    if model == "TemkinApprox":
        # equivalent to Langmuir model if theta = 0.0
        return {"M": saturation_loading, "K": langmuir_k, "theta": 0.0}