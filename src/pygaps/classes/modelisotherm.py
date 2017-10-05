"""
This module contains objects to model pure-component adsorption
isotherms from experimental or simulated data.
"""


import copy

import matplotlib.pyplot as plt
import numpy
import pandas
import scipy.optimize

from ..graphing.isothermgraphs import plot_iso
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.unit_converter import convert_loading
from ..utilities.unit_converter import convert_pressure
from .adsorbate import Adsorbate
from .isotherm import Isotherm
from .sample import Sample

# ! list of models implemented
# ! with parameters involved in each model
_MODELS = {
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

    A `ModelIsotherm` class is instantiated by passing it the
    pure-component adsorption isotherm in the form of a Pandas DataFrame.

    Parameters
    ----------
    isotherm_data : DataFrame
        pure-component adsorption isotherm data
    loading_key : str
        column of the pandas DataFrame where the loading is stored
    pressure_key : str
        column of the pandas DataFrame where the pressure is stored
    model : str
        the model to be used to describe the isotherm
    param_guess : dict
        starting guess for model parameters in the data fitting routine
    optimization_method : str
        method in SciPy minimization function to use in fitting model to data.
        See `here
        <http://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
    branch : ['ads', 'des'], optional
        The branch on which the model isotherm is based on. It is assumed to be the
        adsorption branch, as it is the most commonly modelled part, although may
        set to desorption as well.
    verbose : bool
        Prints out extra information about steps taken.
    basis_adsorbent : str, optional
        whether the adsorption is read in terms of either 'per volume'
        or 'per mass'
    mode_pressure : str, optional
        the pressure mode, either absolute pressures or relative in
        the form of p/p0
    unit_loading : str, optional
        unit of loading
    unit_pressure : str, optional
        unit of pressure
    isotherm_parameters:
        dictionary of the form::

            isotherm_params = {
                'sample_name' : 'Zeolite-1',
                'sample_batch' : '1234',
                'adsorbate' : 'N2',
                't_exp' : 200,
                'user' : 'John Doe',
                'properties' : {
                    'doi' : '10.0000/'
                    'x' : 'y'
                }
            }

    Notes
    -----

    Models supported are as follows. Here, :math:`L` is the adsorbate uptake,
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

##########################################################
#   Instantiation and classmethods

    def __init__(self, data,
                 loading_key=None,
                 pressure_key=None,
                 model=None,
                 param_guess=None,
                 optimization_method="Nelder-Mead",
                 branch='ads',
                 verbose=False,
                 basis_adsorbent='mass',
                 mode_pressure='absolute',
                 unit_loading='mmol',
                 unit_pressure='bar',
                 **isotherm_parameters):
        """
        Instantiation is done by passing the data to be fitted, model to be
        used and fitting method as well as the parameters required by parent
        class
        """
        # Checks
        if model is None:
            raise ParameterError("Specify a model to fit to the pure-component"
                                 " isotherm data. e.g. model=\"Langmuir\"")
        if model not in _MODELS:
            raise ParameterError("Model {0} not an option in pyIAST. Viable"
                                 "models are {1}".format(model, _MODELS))

        # We change it to a model
        isotherm_parameters['is_real'] = False

        # Run base class constructor
        Isotherm.__init__(self,
                          basis_adsorbent,
                          mode_pressure,
                          unit_loading,
                          unit_pressure,
                          **isotherm_parameters)

        # Save column names
        #: Name of column in the dataframe that contains adsorbed amount
        self.loading_key = loading_key

        #: Name of column in the dataframe that contains pressure
        self.pressure_key = pressure_key

        #: The pressure range on which the model was built
        self.pressure_range = [min(data[pressure_key]),
                               max(data[pressure_key])]

        #: Branch the isotherm model is based on
        self.branch = branch

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
                    raise ParameterError("%s is not a valid parameter"
                                         " in the %s model." % (param, model))
                self.param_guess[param] = guess_val

        # ! Dictionary of identified model parameters
        # initialize params as nan
        self.params = copy.deepcopy(_MODELS[model])

        # fit model to isotherm data
        self._fit(data[loading_key].values,
                  data[pressure_key].values,
                  optimization_method,
                  verbose)

    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data,
                      loading_key, pressure_key,
                      model, param_guess=None,
                      optimization_method="Nelder-Mead"):
        """
        Constructs a ModelIsotherm using a parent isotherm as the template for
        all the parameters.

        Parameters
        ----------
        isotherm : Isotherm
            an instance of the Isotherm parent class
        isotherm_data : DataFrame
            pure-component adsorption isotherm data
        loading_key : str
            column of the pandas DataFrame where the loading is stored
        pressure_key : str
            column of the pandas DataFrame where the pressure is stored
        model : str
            the model to be used to describe the isotherm
        param_guess : dict
            starting guess for model parameters in the data fitting routine
        optimization_method : str
            method in SciPy minimization function to use in fitting model to data.
        """
        return cls(isotherm_data,
                   loading_key=loading_key,
                   pressure_key=pressure_key,
                   model=model,
                   param_guess=param_guess,
                   optimization_method=optimization_method,
                   basis_adsorbent=isotherm.basis_adsorbent,
                   mode_pressure=isotherm.mode_pressure,
                   unit_loading=isotherm.unit_loading,
                   unit_pressure=isotherm.unit_pressure,
                   **isotherm.to_dict())

    @classmethod
    def from_pointisotherm(cls,
                           isotherm,
                           model=None,
                           guess_model=False,
                           branch='ads',
                           param_guess=None,
                           optimization_method="Nelder-Mead",
                           verbose=False):
        """
        Constructs a ModelIsotherm using a the data from a PointIsotherm
        and all its parameters.

        Parameters
        ----------
        isotherm : PointIsotherm
            An instance of the PointIsotherm parent class to model.
        model : str
            The model to be used to describe the isotherm
        guess_model : bool
            Set to true if you want to attemt to guess which model best
            fits the isotherm data. This will mean a calculation of all
            models available, so it will take a longer time.
        branch : {None, 'ads', 'des'}, optional
            Branch of isotherm to model. Defaults to adsorption branch.
        param_guess : dict, optional
            Starting guess for model parameters in the data fitting routine.
        optimization_method : str, optional
            Method in SciPy minimization function to use in fitting model to data.
        verbose : bool
            Prints out extra information about steps taken.
        """
        if guess_model:
            return ModelIsotherm.guess(isotherm.data(branch=branch),
                                       loading_key=isotherm.loading_key,
                                       pressure_key=isotherm.pressure_key,
                                       optimization_method=optimization_method,
                                       branch=branch,
                                       verbose=verbose,
                                       basis_adsorbent=isotherm.basis_adsorbent,
                                       mode_pressure=isotherm.mode_pressure,
                                       unit_loading=isotherm.unit_loading,
                                       unit_pressure=isotherm.unit_pressure,
                                       **isotherm.to_dict())

        return cls(isotherm.data(branch=branch),
                   loading_key=isotherm.loading_key,
                   pressure_key=isotherm.pressure_key,
                   model=model,
                   param_guess=param_guess,
                   optimization_method=optimization_method,
                   branch=branch,
                   verbose=verbose,
                   basis_adsorbent=isotherm.basis_adsorbent,
                   mode_pressure=isotherm.mode_pressure,
                   unit_loading=isotherm.unit_loading,
                   unit_pressure=isotherm.unit_pressure,
                   **isotherm.to_dict())

    @classmethod
    def guess(cls, data,
              loading_key=None,
              pressure_key=None,
              optimization_method="Nelder-Mead",
              branch='ads',
              verbose=False,
              basis_adsorbent="mass",
              mode_pressure="absolute",
              unit_loading="mmol",
              unit_pressure="bar",
              **isotherm_parameters):
        """
        Attempts to model the data using all available models, then returns
        the one with the best rms fit.

        May take a long time depending on the number of datapoints.

        Parameters
        ----------
        isotherm_data : DataFrame
            Pure-component adsorption isotherm data.
        loading_key : str
            Column of the pandas DataFrame where the loading is stored.
        pressure_key : str
            Column of the pandas DataFrame where the pressure is stored.
        optimization_method : str
            Method in SciPy minimization function to use in fitting model to data.
        branch : ['ads', 'des'], optional
            The branch on which the model isotherm is based on. It is assumed to be the
            adsorption branch, as it is the most commonly modelled part, although may
            set to desorption as well.
        verbose : bool, optional
            Prints out extra information about steps taken.
        basis_adsorbent : {'relative', 'optional'}
            Whether the adsorption is read in terms of either 'per volume'
            or 'per mass'.
        mode_pressure : {'relative', 'optional'}
            The pressure mode, either absolute pressures or relative in
            the form of p/p0.
        unit_loading : str, optional
            Unit of loading.
        unit_pressure : str, optional
            Unit of pressure.
        isotherm_parameters:
            Dictionary with the paramters.
        """
        attempts = []
        for model in _MODELS:
            try:
                isotherm = ModelIsotherm(data,
                                         loading_key=loading_key,
                                         pressure_key=pressure_key,
                                         model=model,
                                         param_guess=None,
                                         optimization_method=optimization_method,
                                         branch=branch,
                                         verbose=verbose,
                                         basis_adsorbent=basis_adsorbent,
                                         mode_pressure=mode_pressure,
                                         unit_loading=unit_loading,
                                         unit_pressure=unit_pressure,
                                         **isotherm_parameters)

                attempts.append(isotherm)

            except CalculationError:
                if verbose:
                    print("Modelling using {0} failed".format(model))

        if not attempts:
            raise CalculationError(
                "No model could be reliably fit on the isotherm")
        else:
            errors = [x.rmse for x in attempts]
            best_fit = attempts[errors.index(min(errors))]

            if verbose:
                print("Best model fit is {0}".format(best_fit.model))

            return best_fit

        ##########################################################
        #   Overloaded and private functions

    def _fit(self, loading, pressure, optimization_method, verbose=False):
        """
        Fit model to data using nonlinear optimization with least squares loss
        function. Assigns parameters to self

        Parameters
        ----------
        loading : ndarray
            the loading for each point
        pressure : ndarray
            the pressures of each point
        optimization_method : str
            method in SciPy minimization function to use in fitting model to data.
        verbose : bool, optional
            Prints out extra information about steps taken.
        """
        if verbose:
            print("Attempting to model using {}".format(self.model))

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.params.keys()]
        # guess
        guess = numpy.array([self.param_guess[param] for param in param_names])

        def residual_sum_of_squares(params_):
            """
            Residual Sum of Squares between model and data in data
            """
            # change params to those in x
            for i, _ in enumerate(param_names):
                self.params[param_names[i]] = params_[i]

            return numpy.sum((loading - self.loading_at(pressure)) ** 2)

        # minimize RSS
        opt_res = scipy.optimize.minimize(residual_sum_of_squares, guess,
                                          method=optimization_method)
        if not opt_res.success:
            raise CalculationError("""
            Minimization of RSS for {0} isotherm fitting failed with error {1}.
            Try a different starting point in the nonlinear optimization
            by passing a dictionary of parameter guesses, param_guess, to the
            constructor.
            "\n\tDefault starting guess for parameters: {2}"
            """.format(self.model, opt_res.message, self.param_guess))

        # assign params
        for index, _ in enumerate(param_names):
            self.params[param_names[index]] = opt_res.x[index]

        self.rmse = numpy.sqrt(opt_res.fun / len(pressure))

        if verbose:
            print("Model {0} success, rmse is {1}".format(
                self.model, self.rmse))

##########################################################
#   Methods

    def has_branch(self, branch):
        """
        Returns if the isotherm has an specific branch

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the data to check for.

        Returns
        -------
        bool
            Whether the data exists or not
        """

        if self.branch == branch:
            return True
        else:
            return False

    def pressure(self, points=20, unit=None, branch=None, mode=None,
                 min_range=None, max_range=None, indexed=False):
        """
        Returns a numpy.linspace generated array with
        a fixed number of equidistant points within the
        pressure range the model was created.

        Parameters
        ----------
        points : int
            The number of points to get.
        unit : str, optional
            Unit in which the pressure should be returned. If None
            it defaults to which pressure unit the isotherm is currently in
        branch : {None, 'ads', 'des'}
            The branch of the pressure to return. If None, returns the branch
            the isotherm is modelled on
        mode : {None, 'absolute', 'relative'}
            The mode in which to return the pressure, if possible. If None,
            returns mode the isotherm is currently in.
        min_range : float, optional
            The lower limit for the pressure to select.
        max_range : float, optional
            The higher limit for the pressure to select.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series with the columns requested instead of an array.


        Returns
        -------
        numpy.array
            Pressure points in the model pressure range.
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")

        # Generate pressure points
        ret = numpy.linspace(self.pressure_range[0],
                             self.pressure_range[1],
                             points)

        # Convert if needed
        if mode is not None and mode != self.mode_pressure:
            ret = Adsorbate.from_list(self.adsorbate).convert_mode(
                mode,
                ret,
                self.t_exp,
                self.unit_pressure)
        if unit is not None and unit != self.unit_pressure:
            ret = convert_pressure(ret, self.unit_pressure, unit)

        # Select required points
        if max_range is not None or min_range is not None:
            if min_range is None:
                min_range = min(ret)
            if max_range is None:
                max_range = max(ret)

            ret = ret.loc[lambda x: x >=
                          min_range].loc[lambda x: x <= max_range]

        if indexed:
            return pandas.Series(ret)
        else:
            return ret

    def loading(self, points=20, unit=None, branch=None, basis=None,
                min_range=None, max_range=None, indexed=False):
        """
        Returns the loading calculated at equidistant pressure
        points within the pressure range the model was created.

        Parameters
        ----------
        points : int
            The number of points to get.
        unit : str, optional
            Unit in which the loading should be returned. If None
            it defaults to which loading unit the isotherm is currently in
        branch : {None, 'ads', 'des'}
            The branch of the loading to return. If None, returns entire
            dataset
        basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If None,
            returns on the basis the isotherm is currently in.
        min_range : float, optional
            The lower limit for the loading to select.
        max_range : float, optional
            The higher limit for the loading to select.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series with the columns requested instead of an array.


        Returns
        -------
        numpy.array
            Loading calculated at points the model pressure range.
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")

        ret = self.loading_at(self.pressure(points))

        # Convert if needed
        if basis is not None and basis != self.basis_adsorbent:
            ret = Sample.from_list(self.sample_name, self.sample_batch).convert_basis(
                basis,
                ret)
        if unit is not None and unit != self.unit_loading:
            ret = convert_loading(ret, self.unit_loading, unit)

        # Select required points
        if max_range is not None or min_range is not None:
            if min_range is None:
                min_range = min(ret)
            if max_range is None:
                max_range = max(ret)
            ret = ret.loc[lambda x: x >=
                          min_range].loc[lambda x: x <= max_range]

        if indexed:
            return pandas.Series(ret)
        else:
            return ret

    def loading_at(self, pressure,
                   pressure_unit=None,
                   pressure_mode=None,
                   loading_unit=None,
                   adsorbent_basis=None):
        """
        Given stored model parameters, compute loading at pressure P.

        Parameters
        ----------
        pressure : float or array
            Pressure at which to compute loading.
        loading_unit : str
            Unit the loading is returned in. If None, it defaults to
            internal model units.
        pressure_unit : str
            Unit the pressure is specified in. If None, it defaults to
            internal model units.
        adsorbent_basis : str
            The basis the loading should be returned in. If None, it defaults to
            internal model basis.
        pressure_mode : str
            The mode the pressure is passed in. If None, it defaults to
            internal model mode.

        Returns
        -------
        float or array
            predicted loading at pressure P using fitted model
            parameters
        """
        # Ensure pressure is in correct units and mode for the internal model
        if pressure_unit is not None and pressure_unit != self.unit_pressure:
            pressure = convert_pressure(
                pressure, pressure_unit, self.unit_pressure)
        if pressure_mode is not None and pressure_mode != self.mode_pressure:
            pressure = Adsorbate.from_list(self.adsorbate).convert_mode(
                pressure_mode, pressure, self.t_exp, pressure_unit)

        # Convert to numpy array just in case
        pressure = numpy.array(pressure)

        # Calculate loading using internal model
        if self.model == "Langmuir":
            loading = self.params["M"] * self.params["K"] * pressure / \
                (1.0 + self.params["K"] * pressure)

        elif self.model == "Quadratic":
            loading = self.params["M"] * (self.params["Ka"] +
                                          2.0 * self.params["Kb"] * pressure) * pressure / (
                1.0 + self.params["Ka"] * pressure +
                self.params["Kb"] * pressure ** 2)

        if self.model == "BET":
            loading = self.params["M"] * self.params["Ka"] * pressure / (
                (1.0 - self.params["Kb"] * pressure) *
                (1.0 - self.params["Kb"] * pressure +
                 self.params["Ka"] * pressure))

        elif self.model == "DSLangmuir":
            # K_i P
            k1p = self.params["K1"] * pressure
            k2p = self.params["K2"] * pressure
            loading = self.params["M1"] * k1p / (1.0 + k1p) + \
                self.params["M2"] * k2p / (1.0 + k2p)

        elif self.model == "TSLangmuir":
            # K_i P
            k1p = self.params["K1"] * pressure
            k2p = self.params["K2"] * pressure
            k3p = self.params["K3"] * pressure
            loading = self.params["M1"] * k1p / (1.0 + k1p) + \
                self.params["M2"] * k2p / (1.0 + k2p) + \
                self.params["M3"] * k3p / (1.0 + k3p)

        elif self.model == "Henry":
            return self.params["KH"] * pressure

        elif self.model == "TemkinApprox":
            langmuir_fractional_loading = self.params["K"] * pressure / \
                (1.0 + self.params["K"] * pressure)
            loading = self.params["M"] * (langmuir_fractional_loading +
                                          self.params["theta"] * langmuir_fractional_loading ** 2 *
                                          langmuir_fractional_loading)

        # Ensure loading is in correct units and basis for the internal model
        if loading_unit is not None and loading_unit != self.unit_loading:
            loading = convert_loading(
                loading, self.unit_loading, loading_unit)
        if adsorbent_basis is not None and adsorbent_basis != self.basis_adsorbent:
            loading = Sample.from_list(self.sample_name, self.sample_batch).convert_basis(
                adsorbent_basis, pressure, self.unit_loading)

        return loading

    def spreading_pressure_at(self, pressure,
                              pressure_unit=None,
                              pressure_mode=None):
        """
        Calculate reduced spreading pressure at a bulk gas pressure P.

        The reduced spreading pressure is an integral involving the isotherm
        :math:`L(P)`:

        .. math::

            \\Pi(p) = \\int_0^p \\frac{L(\\hat{p})}{ \\hat{p}} d\\hat{p},

        which is computed analytically, as a function of the model isotherm
        parameters.

        Parameters
        ----------
        pressure : float
            pressure (in corresponding units as data in instantiation)

        Returns
        -------
        float
            spreading pressure, :math:`\\Pi`
        """

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_unit is not None and pressure_unit != self.unit_pressure:
            pressure = convert_pressure(
                pressure, pressure_unit, self.unit_pressure)
        if pressure_mode is not None and pressure_mode != self.mode_pressure:
            pressure = Adsorbate.from_list(self.adsorbate).convert_mode(
                pressure_mode, pressure, self.t_exp, pressure_unit)

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

    def print_info(self, logarithmic=False, show=True):
        """
        Prints a short summary of all the isotherm parameters

        Parameters
        ----------
        logarithmic : bool, optional
            Specifies if the graph printed is logarithmic or not
        show : bool, optional
            Specifies if the graph is shown automatically or not
        """

        print(self)

        print("%s identified model parameters:" % self.model)
        for param, val in self.params.items():
            print("\t%s = %f" % (param, val))
        print("RMSE = ", self.rmse)

        plot_iso([self], plot_type='isotherm',
                 logarithmic=logarithmic,

                 basis_adsorbent=self.basis_adsorbent,
                 mode_pressure=self.mode_pressure,
                 unit_loading=self.unit_pressure,
                 unit_pressure=self.unit_loading,

                 )

        if show:
            plt.show()

        return


def get_default_guess_params(model, data, pressure_key, loading_key):
    """
    Get dictionary of default parameters for starting guesses in data fitting
    routine.

    The philosophy behind the default starting guess is that (1) the saturation
    loading is close to the highest loading observed in the data, and (2) the
    default assumption is a Langmuir isotherm.

    Reminder: pass your own guess via `param_guess` in instantiation if these
    default guesses do not lead to a converged set of parameters.

    Parameters
    ----------
    model: str
        name of analytical model
    data: DataFrame
        adsorption isotherm data
    pressure_key: str
        key for pressure column in data
    loading_key: str
        key for loading column in data

    Returns
    -------
    dict
        initial parameter guesses for particular model
    """

    # guess saturation loading to 10% more than highest loading
    saturation_loading = 1.1 * data[loading_key].max()

    # guess Langmuir K using the guess for saturation loading and lowest
    # pressure point (but not zero)
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
                "M3": 0.5 * saturation_loading, "K3": 0.8 * langmuir_k}

    if model == "Henry":
        return {"KH": saturation_loading * langmuir_k}

    if model == "TemkinApprox":
        # equivalent to Langmuir model if theta = 0.0
        return {"M": saturation_loading, "K": langmuir_k, "theta": 0.0}
