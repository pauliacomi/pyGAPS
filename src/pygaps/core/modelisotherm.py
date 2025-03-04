"""Class representing a model of and isotherm."""

import typing as t

import numpy
import pandas

from pygaps import logger
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.modelling import _GUESS_MODELS
from pygaps.modelling import get_isotherm_model
from pygaps.modelling import is_model
from pygaps.modelling import is_model_class
from pygaps.units.converter_mode import c_loading
from pygaps.units.converter_mode import c_material
from pygaps.units.converter_mode import c_pressure
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


class ModelIsotherm(BaseIsotherm):
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
    model : str or Model class
        The model to be used to describe the isotherm.
    param_guess : dict
        Starting guess for model parameters in the data fitting routine.
    param_bounds : dict
        Bounds for model parameters in the data fitting routine (applicable to some models).
    branch : ['ads', 'des'], optional
        The branch on which the model isotherm is based on. It is assumed to be the
        adsorption branch, as it is the most commonly modelled part, although may
        set to desorption as well.
    material : str
        Name of the material on which the isotherm is measured.
    adsorbate : str
        Isotherm adsorbate.
    temperature : float
        Isotherm temperature.

    Other Parameters
    ----------------
    optimization_params : dict
        Dictionary to be passed to the minimization function to use in fitting model to data.
        See `here
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html>`__.
    pressure_mode : str, optional
        The pressure mode, either 'absolute' pressure or 'relative'
        ('relative%') in the form of p/p0.
    pressure_unit : str, optional
        Unit of pressure, if applicable.
    loading_basis : str, optional
        Whether the adsorbed amount is in terms of either 'volume_gas'
        'volume_liquid', 'molar', 'mass', or a fraction/percent basis.
    loading_unit : str, optional
        Unit in which the loading basis is expressed.
    material_basis : str, optional
        Whether the underlying material is in terms of 'per volume'
        'per molar amount' or 'per mass' of material.
    material_unit : str, optional
        Unit in which the material basis is expressed.

    Notes
    -----
    Models supported are found in :mod:modelling. Here, :math:`L` is the
    adsorbate uptake and :math:`P` is pressure (fugacity technically).

    """

    _reserved_params = BaseIsotherm._reserved_params + [
        'model',
    ]

    ##########################################################
    #   Instantiation and classmethods

    def __init__(
        self,
        pressure: t.List[float] = None,
        loading: t.List[float] = None,
        isotherm_data: pandas.DataFrame = None,
        pressure_key: str = None,
        loading_key: str = None,
        branch: str = 'ads',
        model: t.Union[str, t.List[str], t.Any] = None,
        param_guess: dict = None,
        param_bounds: dict = None,
        optimization_params: dict = None,
        verbose: bool = False,
        **other_properties
    ):
        """
        Instantiation is done by passing the data to be fitted, model to be
        used and fitting method as well as the parameters required by parent
        class.
        """

        # Run base class constructor
        super().__init__(**other_properties)

        # Checks
        if model is None:
            raise ParameterError(
                "Specify a model to fit to the pure-component"
                " isotherm data. e.g. model=\"Langmuir\""
            )

        if isotherm_data is not None:
            if None in [pressure_key, loading_key]:
                raise ParameterError(
                    "Pass loading_key and pressure_key, the names of the loading and"
                    " pressure columns in the DataFrame, to the constructor."
                )

            data = isotherm_data.copy()
            # If branch column is already set
            if 'branch' not in isotherm_data.columns:
                data['branch'] = self._splitdata(data, pressure_key)

            if branch == 'ads':
                data = data.loc[data['branch'] == 0]
            elif branch == 'des':
                data = data.loc[data['branch'] == 1]
            else:
                raise ParameterError("ModelIsotherm branch must be singular: 'ads' or 'des'.")

            if data.empty:
                raise ParameterError("The required isotherm branch does not contain any points.")

            # Get just the pressure and loading columns
            pressure = data[pressure_key].values
            loading = data[loading_key].values

            process = True

        elif pressure is not None or loading is not None:
            if pressure is None or loading is None:
                raise ParameterError(
                    "If you've chosen to pass loading and pressure directly as"
                    " arrays, make sure both are specified!"
                )
            if len(pressure) != len(loading):
                raise ParameterError("Pressure and loading arrays are not equal!")

            # Ensure we are dealing with numpy arrays
            pressure = numpy.asarray(pressure)
            loading = numpy.asarray(loading)

            process = True

        elif is_model_class(model):
            self.model = model
            self.branch = branch

            process = False

        else:
            raise ParameterError(
                "Pass isotherm data to fit in a pandas.DataFrame as ``isotherm_data``"
                " or directly ``pressure`` and ``loading`` as arrays."
                "Alternatively, pass an isotherm model instance."
            )

        if process:

            # Branch the isotherm model is based on.
            self.branch = branch

            # Name of analytical model to fit to pure-component isotherm data
            # adsorption isotherm.
            self.model = get_isotherm_model(
                model,
                pressure_range=(min(pressure), max(pressure)),
                loading_range=(min(loading), max(loading)),
                param_bounds=param_bounds,
            )

            # Pass odd parameters
            self.model.__init_parameters__(other_properties)

            # Dictionary of parameters as a starting point for data fitting.
            if param_guess:
                for param in param_guess.keys():
                    if param not in self.model.param_names:
                        raise ParameterError(
                            f"'{param}' is not a valid parameter"
                            f" in the '{model}' model."
                        )
            else:
                param_guess = self.model.initial_guess(pressure, loading)

            # fit model to isotherm data
            self.model.fit(
                pressure,
                loading,
                param_guess,
                optimization_params,
                verbose,
            )

        # Plot fit if verbose
        if verbose and other_properties.pop('plot_fit', True):
            from pygaps.graphing.model_graphs import plot_model_guesses
            plot_model_guesses([self], pressure, loading)

    @classmethod
    def from_isotherm(
        cls,
        isotherm: BaseIsotherm,
        pressure: t.List[float] = None,
        loading: t.List[float] = None,
        isotherm_data: pandas.DataFrame = None,
        pressure_key: str = None,
        loading_key: str = None,
        branch: str = 'ads',
        model: t.Union[str, t.List[str], t.Any] = None,
        param_guess: dict = None,
        param_bounds: dict = None,
        optimization_params: dict = None,
        verbose: bool = False,
    ):
        """
        Construct a ModelIsotherm using a parent isotherm as the template for
        all the parameters.

        Parameters
        ----------

        isotherm : BaseIsotherm
            An instance of the BaseIsotherm parent class.
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
        branch : ['ads', 'des'], optional
            The branch on which the model isotherm is based on. It is assumed to be the
            adsorption branch, as it is the most commonly modelled.
        model : str
            The model to be used to describe the isotherm.
        param_guess : dict
            Starting guess for model parameters in the data fitting routine.
        param_bounds : dict
            Bounds for model parameters in the data fitting routine.
        optimization_params : dict
            Dictionary to be passed to the minimization function to use in fitting model to data.
            See `here
            <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
            Defaults to "Nelder-Mead".
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
        iso_params['param_bounds'] = param_bounds
        iso_params['optimization_params'] = optimization_params
        iso_params['branch'] = branch
        iso_params['verbose'] = verbose

        return cls(**iso_params)

    @classmethod
    def from_pointisotherm(
        cls,
        isotherm,
        branch: str = 'ads',
        model: t.Union[str, t.List[str], t.Any] = None,
        param_guess: dict = None,
        param_bounds: dict = None,
        optimization_params: dict = None,
        verbose: bool = False
    ):
        """
        Constructs a ModelIsotherm using data from a PointIsotherm and all its
        parameters.

        Parameters
        ----------
        isotherm : PointIsotherm
            An instance of the PointIsotherm parent class to model.
        branch : [None, 'ads', 'des'], optional
            Branch of isotherm to model. Defaults to adsorption branch.
        model : str, list, 'guess'
            The model to be used to describe the isotherm. Give a single model
            name (`"Langmuir"`) to fit it. Give a list of many model names to
            try them all and return the best fit (`[`Henry`, `Langmuir`]`).
            Specify `"guess"` to try all available models.
        param_guess : dict, optional
            Starting guess for model parameters in the data fitting routine.
        param_bounds : dict
            Bounds for model parameters in the data fitting routine.
        optimization_params : dict, optional
            Dictionary to be passed to the minimization function to use in fitting model to data.
            See `here
            <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
        verbose : bool
            Prints out extra information about steps taken.
        """
        if not model:
            raise ParameterError("Provide a model name (or a list of them) to fit.")
        # get isotherm parameters as a dictionary
        iso_params = isotherm.to_dict()
        iso_params['isotherm_data'] = isotherm.data(branch=branch)
        iso_params['pressure_key'] = isotherm.pressure_key
        iso_params['loading_key'] = isotherm.loading_key

        if isinstance(model, str):
            if model != 'guess':
                return cls(
                    branch=branch,
                    model=model,
                    param_guess=param_guess,
                    param_bounds=param_bounds,
                    optimization_params=optimization_params,
                    verbose=verbose,
                    **iso_params
                )

        return ModelIsotherm.guess(
            branch=branch,
            models=model,
            optimization_params=optimization_params,
            verbose=verbose,
            **iso_params
        )

    @classmethod
    def guess(
        cls,
        pressure: t.List[float] = None,
        loading: t.List[float] = None,
        isotherm_data: pandas.DataFrame = None,
        pressure_key: str = None,
        loading_key: str = None,
        branch: str = 'ads',
        models='guess',
        optimization_params: dict = None,
        param_bounds: dict = None,
        verbose: bool = False,
        **other_properties
    ):
        """
        Attempt to model the data using supplied list of model names,
        then return the one with the best RMS fit.

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
        models : 'guess', list of model names
            Attempt to guess which model best fits the isotherm data
            from the model name list supplied. If set to 'guess'
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
        other_properties:
            Any other parameters of the isotherm which should be stored internally.
        """
        attempts = []
        if models == 'guess':
            guess_models = _GUESS_MODELS
        else:
            try:
                guess_models = [m for m in models if is_model(m)]
            except TypeError as ex:
                raise ParameterError(
                    "Could not figure out the list of models. Is it a list?"
                ) from ex
            if len(guess_models) != len(models):
                raise ParameterError(
                    f'Not all models correspond to internal models. Possible models are f{models}'
                )

        for model in guess_models:
            if param_bounds is not None:
                params = get_isotherm_model(model).params.keys()
                param_bounds = {key: param_bounds[key] for key in param_bounds if key in params}
            try:
                isotherm = cls(
                    pressure=pressure,
                    loading=loading,
                    isotherm_data=isotherm_data,
                    pressure_key=pressure_key,
                    loading_key=loading_key,
                    model=model,
                    param_guess=None,
                    param_bounds=param_bounds,
                    optimization_params=optimization_params,
                    branch=branch,
                    verbose=verbose,
                    plot_fit=False,  # we don't want to plot at this stage
                    **other_properties
                )

                attempts.append(isotherm)

            except CalculationError as err:
                logger.info(f"Modelling using {model} failed.")
                if verbose:
                    logger.info(f"\n{err}")

        if not attempts:
            raise CalculationError("No model could be reliably fit on the isotherm.")

        errors = [x.model.rmse for x in attempts]
        best_fit = attempts[errors.index(min(errors))]

        if verbose:
            if loading is None:
                pressure = isotherm_data[pressure_key]
                loading = isotherm_data[loading_key]
            from pygaps.graphing.model_graphs import plot_model_guesses
            plot_model_guesses(attempts, pressure, loading)
            logger.info(f"Best model fit is {best_fit.model.name}.")

        return best_fit

    ###########################################################
    #   Info function

    def __str__(self) -> str:
        """Print a short summary of all the isotherm parameters."""
        return super().__str__() + self.model.__str__()

    def print_info(self, **plot_iso_args):
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
        return self.plot(**plot_iso_args)

    def plot(self, **plot_iso_args):
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
        plot_dict = {
            "material_basis": self.material_basis,
            "material_unit": self.material_unit,
            "loading_basis": self.loading_basis,
            "loading_unit": self.loading_unit,
            "pressure_unit": self.pressure_unit,
            "pressure_mode": self.pressure_mode,
        }
        plot_dict.update(plot_iso_args)

        from pygaps.graphing.isotherm_graphs import plot_iso
        return plot_iso(self, **plot_dict)

    ##########################################################
    #   Methods

    def has_branch(self, branch: str) -> bool:
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
        return self.branch == branch

    def pressure(
        self,
        points: int = 60,
        branch: str = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
        limits: t.Tuple[float, float] = None,
        indexed: bool = False
    ):
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
        pressure_mode : {None, 'absolute', 'relative', 'relative%'}
            The mode in which to return the pressure, if possible. If ``None``,
            returns mode the isotherm is currently in.
        limits : [float, float], optional
            Minimum and maximum pressure limits.
            Put None or -+np.inf for no limit.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series with the columns requested instead of an array.

        Returns
        -------
        numpy.array or pandas.Series
            Pressure points in the model pressure range.

        """
        if branch and branch not in [self.branch, 'all']:
            raise ParameterError(
                f"ModelIsotherm is based on an '{self.branch}' branch "
                f"(while parameter supplied was '{branch}')."
            )
        # TODO: to calculate limits like this, better to put the limits directly to evaluate
        # Generate pressure points
        if self.model.calculates == 'loading':
            ret = numpy.linspace(
                self.model.pressure_range[0],
                self.model.pressure_range[1],
                points,
            )

            # Convert if needed
            if pressure_mode or pressure_unit:
                if not pressure_mode:
                    pressure_mode = self.pressure_mode
                if not pressure_unit:
                    pressure_unit = self.pressure_unit

                ret = c_pressure(
                    ret,
                    mode_from=self.pressure_mode,
                    mode_to=pressure_mode,
                    unit_from=self.pressure_unit,
                    unit_to=pressure_unit,
                    adsorbate=self.adsorbate,
                    temp=self.temperature
                )
        elif self.model.calculates == 'pressure':
            ret = self.pressure_at(
                self.loading(points),
                pressure_mode=pressure_mode,
                pressure_unit=pressure_unit,
            )

        # Select required points
        if limits and any(limits):
            ret = ret[((-numpy.inf if limits[0] is None else limits[0]) < ret)
                      & (ret < (numpy.inf if limits[1] is None else limits[1]))]

        if indexed:
            return pandas.Series(ret)
        return ret

    def loading(
        self,
        points: int = 60,
        branch: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
        limits: t.Tuple[float, float] = None,
        indexed: bool = False
    ):
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
        loading_basis : {None, 'mass', 'volume_gas', 'volume_liquid'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        material_unit : str, optional
            Unit in which the material should be returned. If None
            it defaults to which loading unit the isotherm is currently in.
        material_basis : {None, 'mass', 'volume'}
            The basis on which to return the material, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        limits : [float, float], optional
            Minimum and maximum loading limits.
            Put None or -+np.inf for no limit.
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
                f"ModelIsotherm is based on an '{self.branch}' branch "
                f"(while parameter supplied was '{branch}')."
            )

        if self.model.calculates == 'pressure':
            ret = numpy.linspace(
                self.model.loading_range[0],
                self.model.loading_range[1],
                points,
            )

            # Convert if needed
            # First material is converted
            if material_basis or material_unit:
                if not material_basis:
                    material_basis = self.material_basis

                ret = c_material(
                    ret,
                    basis_from=self.material_basis,
                    basis_to=material_basis,
                    unit_from=self.material_unit,
                    unit_to=material_unit,
                    material=self.material
                )

            if loading_basis or loading_unit:
                if not loading_basis:
                    loading_basis = self.loading_basis

                # These must be specified
                # in the case of fractional conversions
                if not material_basis:
                    material_basis = self.material_basis
                if not material_unit:
                    material_unit = self.material_unit

                ret = c_loading(
                    ret,
                    basis_from=self.loading_basis,
                    basis_to=loading_basis,
                    unit_from=self.loading_unit,
                    unit_to=loading_unit,
                    adsorbate=self.adsorbate,
                    temp=self.temperature,
                    basis_material=material_basis,
                    unit_material=material_unit,
                )
        else:
            ret = self.loading_at(
                self.pressure(points),
                loading_unit=loading_unit,
                loading_basis=loading_basis,
                material_unit=material_unit,
                material_basis=material_basis,
            )

        # Select required points
        if limits and any(limits):
            ret = ret[((-numpy.inf if limits[0] is None else limits[0]) < ret)
                      & (ret < (numpy.inf if limits[1] is None else limits[1]))]

        if indexed:
            return pandas.Series(ret)
        return ret

    @property
    def other_keys(self):
        """
        Return column names of any supplementary data points.
        """
        return []

    ##########################################################
    #   Functions that calculate values of the isotherm data

    def pressure_at(
        self,
        loading: t.Union[float, t.List[float]],
        branch: str = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
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
        loading_basis : {None, 'mass', 'volume_gas', 'volume_liquid'}
            The basis the loading is specified in. If ``None``,
            assumes the basis the isotherm is currently in.
        material_unit : str, optional
            Unit in which the material is passed in. If None
            it defaults to which loading unit the isotherm is currently in
        material_basis : str
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
                f"ModelIsotherm is based on an '{self.branch}' branch "
                f"(while parameter supplied was '{branch}')."
            )

        # Convert to numpy array just in case
        loading = numpy.asarray(loading)

        # Ensure loading is in correct units and basis for the internal model
        if material_basis or material_unit:
            if not material_basis:
                material_basis = self.material_basis
            if not material_unit:
                raise ParameterError(
                    "Must specify a material unit if the input"
                    " is in another basis"
                )

            loading = c_material(
                loading,
                basis_from=material_basis,
                basis_to=self.material_basis,
                unit_from=material_unit,
                unit_to=self.material_unit,
                material=self.material
            )

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.loading_basis
            if not loading_unit:
                raise ParameterError(
                    "Must specify a loading unit if the input"
                    " is in another basis"
                )

            loading = c_loading(
                loading,
                basis_from=loading_basis,
                basis_to=self.loading_basis,
                unit_from=loading_unit,
                unit_to=self.loading_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature,
                basis_material=material_basis,
                unit_material=material_unit,
            )

        # Calculate pressure using internal model
        pressure = self.model.pressure(loading)

        # Ensure pressure is in correct units and mode requested
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if not pressure_unit:
                pressure_unit = self.pressure_unit

            pressure = c_pressure(
                pressure,
                mode_from=self.pressure_mode,
                mode_to=pressure_mode,
                unit_from=self.pressure_unit,
                unit_to=pressure_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature
            )

        return pressure

    def loading_at(
        self,
        pressure: t.Union[float, t.List[float]],
        branch: str = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
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
        loading_basis : {None, 'mass',  'volume_gas', 'volume_liquid'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        material_unit : str, optional
            Unit in which the material should be returned. If None
            it defaults to which loading unit the isotherm is currently in.
        material_basis : {None, 'mass', 'volume'}
            The basis on which to return the material, if possible. If ``None``,
            returns on the basis the isotherm is currently in.

        Returns
        -------
        float or array
            Predicted loading at pressure P using fitted model
            parameters.

        """
        if branch and branch != self.branch:
            raise ParameterError(
                f"ModelIsotherm is based on an '{self.branch}' branch "
                f"(while parameter supplied was '{branch}')."
            )

        # Convert to numpy array just in case
        pressure = numpy.asarray(pressure)

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if pressure_mode == 'absolute' and not pressure_unit:
                raise ParameterError(
                    "Must specify a pressure unit if the input"
                    " is in an absolute mode"
                )

            pressure = c_pressure(
                pressure,
                mode_from=pressure_mode,
                mode_to=self.pressure_mode,
                unit_from=pressure_unit,
                unit_to=self.pressure_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature
            )

        # Calculate loading using internal model
        loading = self.model.loading(pressure)

        # Ensure loading is in correct units and basis requested
        # First adsorbent is converted
        if material_basis or material_unit:
            if not material_basis:
                material_basis = self.material_basis

            loading = c_material(
                loading,
                basis_from=self.material_basis,
                basis_to=material_basis,
                unit_from=self.material_unit,
                unit_to=material_unit,
                material=self.material
            )

        # Then loading
        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.loading_basis

            # These must be specified
            # in the case of fractional conversions
            if not material_basis:
                material_basis = self.material_basis
            if not material_unit:
                material_unit = self.material_unit

            loading = c_loading(
                loading,
                basis_from=self.loading_basis,
                basis_to=loading_basis,
                unit_from=self.loading_unit,
                unit_to=loading_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature,
                basis_material=material_basis,
                unit_material=material_unit,
            )

        return loading

    def spreading_pressure_at(
        self,
        pressure: t.Union[float, t.List[float]],
        branch: str = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
    ):
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
                f"ModelIsotherm is based on an '{self.branch}' branch "
                f"(while parameter supplied was '{branch}')."
            )

        # Convert to numpy array just in case
        pressure = numpy.asarray(pressure)

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if not pressure_unit:
                pressure_unit = self.pressure_unit
            if not pressure_unit and self.pressure_mode.startswith('relative'):
                raise ParameterError(
                    "Must specify a pressure unit if the input"
                    " is in an absolute mode"
                )

            pressure = c_pressure(
                pressure,
                mode_from=pressure_mode,
                mode_to=self.pressure_mode,
                unit_from=pressure_unit,
                unit_to=self.pressure_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature
            )

        # calculate based on model
        return self.model.spreading_pressure(pressure)

    def toth_correction_at(
        self,
        pressure: t.Union[float, t.List[float]],
    ):
        """
        Calculate the Toth correction factor at a given pressure.
        Parameters:
        -----------
        pressure : float
            The pressure at which to calculate the Toth correction factor.
        Returns:
        --------
        float
            The Toth correction factor at the given pressure.
        """

        return self.model.toth_correction(pressure)
