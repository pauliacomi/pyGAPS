"""
This module contains objects to model pure-component adsorption
isotherms from experimental or simulated data.
"""


import matplotlib.pyplot as plt
import numpy
import pandas

from ..calculations.models_isotherm import _GUESS_MODELS
from ..calculations.models_isotherm import get_isotherm_model
from ..calculations.models_isotherm import is_base_model
from ..graphing.isothermgraphs import plot_iso
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.unit_converter import c_adsorbent
from ..utilities.unit_converter import c_loading
from ..utilities.unit_converter import c_pressure
from .isotherm import Isotherm


class ModelIsotherm(Isotherm):
    """
    Class to characterize pure-component isotherm data with an analytical model.
    Data fitting is done during instantiation.

    A `ModelIsotherm` class is instantiated by passing it the
    pure-component adsorption isotherm in the form of a Pandas DataFrame.

    Parameters
    ----------
    isotherm_data : DataFrame
        Pure-component adsorption isotherm data.
    loading_key : str
        Column of the pandas DataFrame where the loading is stored.
    pressure_key : str
        Column of the pandas DataFrame where the pressure is stored.
    model : str
        The model to be used to describe the isotherm.
    param_guess : dict
        Starting guess for model parameters in the data fitting routine.
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

    Other Parameters
    ----------------
    optimization_params : dict
        Dictionary to be passed to the minimization function to use in fitting model to data.
        See `here
        <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
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

    _reserved_params = [
        '_instantiated',
        'model',
    ]

##########################################################
#   Instantiation and classmethods

    def __init__(self, isotherm_data,
                 loading_key=None,
                 pressure_key=None,
                 model=None,
                 param_guess=None,
                 optimization_params=dict(method='Nelder-Mead'),
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
        class.
        """
        # Checks
        if model is None:
            raise ParameterError("Specify a model to fit to the pure-component"
                                 " isotherm data. e.g. model=\"Langmuir\"")

        # Start construction process
        self._instantiated = False

        # We change it to a simulated isotherm
        isotherm_parameters['is_real'] = False

        # Run base class constructor
        Isotherm.__init__(self,
                          adsorbent_basis=adsorbent_basis,
                          adsorbent_unit=adsorbent_unit,
                          loading_basis=loading_basis,
                          loading_unit=loading_unit,
                          pressure_mode=pressure_mode,
                          pressure_unit=pressure_unit,

                          **isotherm_parameters)

        # Column titles
        if None in [loading_key, pressure_key]:
            raise ParameterError(
                "Pass loading_key and pressure_key, the names of the loading and"
                " pressure columns in the DataFrame, to the constructor.")

        if is_base_model(model):
            self.model = model

            self.rmse = 0
            self.branch = 'ads'
            self.pressure_range = [0, 1]
            self.loading_range = [0, 1]

        else:

            # Get required branch
            data = self._splitdata(isotherm_data, pressure_key)

            if branch == 'ads':
                data = data.loc[~data['branch']]
            elif branch == 'des':
                data = data.loc[data['branch']]

            if data.empty:
                raise ParameterError(
                    "The isotherm branch does not contain enough points")

            #: Branch the isotherm model is based on.
            self.branch = branch

            #: The pressure range on which the model was built.
            self.pressure_range = [min(data[pressure_key]),
                                   max(data[pressure_key])]

            #: The loading range on which the model was built.
            self.loading_range = [min(data[loading_key]),
                                  max(data[loading_key])]

            #: Name of analytical model to fit to pure-component isotherm data
            #: adsorption isotherm.
            self.model = get_isotherm_model(model)

            #: Dictionary of parameters as a starting point for data fitting.
            self.param_guess = self.model.default_guess(isotherm_data,
                                                        loading_key,
                                                        pressure_key)

            # Override defaults if user provides param_guess dictionary
            if param_guess is not None:
                for param, guess_val in param_guess.items():
                    if param not in self.param_guess.keys():
                        raise ParameterError("%s is not a valid parameter"
                                             " in the %s model." % (param, model))
                    self.param_guess[param] = guess_val

            #: Root mean square error in fit.
            self.rmse = numpy.nan

            # fit model to isotherm data
            self.rmse = self.model.fit(data[loading_key].values,
                                       data[pressure_key].values,
                                       self.param_guess,
                                       optimization_params,
                                       verbose)

        # Finish instantiation process
        self._instantiated = True

        # Now that all data has been saved, generate the unique id if needed.
        if self.id is None:
            self._check_if_hash(True, [True])

    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data,
                      loading_key=None,
                      pressure_key=None,
                      model=None,
                      param_guess=None,
                      optimization_params=dict(method='Nelder-Mead'),
                      branch='ads',
                      verbose=False,
                      ):
        """
        Constructs a ModelIsotherm using a parent isotherm as the template for
        all the parameters.

        Parameters
        ----------

        isotherm : Isotherm
            An instance of the Isotherm parent class.
        isotherm_data : DataFrame
            Pure-component adsorption isotherm data.
        loading_key : str
            Column of the pandas DataFrame where the loading is stored.
        pressure_key : str
            Column of the pandas DataFrame where the pressure is stored.
        model : str
            The model to be used to describe the isotherm.
        param_guess : dict
            Starting guess for model parameters in the data fitting routine.
        optimization_params : dict
            Dictionary to be passed to the minimization function to use in fitting model to data.
            See `here
            <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
            Defaults to "Nelder-Mead".
        branch : ['ads', 'des'], optional
            The branch on which the model isotherm is based on. It is assumed to be the
            adsorption branch, as it is the most commonly modelled part, although may
            set to desorption as well.
        verbose : bool
            Prints out extra information about steps taken.
        """
        # get isotherm parameters as a dictionary
        iso_params = isotherm.to_dict()
        # remove ID - a new one will be generated
        iso_params.pop('id', None)
        # insert or update values
        iso_params['loading_key'] = loading_key
        iso_params['pressure_key'] = pressure_key
        iso_params['model'] = model
        iso_params['param_guess'] = param_guess
        iso_params['optimization_params'] = optimization_params
        iso_params['branch'] = branch
        iso_params['verbose'] = verbose

        return cls(isotherm_data, **iso_params)

    @classmethod
    def from_pointisotherm(cls,
                           isotherm,
                           model=None,
                           guess_model=False,
                           branch='ads',
                           param_guess=None,
                           optimization_params=dict(method='Nelder-Mead'),
                           verbose=False):
        """
        Constructs a ModelIsotherm using a the data from a PointIsotherm
        and all its parameters.

        Parameters
        ----------
        isotherm : PointIsotherm
            An instance of the PointIsotherm parent class to model.
        model : str
            The model to be used to describe the isotherm.
        guess_model : bool
            Set to true if you want to attempt to guess which model best
            fits the isotherm data. This will mean a calculation of all
            models available, so it will take a longer time.
        branch : {None, 'ads', 'des'}, optional
            Branch of isotherm to model. Defaults to adsorption branch.
        param_guess : dict, optional
            Starting guess for model parameters in the data fitting routine.
        optimization_params : dict, optional
            Dictionary to be passed to the minimization function to use in fitting model to data.
            See `here
            <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
        verbose : bool
            Prints out extra information about steps taken.
        """
        # get isotherm parameters as a dictionary
        iso_params = isotherm.to_dict()
        # remove ID - a new one will be generated
        iso_params.pop('id', None)

        if guess_model:
            return ModelIsotherm.guess(isotherm.data(branch=branch),
                                       loading_key=isotherm.loading_key,
                                       pressure_key=isotherm.pressure_key,
                                       optimization_params=optimization_params,
                                       branch=branch,
                                       verbose=verbose,
                                       **iso_params)

        return cls(isotherm.data(branch=branch),
                   loading_key=isotherm.loading_key,
                   pressure_key=isotherm.pressure_key,
                   model=model,
                   param_guess=param_guess,
                   optimization_params=optimization_params,
                   branch=branch,
                   verbose=verbose,
                   **iso_params)

    @classmethod
    def guess(cls, data,
              loading_key=None,
              pressure_key=None,
              optimization_params=dict(method='Nelder-Mead'),
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

        optimization_params : dict
            Dictionary to be passed to the minimization function to use in fitting model to data.
            See `here
            <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
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
        for model in _GUESS_MODELS:
            try:
                isotherm = ModelIsotherm(data,
                                         loading_key=loading_key,
                                         pressure_key=pressure_key,
                                         model=model.name,
                                         param_guess=None,
                                         optimization_params=optimization_params,
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

    def __setattr__(self, name, value):
        """
        We overload the usual class setter to make sure that the id is always
        representative of the data inside the isotherm.

        The '_instantiated' attribute gets set to true after isotherm __init__
        From then afterwards, each call to modify the isotherm properties
        recalculates the md5 hash.
        This is done to ensure uniqueness and also to allow isotherm objects to
        be easily compared to each other.
        """
        object.__setattr__(self, name, value)
        self._check_if_hash(name, ['model'])

##########################################################
#   Methods

    def has_branch(self, branch):
        """
        Returns if the isotherm has an specific branch.

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the data to check for.

        Returns
        -------
        bool
            Whether the data exists or not.
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
            The branch of the pressure to return. If ``None``, returns the branch
            the isotherm is modelled on.
        pressure_unit : str, optional
            Unit in which the pressure should be returned. If None
            it defaults to which pressure unit the isotherm is currently in.
        pressure_mode : {None, 'absolute', 'relative'}
            The mode in which to return the pressure, if possible. If ``None``,
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
        if self.model.calculates == 'loading':
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
        else:
            ret = self.pressure_at(
                self.loading(points),
                pressure_mode=pressure_mode,
                pressure_unit=pressure_unit,
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
            The branch of the loading to return. If ``None``, returns entire
            dataset.
        loading_unit : str, optional
            Unit in which the loading should be returned. If None
            it defaults to which loading unit the isotherm is currently in.
        loading_basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If None
            it defaults to which loading unit the isotherm is currently in.
        adsorbent_basis : {None, 'mass', 'volume'}
            The basis on which to return the adsorbent, if possible. If ``None``,
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

        if self.model.calculates == 'pressure':
            ret = numpy.linspace(self.loading_range[0],
                                 self.loading_range[1],
                                 points)

            if adsorbent_basis or adsorbent_unit:
                if not adsorbent_basis:
                    adsorbent_basis = self.adsorbent_basis

                ret = c_adsorbent(ret,
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

                ret = c_loading(ret,
                                basis_from=self.loading_basis,
                                basis_to=loading_basis,
                                unit_from=self.loading_unit,
                                unit_to=loading_unit,
                                adsorbate_name=self.adsorbate,
                                temp=self.t_exp
                                )
        else:
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
            Unit the pressure is specified in. If ``None``, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is passed in. If ``None``, it defaults to
            internal isotherm mode.

        loading_unit : str, optional
            Unit in which the loading should be returned. If None
            it defaults to which loading unit the isotherm is currently in.
        loading_basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If None
            it defaults to which loading unit the isotherm is currently in.
        adsorbent_basis : {None, 'mass', 'volume'}
            The basis on which to return the adsorbent, if possible. If ``None``,
            returns on the basis the isotherm is currently in.

        Returns
        -------
        float or array
            Predicted loading at pressure P using fitted model
            parameters.
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")
        else:
            branch = self.branch

        # Convert to numpy array just in case
        pressure = numpy.array(pressure, ndmin=1)

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if pressure_mode == 'absolute' and not pressure_unit:
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
        loading = numpy.apply_along_axis(self.model.loading, 0, pressure)

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
            Unit the pressure is returned in. If ``None``, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is returned in. If ``None``, it defaults to
            internal isotherm mode.

        loading_unit : str
            Unit the loading is specified in. If ``None``, it defaults to
            internal isotherm units.
        loading_basis : {None, 'mass', 'volume'}
            The basis the loading is specified in. If ``None``,
            assumes the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent is passed in. If None
            it defaults to which loading unit the isotherm is currently in
        adsorbent_basis : str
            The basis the loading is passed in. If ``None``, it defaults to
            internal isotherm basis.

        Returns
        -------
        float or array
            Predicted pressure at loading L using fitted model
            parameters.
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")
        else:
            branch = self.branch

        # Convert to numpy array just in case
        loading = numpy.array(loading, ndmin=1)

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
        pressure = numpy.apply_along_axis(self.model.pressure, 0, loading)

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
            Pressure (in corresponding units as data in instantiation)
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.
        pressure_unit : str
            Unit the pressure is returned in. If ``None``, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is returned in. If ``None``, it defaults to
            internal isotherm mode.

        Returns
        -------
        float
            Spreading pressure, :math:`\\Pi`.
        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")
        else:
            branch = self.branch

        pressure = numpy.array(pressure, ndmin=1)

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
        spreading_p = numpy.apply_along_axis(
            self.model.spreading_pressure, 0, pressure)

        return spreading_p

###########################################################
#   Info function

    def print_info(self, show=True, **plot_iso_args):
        """
        Prints a short summary of all the isotherm parameters and a
        graph of the isotherm.

        Parameters
        ----------
        show : bool, optional
            Specifies if the graph is shown automatically or not.

        Other Parameters
        ----------------
        plot_iso_args : dict
            options to be passed to pygaps.plot_iso()

        Returns
        -------
        fig : Matplotlib figure
            The figure object generated. Only returned if graph is not shown.
        ax1 : Matplotlib ax
            Ax object for primary graph. Only returned if graph is not shown.
        ax2 : Matplotlib ax
            Ax object for secondary graph. Only returned if graph is not shown.
        """

        print(self)

        print("%s identified model parameters:" % self.model.name)
        for param, val in self.model.params.items():
            print("\t%s = %f" % (param, val))
        print("RMSE = ", self.rmse)

        plot_dict = dict(
            plot_type='isotherm',
            adsorbent_basis=self.adsorbent_basis,
            adsorbent_unit=self.adsorbent_unit,
            loading_basis=self.loading_basis,
            loading_unit=self.loading_unit,
            pressure_unit=self.pressure_unit,
            pressure_mode=self.pressure_mode,
        )
        plot_dict.update(plot_iso_args)

        fig, ax1, ax2 = plot_iso(self, **plot_dict)

        if show:
            plt.show()
            return

        return fig, ax1, ax2
