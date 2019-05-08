"""Class representing a model of and isotherm."""


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
    pressure : list
        Create an isotherm directly from an array. Values for pressure.
        If the ``isotherm_data`` dataframe is specified, these values are ignored.
    loading : list
        Create an isotherm directly from an array. Values for loading.
        If the ``isotherm_data`` dataframe is specified, these values are ignored.
    isotherm_data : DataFrame
        Pure-component adsorption isotherm data.
    pressure_key : str
        Column of the pandas DataFrame where the pressure is stored.
    loading_key : str
        Column of the pandas DataFrame where the loading is stored.
    model : str
        The model to be used to describe the isotherm.
    param_guess : dict
        Starting guess for model parameters in the data fitting routine.
    branch : ['ads', 'des'], optional
        The branch on which the model isotherm is based on. It is assumed to be the
        adsorption branch, as it is the most commonly modelled part, although may
        set to desorption as well.
    material_name : str
        Name of the material on which the isotherm is measured.
    material_batch : str
        Batch (or identifier) of the material on which the isotherm is measured.
    adsorbate : str
        The adsorbate used in the experiment.
    t_iso : float
        Experiment temperature.

    Other Parameters
    ----------------
    optimization_params : dict
        Dictionary to be passed to the minimization function to use in fitting model to data.
        See `here
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html>`__.
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
        'model',
        'param_guess'
    ]

##########################################################
#   Instantiation and classmethods

    def __init__(self,
                 pressure=None,
                 loading=None,
                 isotherm_data=None,
                 pressure_key=None,
                 loading_key=None,
                 model=None,
                 param_guess=None,
                 optimization_params=None,
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

        if isotherm_data is not None:
            if None in [pressure_key, loading_key]:
                raise ParameterError(
                    "Pass loading_key and pressure_key, the names of the loading and"
                    " pressure columns in the DataFrame, to the constructor.")

            # If branch column is already set
            if 'branch' in isotherm_data.columns:
                data = isotherm_data
            else:
                data = self._splitdata(isotherm_data, pressure_key)

            if branch == 'ads':
                data = data.loc[~data['branch']]
            elif branch == 'des':
                data = data.loc[data['branch']]

            if data.empty:
                raise ParameterError(
                    "The isotherm branch does not contain enough points")

            # Get just the pressure and loading columns
            pressure = isotherm_data[pressure_key].values
            loading = isotherm_data[loading_key].values

            process = True

        elif pressure is not None or loading is not None:
            if pressure is None or loading is None:
                raise ParameterError(
                    "If you've chosen to pass loading and pressure directly as"
                    " arrays, make sure both are specified!")
            if len(pressure) != len(loading):
                raise ParameterError(
                    "Pressure and loading arrays are not equal!")

            # Ensure we are dealing with numpy arrays
            pressure = numpy.asarray(pressure)
            loading = numpy.asarray(loading)

            process = True

        elif is_base_model(model):
            self.model = model
            self.branch = branch

            process = False

        else:
            raise ParameterError(
                "Pass isotherm data to fit in a pandas.DataFrame as ``isotherm_data``"
                " or directly ``pressure`` and ``loading`` as arrays."
                "Alternatively, pass an isotherm model instance.")

        if process:

            #: Branch the isotherm model is based on.
            self.branch = branch

            #: Name of analytical model to fit to pure-component isotherm data
            #: adsorption isotherm.
            self.model = get_isotherm_model(model)

            # Pass odd parameters
            self.model.__init_parameters__(isotherm_parameters)

            #: The pressure range on which the model was built.
            self.model.pressure_range = [min(pressure), max(pressure)]

            #: The loading range on which the model was built.
            self.model.loading_range = [min(loading), max(loading)]

            #: Dictionary of parameters as a starting point for data fitting.
            self.param_guess = self.model.default_guess(pressure, loading)

            # Override defaults if user provides param_guess dictionary
            if param_guess is not None:
                for param, guess_val in param_guess.items():
                    if param not in self.param_guess.keys():
                        raise ParameterError("%s is not a valid parameter"
                                             " in the %s model." % (param, model))
                    self.param_guess[param] = guess_val

            # fit model to isotherm data
            self.model.fit(pressure, loading,
                           self.param_guess,
                           optimization_params,
                           verbose)

        # State it's a simulated isotherm
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

    @classmethod
    def from_isotherm(cls, isotherm,
                      pressure=None,
                      loading=None,
                      isotherm_data=None,
                      pressure_key=None,
                      loading_key=None,
                      model=None,
                      param_guess=None,
                      optimization_params=None,
                      branch='ads',
                      verbose=False,
                      ):
        """
        Construct a ModelIsotherm using a parent isotherm as the template for
        all the parameters.

        Parameters
        ----------

        isotherm : Isotherm
            An instance of the Isotherm parent class.
        pressure : list
            Create an isotherm directly from an array. Values for pressure.
            If the ``isotherm_data`` dataframe is specified, these values are ignored.
        loading : list
            Create an isotherm directly from an array. Values for loading.
            If the ``isotherm_data`` dataframe is specified, these values are ignored.
        isotherm_data : DataFrame
            Pure-component adsorption isotherm data.
        pressure_key : str
            Column of the pandas DataFrame where the pressure is stored.
        loading_key : str
            Column of the pandas DataFrame where the loading is stored.
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
        # insert or update values
        iso_params['pressure'] = pressure
        iso_params['loading'] = loading
        iso_params['isotherm_data'] = isotherm_data
        iso_params['pressure_key'] = pressure_key
        iso_params['loading_key'] = loading_key
        iso_params['model'] = model
        iso_params['param_guess'] = param_guess
        iso_params['optimization_params'] = optimization_params
        iso_params['branch'] = branch
        iso_params['verbose'] = verbose

        return cls(**iso_params)

    @classmethod
    def from_pointisotherm(cls,
                           isotherm,
                           model=None,
                           guess_model=None,
                           branch='ads',
                           param_guess=None,
                           optimization_params=None,
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
        guess_model : 'all', list of model names
            Attempt to guess which model best fits the isotherm data
            from the model name list supplied. If set to 'all'
            A calculation of all models available will be performed,
            therefore it will take a longer time.
        branch : [None, 'ads', 'des'], optional
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

        if guess_model:
            return ModelIsotherm.guess(isotherm_data=isotherm.data(branch=branch),
                                       pressure_key=isotherm.pressure_key,
                                       loading_key=isotherm.loading_key,
                                       models=guess_model,
                                       optimization_params=optimization_params,
                                       branch=branch,
                                       verbose=verbose,
                                       **iso_params)

        return cls(isotherm_data=isotherm.data(branch=branch),
                   pressure_key=isotherm.pressure_key,
                   loading_key=isotherm.loading_key,
                   model=model,
                   param_guess=param_guess,
                   optimization_params=optimization_params,
                   branch=branch,
                   verbose=verbose,
                   **iso_params)

    @classmethod
    def guess(cls,
              pressure=None,
              loading=None,
              isotherm_data=None,
              pressure_key=None,
              loading_key=None,
              models='all',
              optimization_params=None,
              branch='ads',
              verbose=False,

              **isotherm_parameters):
        """
        Attempt to model the data using supplied list of model names,
        then return the one with the best rms fit.

        May take a long time depending on the number of datapoints.

        Parameters
        ----------
        pressure : list
            Create an isotherm directly from an array. Values for pressure.
            If the ``isotherm_data`` dataframe is specified, these values are ignored.
        loading : list
            Create an isotherm directly from an array. Values for loading.
            If the ``isotherm_data`` dataframe is specified, these values are ignored.
        isotherm_data : DataFrame
            Pure-component adsorption isotherm data.
        pressure_key : str
            Column of the pandas DataFrame where the pressure is stored.
        loading_key : str
            Column of the pandas DataFrame where the loading is stored.
        models : 'all', list of model names
            Attempt to guess which model best fits the isotherm data
            from the model name list supplied. If set to 'all'
            A calculation of all models available will be performed,
            therefore it will take a longer time.

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
        if models == 'all':
            guess_models = [md.name for md in _GUESS_MODELS]
        else:
            guess_models = list(m for m in [md.name for md in _GUESS_MODELS] if m in models)
            if len(guess_models) != len(models):
                raise ParameterError('Not all models provided correspond to internal models')

        for model in guess_models:
            try:
                isotherm = ModelIsotherm(pressure=pressure,
                                         loading=loading,
                                         isotherm_data=isotherm_data,
                                         pressure_key=pressure_key,
                                         loading_key=loading_key,
                                         model=model,
                                         param_guess=None,
                                         optimization_params=optimization_params,
                                         branch=branch,
                                         verbose=verbose,

                                         **isotherm_parameters)

                attempts.append(isotherm)

            except CalculationError:
                if verbose:
                    print("Modelling using {0} failed".format(model))

        if not attempts:
            raise CalculationError(
                "No model could be reliably fit on the isotherm")

        errors = [x.model.rmse for x in attempts]
        best_fit = attempts[errors.index(min(errors))]

        if verbose:
            print("Best model fit is {0}".format(best_fit.model.name))

        return best_fit

###########################################################
#   Info function

    def print_info(self, show=True, **plot_iso_args):
        """
        Print a short summary of the isotherm parameters and a graph.

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
        axes : matplotlib.axes.Axes or numpy.ndarray of them

        """
        print(self)
        print(self.model)
        return self.plot(show, **plot_iso_args)

    def plot(self, show=True, **plot_iso_args):
        """
        Plot the isotherm using pygaps.plot_iso().

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
        axes : matplotlib.axes.Axes or numpy.ndarray of them

        """
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

        axes = plot_iso(self, **plot_dict)

        if show:
            plt.show()
            return None

        return axes

##########################################################
#   Methods

    def has_branch(self, branch):
        """
        Check if the isotherm has an specific branch.

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
        return False

    def pressure(self, points=20, branch=None,
                 pressure_unit=None, pressure_mode=None,
                 min_range=None, max_range=None, indexed=False):
        """
        Return a numpy.linspace generated array with
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
            ret = numpy.linspace(self.model.pressure_range[0],
                                 self.model.pressure_range[1],
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
                                 temp=self.t_iso
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

            ret = list(filter(lambda x: min_range <= x <= max_range, ret))

        if indexed:
            return pandas.Series(ret)
        return ret

    def loading(self, points=20, branch=None,
                loading_unit=None, loading_basis=None,
                adsorbent_unit=None, adsorbent_basis=None,
                min_range=None, max_range=None, indexed=False):
        """
        Return the loading calculated at equidistant pressure
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
            ret = numpy.linspace(self.model.loading_range[0],
                                 self.model.loading_range[1],
                                 points)

            if adsorbent_basis or adsorbent_unit:
                if not adsorbent_basis:
                    adsorbent_basis = self.adsorbent_basis

                ret = c_adsorbent(ret,
                                  basis_from=self.adsorbent_basis,
                                  basis_to=adsorbent_basis,
                                  unit_from=self.adsorbent_unit,
                                  unit_to=adsorbent_unit,
                                  material_name=self.material_name,
                                  material_batch=self.material_batch
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
                                temp=self.t_iso
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

            ret = list(filter(lambda x: min_range <= x <= max_range, ret))

        if indexed:
            return pandas.Series(ret)
        else:
            return ret

##########################################################
#   Functions that calculate values of the isotherm data

    def loading_at(self, pressure, branch=None,

                   pressure_unit=None, pressure_mode=None,
                   loading_unit=None, loading_basis=None,
                   adsorbent_unit=None, adsorbent_basis=None,
                   ):
        """
        Compute loading at pressure P, given stored model parameters.

        Depending on the model, may be calculated directly or through
        a numerical minimisation.

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

        # Convert to numpy array just in case
        pressure = numpy.asarray(pressure)

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
                                  temp=self.t_iso)

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
                                  material_name=self.material_name,
                                  material_batch=self.material_batch
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
                                temp=self.t_iso
                                )

        return loading

    def pressure_at(self, loading, branch=None,

                    pressure_unit=None, pressure_mode=None,
                    loading_unit=None, loading_basis=None,
                    adsorbent_unit=None, adsorbent_basis=None,
                    ):
        """
        Compute pressure at loading L, given stored model parameters.

        Depending on the model, may be calculated directly or through
        a numerical minimisation.

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

        # Convert to numpy array just in case
        loading = numpy.asarray(loading)

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
                                  material_name=self.material_name,
                                  material_batch=self.material_batch
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
                                temp=self.t_iso
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
                                  temp=self.t_iso)

        return pressure

    def spreading_pressure_at(self, pressure, branch=None,

                              pressure_unit=None,
                              pressure_mode=None):
        r"""
        Calculate reduced spreading pressure at a bulk gas pressure P.

        The reduced spreading pressure is an integral involving the isotherm
        :math:`L(P)`:

        .. math::

            \Pi(p) = \int_0^p \frac{L(\hat{p})}{ \hat{p}} d\hat{p},

        which is computed analytically or numerically, depending on the
        model used.

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
            Spreading pressure, :math:`\Pi`.

        """
        if branch and branch != self.branch:
            raise ParameterError(
                "ModelIsotherm is not based off this isotherm branch")

        # Convert to numpy array just in case
        pressure = numpy.asarray(pressure)

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
                                  temp=self.t_iso)

        # based on model
        spreading_p = self.model.spreading_pressure(pressure)

        return spreading_p
