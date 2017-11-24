"""
This module contains objects to model pure-component adsorption
isotherms from experimental or simulated data.
"""


import matplotlib.pyplot as plt
import numpy
import pandas
import scipy.optimize

from ..graphing.isothermgraphs import plot_iso
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.unit_converter import c_adsorbent
from ..utilities.unit_converter import c_loading
from ..utilities.unit_converter import c_pressure
from .isotherm import Isotherm
from ..calculations.models_isotherm import get_isotherm_model
from ..calculations.models_isotherm import _MODELS


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
    sample_name : str
        Name of the sample on which the isotherm is measured.
    sample_batch : str
        Batch (or identifier) of the sample on which the isotherm is measured.
    adsorbate : str
        The adsorbate used in the experiment.
    t_exp : float
        Experiment temperature.
    isotherm_parameters : dict
        Any other parameters of the isotherm which should be stored
        internally. Pass a dictionary of the form::

            isotherm_params = {
                'user' : 'John Doe',
                'doi' : '10.0000/',
                'x' : 'y',
                }
            }

    Other Parameters
    ----------------
    adsorbent_basis : str, optional
        Whether the adsorption is read in terms of either 'per volume'
        'per molar amount' or 'per mass' of material.
    adsorbent_unit : str, optional
        Unit in which the adsorbent basis is expressed.
    loading_basis : str, optional
        Whether the adsorbed material is read in terms of either 'volume'
        'molar' or 'mass'.
    loading_unit : str, optional
        Unit in which the loading basis is expressed.
    pressure_mode : str, optional
        The pressure mode, either 'absolute' pressures or 'relative' in
        the form of p/p0.
    pressure_unit : str, optional
        Unit of pressure.
    verbose : bool
        Prints out extra information about steps taken.

    Notes
    -----

    Models supported are found in the :mod:calculations.models_isotherm.
    Here, :math:`L` is the adsorbate uptake and
    :math:`P` is pressure (fugacity technically).

    """

##########################################################
#   Instantiation and classmethods

    def __init__(self, isotherm_data,
                 loading_key=None,
                 pressure_key=None,
                 model=None,
                 param_guess=None,
                 optimization_method="Nelder-Mead",
                 branch='ads',
                 verbose=False,

                 adsorbent_basis="mass",
                 adsorbent_unit="g",
                 loading_basis="molar",
                 loading_unit="mmol",
                 pressure_mode="absolute",
                 pressure_unit="bar",

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

        # We change it to a simulated isotherm
        isotherm_parameters['is_real'] = False

        # Run base class constructor
        Isotherm.__init__(self,
                          pressure_key=pressure_key,
                          loading_key=loading_key,

                          adsorbent_basis=adsorbent_basis,
                          adsorbent_unit=adsorbent_unit,
                          loading_basis=loading_basis,
                          loading_unit=loading_unit,
                          pressure_mode=pressure_mode,
                          pressure_unit=pressure_unit,

                          **isotherm_parameters)

        # Get required branch
        data = self._splitdata(isotherm_data)

        if branch == 'ads':
            data = data.loc[~data['check']]
        elif branch == 'des':
            data = data.loc[data['check']]

        #: Branch the isotherm model is based on
        self.branch = branch

        #: The pressure range on which the model was built
        self.pressure_range = [min(data[pressure_key]),
                               max(data[pressure_key])]

        #: Name of analytical model to fit to pure-component isotherm data
        #: adsorption isotherm
        self.model = get_isotherm_model(model)

        # ! root mean square error in fit
        self.rmse = numpy.nan

        # ! Dictionary of parameters as a starting point for data fitting
        self.param_guess = get_default_guess_params(self.model, isotherm_data, pressure_key,
                                                    loading_key)

        # Override defaults if user provides param_guess dictionary
        if param_guess is not None:
            for param, guess_val in param_guess.items():
                if param not in self.param_guess.keys():
                    raise ParameterError("%s is not a valid parameter"
                                         " in the %s model." % (param, model))
                self.param_guess[param] = guess_val

        # fit model to isotherm data
        self._fit(data[loading_key].values,
                  data[pressure_key].values,
                  optimization_method,
                  verbose)

    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data,
                      model=None,
                      param_guess=None,
                      optimization_method="Nelder-Mead",
                      branch='ads',
                      verbose=False,
                      ):
        """
        Constructs a ModelIsotherm using a parent isotherm as the template for
        all the parameters.

        Parameters
        ----------

        isotherm : Isotherm
            an instance of the Isotherm parent class
        isotherm_data : DataFrame
            pure-component adsorption isotherm data
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
        """
        return cls(isotherm_data,
                   model=model,
                   param_guess=param_guess,
                   optimization_method=optimization_method,
                   branch=branch,
                   verbose=verbose,

                   loading_key=isotherm.loading_key,
                   pressure_key=isotherm.pressure_key,
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
                                       optimization_method=optimization_method,
                                       branch=branch,
                                       verbose=verbose,

                                       loading_key=isotherm.loading_key,
                                       pressure_key=isotherm.pressure_key,
                                       **isotherm.to_dict())

        return cls(isotherm.data(branch=branch),
                   model=model,
                   param_guess=param_guess,
                   optimization_method=optimization_method,
                   branch=branch,
                   verbose=verbose,

                   loading_key=isotherm.loading_key,
                   pressure_key=isotherm.pressure_key,
                   **isotherm.to_dict())

    @classmethod
    def guess(cls, data,
              loading_key=None,
              pressure_key=None,
              optimization_method="Nelder-Mead",
              branch='ads',
              verbose=False,

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
        isotherm_parameters:
            Any other parameters of the isotherm which should be stored internally.
        """
        attempts = []
        for model in _MODELS:
            try:
                isotherm = ModelIsotherm(data,
                                         loading_key=loading_key,
                                         pressure_key=pressure_key,
                                         model=model.name,
                                         param_guess=None,
                                         optimization_method=optimization_method,
                                         branch=branch,
                                         verbose=verbose,

                                         **isotherm_parameters)

                attempts.append(isotherm)

            except CalculationError:
                if verbose:
                    print("Modelling using {0} failed".format(model.name))

        if not attempts:
            raise CalculationError(
                "No model could be reliably fit on the isotherm")
        else:
            errors = [x.rmse for x in attempts]
            best_fit = attempts[errors.index(min(errors))]

            if verbose:
                print("Best model fit is {0}".format(best_fit.model.name))

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
            The loading for each point.
        pressure : ndarray
            The pressures of each point.
        optimization_method : str
            Method in SciPy minimization function to use in fitting model to data.
        verbose : bool, optional
            Prints out extra information about steps taken.
        """
        if verbose:
            print("Attempting to model using {}".format(self.model.name))

        # parameter names (cannot rely on order in Dict)
        param_names = [param for param in self.model.params.keys()]
        # guess
        guess = numpy.array([self.param_guess[param] for param in param_names])

        def residual_sum_of_squares(params_):
            """
            Residual Sum of Squares between model and data in data
            """
            # change params to those in x
            for i, _ in enumerate(param_names):
                self.model.params[param_names[i]] = params_[i]

            return numpy.sum((loading - self.loading_at(pressure)) ** 2)

        # minimize RSS
        opt_res = scipy.optimize.minimize(residual_sum_of_squares, guess,
                                          method=optimization_method)
        if not opt_res.success:
            raise CalculationError("""
            Minimization of RSS for {0} isotherm fitting failed with error:
            \n\t {1}
            Try a different starting point in the nonlinear optimization
            by passing a dictionary of parameter guesses, param_guess, to the
            constructor.
            "\n\tDefault starting guess for parameters: {2}"
            """.format(self.model.name, opt_res.message, self.param_guess))

        # assign params
        for index, _ in enumerate(param_names):
            self.model.params[param_names[index]] = opt_res.x[index]

        self.rmse = numpy.sqrt(opt_res.fun / len(pressure))

        if verbose:
            print("Model {0} success, rmse is {1}".format(
                self.model.name, self.rmse))

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

    def pressure(self, points=20, branch=None,
                 pressure_unit=None, pressure_mode=None,
                 min_range=None, max_range=None, indexed=False):
        """
        Returns a numpy.linspace generated array with
        a fixed number of equidistant points within the
        pressure range the model was created.

        Parameters
        ----------
        points : int
            The number of points to get.
        branch : {None, 'ads', 'des'}
            The branch of the pressure to return. If None, returns the branch
            the isotherm is modelled on
        pressure_unit : str, optional
            Unit in which the pressure should be returned. If None
            it defaults to which pressure unit the isotherm is currently in
        modpressure_modee : {None, 'absolute', 'relative'}
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
        numpy.array or pandas.Series
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
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if not pressure_unit:
                pressure_unit = self.pressure_unit

            ret = c_pressure(ret,
                             mode_from=self.pressure_mode,
                             mode_to=pressure_mode,
                             unit_from=self.pressure_unit,
                             unit_to=pressure_unit,
                             adsorbate_name=self.adsorbate,
                             temp=self.t_exp
                             )

        # Select required points
        if max_range is not None or min_range is not None:
            if min_range is None:
                min_range = min(ret)
            if max_range is None:
                max_range = max(ret)

            ret = list(filter(lambda x: x >= min_range and x <= max_range, ret))

        if indexed:
            return pandas.Series(ret)
        else:
            return ret

    def loading(self, points=20, branch=None,
                loading_unit=None, loading_basis=None,
                adsorbent_unit=None, adsorbent_basis=None,
                min_range=None, max_range=None, indexed=False):
        """
        Returns the loading calculated at equidistant pressure
        points within the pressure range the model was created.

        Parameters
        ----------
        points : int
            The number of points to get.
        branch : {None, 'ads', 'des'}
            The branch of the loading to return. If None, returns entire
            dataset
        loading_unit : str, optional
            Unit in which the loading should be returned. If None
            it defaults to which loading unit the isotherm is currently in
        loading_basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If None,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If None
            it defaults to which loading unit the isotherm is currently in
        adsorbent_basis : {None, 'mass', 'volume'}
            The basis on which to return the adsorbent, if possible. If None,
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
        numpy.array or pandas.Series
            Loading calculated at points the model pressure range.
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")

        ret = self.loading_at(
            self.pressure(points),
            loading_unit=loading_unit,
            loading_basis=loading_basis,
            adsorbent_unit=adsorbent_unit,
            adsorbent_basis=adsorbent_basis,
        )

        # Select required points
        if max_range is not None or min_range is not None:
            if min_range is None:
                min_range = min(ret)
            if max_range is None:
                max_range = max(ret)

            ret = list(filter(lambda x: x >= min_range and x <= max_range, ret))

        if indexed:
            return pandas.Series(ret)
        else:
            return ret

##########################################################
#   Functions that calculate values of the isotherm data

    def loading_at(self, pressure,
                   branch=None,

                   pressure_unit=None, pressure_mode=None,
                   loading_unit=None, loading_basis=None,
                   adsorbent_unit=None, adsorbent_basis=None,
                   ):
        """
        Given stored model parameters, compute loading at pressure P.

        Parameters
        ----------
        pressure : float or array
            Pressure at which to compute loading.
        branch : {None, 'ads', 'des'}
            The branch the calculation is based on.

        pressure_unit : str
            Unit the pressure is specified in. If None, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is passed in. If None, it defaults to
            internal isotherm mode.

        loading_unit : str, optional
            Unit in which the loading should be returned. If None
            it defaults to which loading unit the isotherm is currently in
        loading_basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If None,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If None
            it defaults to which loading unit the isotherm is currently in
        adsorbent_basis : {None, 'mass', 'volume'}
            The basis on which to return the adsorbent, if possible. If None,
            returns on the basis the isotherm is currently in.

        Returns
        -------
        float or array
            predicted loading at pressure P using fitted model
            parameters
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")
        else:
            branch = self.branch

        # Convert to numpy array just in case
        pressure = numpy.array(pressure)

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if not pressure_unit:
                pressure_unit = self.pressure_unit
            if not pressure_unit and self.pressure_mode == 'relative':
                raise ParameterError("Must specify a pressure unit if the input"
                                     " is in an absolute mode")

            pressure = c_pressure(pressure,
                                  mode_from=pressure_mode,
                                  mode_to=self.pressure_mode,
                                  unit_from=pressure_unit,
                                  unit_to=self.pressure_unit,
                                  adsorbate_name=self.adsorbate,
                                  temp=self.t_exp)

        # Calculate loading using internal model
        loading = self.model.loading(pressure)

        # Ensure loading is in correct units and basis requested
        if adsorbent_basis or adsorbent_unit:
            if not adsorbent_basis:
                adsorbent_basis = self.adsorbent_basis

            loading = c_adsorbent(loading,
                                  basis_from=self.adsorbent_basis,
                                  basis_to=adsorbent_basis,
                                  unit_from=self.adsorbent_unit,
                                  unit_to=adsorbent_unit,
                                  sample_name=self.sample_name,
                                  sample_batch=self.sample_batch
                                  )

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.loading_basis

            loading = c_loading(loading,
                                basis_from=self.loading_basis,
                                basis_to=loading_basis,
                                unit_from=self.loading_unit,
                                unit_to=loading_unit,
                                adsorbate_name=self.adsorbate,
                                temp=self.t_exp
                                )

        return loading

    def pressure_at(self, loading,
                    branch=None,

                    pressure_unit=None, pressure_mode=None,
                    loading_unit=None, loading_basis=None,
                    adsorbent_unit=None, adsorbent_basis=None,
                    ):
        """
        Given stored model parameters, compute pressure at loading L.

        Parameters
        ----------
        loading : float or array
            Loading at which to compute pressure.
        branch : {None, 'ads', 'des'}
            The branch the calculation is based on.

        pressure_unit : str
            Unit the pressure is returned in. If None, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is returned in. If None, it defaults to
            internal isotherm mode.

        loading_unit : str
            Unit the loading is specified in. If None, it defaults to
            internal isotherm units.
        loading_basis : {None, 'mass', 'volume'}
            The basis the loading is specified in. If None,
            assumes the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent is passed in. If None
            it defaults to which loading unit the isotherm is currently in
        adsorbent_basis : str
            The basis the loading is passed in. If None, it defaults to
            internal isotherm basis.

        Returns
        -------
        float or array
            predicted pressure at loading L using fitted model
            parameters
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")
        else:
            branch = self.branch

        # Convert to numpy array just in case
        loading = numpy.array(loading)

        # Ensure loading is in correct units and basis for the internal model
        if adsorbent_basis or adsorbent_unit:
            if not adsorbent_basis:
                adsorbent_basis = self.adsorbent_basis
            if not adsorbent_unit:
                raise ParameterError("Must specify an adsorbent unit if the input"
                                     " is in another basis")

            loading = c_adsorbent(loading,
                                  basis_from=adsorbent_basis,
                                  basis_to=self.adsorbent_basis,
                                  unit_from=adsorbent_unit,
                                  unit_to=self.adsorbent_unit,
                                  sample_name=self.sample_name,
                                  sample_batch=self.sample_batch
                                  )

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.loading_basis
            if not loading_unit:
                raise ParameterError("Must specify a loading unit if the input"
                                     " is in another basis")

            loading = c_loading(loading,
                                basis_from=loading_basis,
                                basis_to=self.loading_basis,
                                unit_from=loading_unit,
                                unit_to=self.loading_unit,
                                adsorbate_name=self.adsorbate,
                                temp=self.t_exp
                                )

        # Calculate pressure using internal model
        pressure = self.model.pressure(loading)

        # Ensure pressure is in correct units and mode requested
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if not pressure_unit:
                pressure_unit = self.pressure_unit

            pressure = c_pressure(pressure,
                                  mode_from=self.pressure_mode,
                                  mode_to=pressure_mode,
                                  unit_from=self.pressure_unit,
                                  unit_to=pressure_unit,
                                  adsorbate_name=self.adsorbate,
                                  temp=self.t_exp)

        return pressure

    def spreading_pressure_at(self, pressure,
                              branch=None,
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
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.
        pressure_unit : str
            Unit the pressure is returned in. If None, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is returned in. If None, it defaults to
            internal isotherm mode.

        Returns
        -------
        float
            spreading pressure, :math:`\\Pi`
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")
        else:
            branch = self.branch

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if not pressure_unit:
                pressure_unit = self.pressure_unit
            if not pressure_unit and self.pressure_mode == 'relative':
                raise ParameterError("Must specify a pressure unit if the input"
                                     " is in an absolute mode")

            pressure = c_pressure(pressure,
                                  mode_from=pressure_mode,
                                  mode_to=self.pressure_mode,
                                  unit_from=pressure_unit,
                                  unit_to=self.pressure_unit,
                                  adsorbate_name=self.adsorbate,
                                  temp=self.t_exp)

        # based on model
        spreading_p = self.model.spreading_pressure(pressure)

        return spreading_p

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

        print("%s identified model parameters:" % self.model.name)
        for param, val in self.model.params.items():
            print("\t%s = %f" % (param, val))
        print("RMSE = ", self.rmse)

        plot_iso([self], plot_type='isotherm',
                 logx=logarithmic,

                 adsorbent_basis=self.adsorbent_basis,
                 adsorbent_unit=self.adsorbent_unit,
                 loading_basis=self.loading_basis,
                 loading_unit=self.loading_unit,
                 pressure_unit=self.pressure_unit,
                 pressure_mode=self.pressure_mode,

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
    model: IsothermModel
        Analytical model
    data: DataFrame
        Adsorption isotherm data.
    pressure_key: str
        Key for pressure column in data.
    loading_key: str
        Key for loading column in data.

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

    return model.default_guess(saturation_loading, langmuir_k)
