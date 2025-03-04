"""
This module contains the main class that describes an isotherm through discrete points.
"""

import textwrap
import typing as t

import numpy
import pandas

from pygaps import logger
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.units.converter_mode import c_loading
from pygaps.units.converter_mode import c_material
from pygaps.units.converter_mode import c_pressure
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import pgError
from pygaps.utilities.isotherm_interpolator import IsothermInterpolator


class PointIsotherm(BaseIsotherm):
    """
    Class which contains the points from an adsorption isotherm.

    This class is designed to be a complete description of a discrete isotherm.
    It extends the BaseIsotherm class, which contains all the description of the
    isotherm parameters, but also holds the datapoints recorded during an
    experiment or simulation.

    The minimum arguments required to instantiate the class, besides those
    required for the parent BaseIsotherm, is the actual data, specified either
    as `pressure` + `loading` arrays or as `isotherm_data` (a
    `pandas.DataFrame`) + keys for the columns of the dataframe which have the
    loading and the pressure data.

    Parameters
    ----------
    pressure : list
        Create an isotherm directly from an array. Values for pressure.
        If the ``isotherm_data`` dataframe is specified, these values are ignored.
    loading : list
        Create an isotherm directly from an array. Values for loading.
        If the ``isotherm_data`` dataframe is specified, these values are ignored.
    isotherm_data : `pandas.DataFrame`
        Pure-component adsorption isotherm data.
    pressure_key : str
        The title of the pressure data in the DataFrame provided.
    loading_key : str
        The title of the loading data in the DataFrame provided.
    branch : ['guess', ads', 'des', iterable], optional
        The branch of the isotherm. The code will automatically attempt to
        guess if there's an adsorption and desorption branch.
        The user can instead tell the framework that all points are
        part of an adsorption ('ads') or desorption ('des') curve.
        Alternatively, an iterable can be passed which contains
        detailed info for each data point if adsorption points ('False')
        or desorption points ('True'). eg: [False, False, True, True...]
        or as a column of the isotherm_data.
    material : str
        Name of the material on which the isotherm is measured.
    adsorbate : str
        Isotherm adsorbate.
    temperature : float
        Isotherm temperature.

    Other Parameters
    ----------------
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
    This class assumes that the datapoints do not contain noise.
    Detection of adsorption/desorption branches will not work if
    data is noisy.

    """

    _reserved_params = BaseIsotherm._reserved_params + [
        'data_raw',
        'l_interpolator',
        'p_interpolator',
        'loading_key',
        'pressure_key',
        'other_keys',
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
        branch: t.Union[str, t.List[bool]] = 'guess',
        **other_properties
    ):
        """
        Instantiation is done by passing the discrete data as a pandas
        DataFrame, the column keys as string as well as the parameters
        required by parent class.
        """
        # Run base class constructor
        super().__init__(**other_properties)

        # Checks
        if isotherm_data is not None:
            if None in [pressure_key, loading_key]:
                raise ParameterError(
                    "Pass loading_key and pressure_key, the names of the loading and"
                    " pressure columns in the DataFrame, to the constructor."
                )

            # Save column names
            # Name of column in the dataframe that contains adsorbed amount.
            self.loading_key = loading_key

            # Name of column in the dataframe that contains pressure.
            self.pressure_key = pressure_key

            # Pandas DataFrame that stores the data.
            columns = [self.pressure_key, self.loading_key]
            if not all(a in isotherm_data.columns for a in columns):
                raise ParameterError(
                    "Could not find columns "
                    f"({[a for a in columns if a not in isotherm_data.columns]})"
                    " in the adsorption DataFrame."
                )
            if 'branch' not in isotherm_data.columns:
                columns.append('branch')
            other_keys = [c for c in isotherm_data.columns if c not in columns]
            columns = columns + sorted(other_keys)
            self.data_raw = isotherm_data.reindex(columns=columns)

        elif pressure is not None or loading is not None:
            if pressure is None or loading is None:
                raise ParameterError(
                    "If you've chosen to pass loading and pressure directly as"
                    " arrays, make sure both are specified!"
                )
            if len(pressure) != len(loading):
                raise ParameterError("Pressure and loading arrays are not equal!")

            # Standard column names
            self.pressure_key = 'pressure'
            self.loading_key = 'loading'

            # DataFrame creation
            self.data_raw = pandas.DataFrame({
                self.pressure_key: pressure,
                self.loading_key: loading
            })
        else:
            raise ParameterError(
                "Pass either the isotherm data in a pandas.DataFrame as ``isotherm_data``"
                " or directly ``pressure`` and ``loading`` as arrays."
            )

        # Deal with the isotherm branches
        if isotherm_data is not None and 'branch' in isotherm_data.columns:
            pass
        elif isinstance(branch, str):
            if branch == 'guess':
                # Split the data in adsorption/desorption
                self.data_raw['branch'] = self._splitdata(self.data_raw, self.pressure_key)
            elif branch == 'ads':
                self.data_raw['branch'] = 0
            elif branch == 'des':
                self.data_raw['branch'] = 1
            else:
                raise ParameterError(
                    "Isotherm branch parameter must be 'guess ,'ads' or 'des'"
                    " or an array of booleans."
                )
        else:
            try:
                self.data_raw['branch'] = branch
            except Exception as e_info:
                raise ParameterError(e_info)

        # The internal interpolator for loading given pressure.
        self.l_interpolator = None

        # The internal interpolator for pressure given loading.
        self.p_interpolator = None

    @classmethod
    def from_isotherm(
        cls,
        isotherm: BaseIsotherm,
        pressure: t.List[float] = None,
        loading: t.List[float] = None,
        isotherm_data: pandas.DataFrame = None,
        pressure_key: str = None,
        loading_key: str = None,
    ):
        """
        Construct a point isotherm using a parent isotherm as the template for
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
        isotherm_data : pandas.DataFrame
            Pure-component adsorption isotherm data.
        loading_key : str
            Column of the pandas DataFrame where the loading is stored.
        pressure_key : str
            Column of the pandas DataFrame where the pressure is stored.
        """
        # get isotherm parameters as a dictionary
        iso_params = isotherm.to_dict()
        # add pointisotherm values to dict
        iso_params['pressure'] = pressure
        iso_params['loading'] = loading
        iso_params['isotherm_data'] = isotherm_data
        iso_params['pressure_key'] = pressure_key
        iso_params['loading_key'] = loading_key

        return cls(**iso_params)

    @classmethod
    def from_modelisotherm(
        cls,
        modelisotherm,
        pressure_points: t.List[float] = None,
        loading_points: t.List[float] = None,
    ):
        """
        Construct a PointIsotherm from a ModelIsothem class.

        This class method allows for the model to be converted into
        a list of points calculated by using the model in the isotherm.

        Parameters
        ----------
        modelisotherm : ModelIsotherm
            The isotherm containing the model.
        pressure_points : None or List or PointIsotherm
            How the pressure points should be chosen for the resulting PointIsotherm.

            - If ``None``, the PointIsotherm returned has a fixed number of
              equidistant points
            - If an array, the PointIsotherm returned has points at each of the
              values of the array
            - If a PointIsotherm is passed, the values will be calculated at
              each of the pressure points in the passed isotherm. This is useful
              for comparing a model overlap with the real isotherm.
        """
        if pressure_points is not None and loading_points is not None:
            raise ParameterError("""Cannot specify both pressure and loading points.""")

        pressure = None
        loading = None
        if modelisotherm.model.calculates == "loading":
            # The user may request loading even if the model calculates pressure
            if loading_points is None:
                if pressure_points is None:
                    pressure = modelisotherm.pressure()
                elif isinstance(pressure_points, PointIsotherm):
                    pressure = pressure_points.pressure(branch=modelisotherm.branch)
                else:
                    pressure = pressure_points
                loading = modelisotherm.loading_at(pressure)
            else:
                loading = loading_points
                pressure = modelisotherm.pressure_at(loading_points)
        elif modelisotherm.model.calculates == "pressure":
            # The user may request pressure even if the model calculates loading
            if pressure_points is None:
                if loading_points is None:
                    loading = modelisotherm.loading()
                elif isinstance(loading_points, PointIsotherm):
                    loading = loading_points.loading(branch=modelisotherm.branch)
                else:
                    loading = loading_points
                pressure = modelisotherm.pressure_at(loading)
            else:
                pressure = pressure_points
                loading = modelisotherm.loading_at(pressure)

        return PointIsotherm(
            pressure=pressure,
            loading=loading,
            model_from=modelisotherm.model.name,
            **modelisotherm.to_dict()
        )

    ##########################################################
    #   Conversion functions

    def convert(
        self,
        pressure_mode: str = None,
        pressure_unit: str = None,
        loading_basis: str = None,
        loading_unit: str = None,
        material_basis: str = None,
        material_unit: str = None,
        verbose: bool = False,
    ):
        """
        Convenience function for permanently converting any isotherm
        mode/basis/units.

        Parameters
        ----------
        pressure_mode : {'absolute', 'relative', 'relative%'}
            The mode in which the isotherm should be converted.
        pressure_unit : str
            The unit into which the internal pressure should be converted to.
            Only makes sense if converting to absolute pressure.
        loading_basis : {'mass', 'molar', 'volume_gas', 'volume_liquid', 'percent', 'fraction'}
            The basis in which the isotherm should be converted.
        loading_unit : str
            The unit into which the internal loading should be converted to.
        material_basis : {'mass', 'molar', 'volume'}
            The basis in which the isotherm should be converted.
        material_unit : str
            The unit into which the material should be converted to.
        verbose : bool
            Print out steps taken.

        """
        if pressure_mode or pressure_unit:
            self.convert_pressure(
                mode_to=pressure_mode,
                unit_to=pressure_unit,
                verbose=verbose,
            )

        if material_basis or material_unit:
            self.convert_material(
                basis_to=material_basis,
                unit_to=material_unit,
                verbose=verbose,
            )

        if loading_basis or loading_unit:
            self.convert_loading(
                basis_to=loading_basis,
                unit_to=loading_unit,
                verbose=verbose,
            )

    def convert_pressure(
        self,
        mode_to: str = None,
        unit_to: str = None,
        verbose: bool = False,
        pseudo: bool = False,
    ):
        """
        Convert isotherm pressure from one unit to another
        and the pressure mode from absolute to relative.

        Only applicable in the case of isotherms taken below critical
        point of adsorbate.

        Parameters
        ----------
        mode_to : {'absolute', 'relative', 'relative%'}
            The mode in which the isotherm should be converted.
        unit_to : str
            The unit into which the internal pressure should be converted to.
            Only makes sense if converting to absolute pressure.
        verbose : bool
            Print out steps taken.
        pseudo: bool, optional
            Whether to use a pseudo-saturation pressure, in the case that the
            adsorbate is supercritical

        """
        if not mode_to:
            mode_to = self.pressure_mode

        if mode_to == self.pressure_mode and unit_to == self.pressure_unit:
            if verbose:
                logger.info("Mode and units are the same, no changes made.")
            return

        try:
            self.data_raw[self.pressure_key] = c_pressure(
                self.data_raw[self.pressure_key],
                mode_from=self.pressure_mode,
                mode_to=mode_to,
                unit_from=self.pressure_unit,
                unit_to=unit_to,
                adsorbate=self.adsorbate,
                temp=self.temperature,
                pseudo=pseudo,
            )
        except pgError as err:
            raise CalculationError(
                f"The isotherm cannot be converted to a {mode_to} basis ({unit_to}). "
                "Is your isotherm supercritical? "
                "Does the adsorbate have a thermodynamical backend?"
            ) from err

        if mode_to != self.pressure_mode:
            self.pressure_mode = mode_to
        if unit_to != self.pressure_unit and mode_to == 'absolute':
            self.pressure_unit = unit_to
        else:
            self.pressure_unit = None

        # Reset interpolators
        self.l_interpolator = None
        self.p_interpolator = None

        if verbose:
            logger.info(f"Changed pressure to mode '{mode_to}', unit '{unit_to}'.")

    def convert_loading(
        self,
        basis_to: str = None,
        unit_to: str = None,
        verbose: bool = False,
    ):
        """
        Convert isotherm loading from one unit to another
        and the basis of the isotherm loading to be
        either 'mass', 'molar' or 'percent'/'fraction'.

        Parameters
        ----------
        basis_to : {'mass', 'molar', 'volume_gas', 'volume_liquid', 'percent', 'fraction'}
            The basis in which the isotherm should be converted.
        unit_to : str
            The unit into which the internal loading should be converted to.
        verbose : bool
            Print out steps taken.

        """
        if not basis_to:
            basis_to = self.loading_basis

        if basis_to == self.loading_basis and unit_to == self.loading_unit:
            if verbose:
                logger.info("Basis and units are the same, no changes made.")
            return

        if self.loading_basis in ['percent', 'fraction']:
            # TODO this is
            if basis_to == self.loading_basis and unit_to != self.loading_unit:
                if verbose:
                    logger.info("There are no loading units in this mode.")
                return

        self.data_raw[self.loading_key] = c_loading(
            self.data_raw[self.loading_key],
            basis_from=self.loading_basis,
            basis_to=basis_to,
            unit_from=self.loading_unit,
            unit_to=unit_to,
            adsorbate=self.adsorbate,
            temp=self.temperature,
            basis_material=self.material_basis,
            unit_material=self.material_unit,
        )

        if basis_to != self.loading_basis:
            self.loading_basis = basis_to
        if basis_to in ['percent', 'fraction']:
            self.loading_unit = None
        else:
            self.loading_unit = unit_to

        # Reset interpolators
        self.l_interpolator = None
        self.p_interpolator = None

        if verbose:
            logger.info(f"Changed loading to basis '{basis_to}', unit '{unit_to}'.")

    def convert_material(
        self,
        basis_to: str = None,
        unit_to: str = None,
        verbose: bool = False,
    ):
        """
        Convert the material of the isotherm from one unit to another and the
        basis of the isotherm loading to be either 'per mass' or 'per volume' or
        'per mole' of material.

        Only applicable to materials that have been loaded in memory with a
        'density' or 'molar mass' property respectively.

        Parameters
        ----------
        basis : {'mass', 'molar', 'volume'}
            The basis in which the isotherm should be converted.
        unit_to : str
            The unit into which the material should be converted to.
        verbose : bool
            Print out steps taken.

        """
        if not basis_to:
            basis_to = self.material_basis

        if basis_to == self.material_basis and unit_to == self.material_unit:
            if verbose:
                logger.info("Basis and units are the same, no changes made.")
            return

        if (
            self.loading_basis in ['percent', 'fraction'] and basis_to == self.material_basis
            and unit_to != self.material_unit
        ):
            # We "virtually" change the unit without any conversion
            self.material_unit = unit_to
            if verbose:
                logger.info("There are no material units in this mode.")
            return

        self.data_raw[self.loading_key] = c_material(
            self.data_raw[self.loading_key],
            basis_from=self.material_basis,
            basis_to=basis_to,
            unit_from=self.material_unit,
            unit_to=unit_to,
            material=self.material
        )

        # A special case is when conversion is performed from
        # a "fraction" basis to another "fraction" basis.
        # Here, the loading must be simultaneously converted.
        # e.g.: wt% = g/g -> cm3/cm3 = vol%
        if self.loading_basis in ['percent', 'fraction']:
            if basis_to == 'volume':
                _basis_to = 'volume_liquid'
            else:
                _basis_to = basis_to
            if self.material_basis == 'volume':
                _basis_from = 'volume_liquid'
            else:
                _basis_from = self.material_basis
            self.data_raw[self.loading_key] = c_loading(
                self.data_raw[self.loading_key],
                basis_from=_basis_from,
                basis_to=_basis_to,
                unit_from=self.material_unit,
                unit_to=unit_to,
                adsorbate=self.adsorbate,
                temp=self.temperature,
            )
            if verbose:
                logger.info(f"Changed loading to basis '{basis_to}', unit '{unit_to}'.")

        if unit_to != self.material_unit:
            self.material_unit = unit_to
        if basis_to != self.material_basis:
            self.material_basis = basis_to

        # Reset interpolators
        self.l_interpolator = None
        self.p_interpolator = None

        if verbose:
            logger.info(f"Changed material to basis '{basis_to}', unit '{unit_to}'.")

    ###########################################################
    #   Info functions

    def print_info(self, **plot_iso_args):
        """
        Print a short summary of all the isotherm parameters and a graph.

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
            "y2_data": self.other_keys[0] if self.other_keys else None,
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
    #   Functions that return part of the isotherm data

    def data(self, branch: str = None) -> pandas.DataFrame:
        """
        Return underlying isotherm data.

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the isotherm to return. If ``None``, returns entire
            dataset.

        Returns
        -------
        DataFrame
            The pandas DataFrame containing all isotherm data.

        """
        if branch is None or branch.startswith('all'):
            return self.data_raw
        if branch == 'ads':
            return self.data_raw.loc[self.data_raw['branch'] == 0]
        if branch == 'des':
            return self.data_raw.loc[self.data_raw['branch'] == 1]
        raise ParameterError('Bad branch specification.')

    def pressure(
        self,
        branch: str = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
        limits: t.Tuple[float, float] = None,
        indexed: bool = False,
    ) -> t.Union[numpy.ndarray, pandas.Series]:
        """
        Return pressure points as an array.

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the pressure to return. If ``None``, returns entire
            dataset.
        pressure_unit : str, optional
            Unit in which the pressure should be returned. If ``None``
            it defaults to which pressure unit the isotherm is currently in.
        pressure_mode : {None, 'absolute', 'relative', 'relative%'}
            The mode in which to return the pressure, if possible. If ``None``,
            returns mode the isotherm is currently in.
        limits : [float, float], optional
            Minimum and maximum pressure limits.
            Put None or -+np.inf for no limit.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series instead of an array.

        Returns
        -------
        array or Series
            The pressure slice corresponding to the parameters passed.

        """
        ret = self.data(branch=branch).loc[:, self.pressure_key]

        if not ret.empty:
            # Convert if needed
            if pressure_mode or pressure_unit:
                # If pressure mode not given, try current
                if not pressure_mode:
                    pressure_mode = self.pressure_mode
                # If pressure unit not given, try current
                if not pressure_unit:
                    pressure_unit = self.pressure_unit

                try:
                    ret = c_pressure(
                        ret,
                        mode_from=self.pressure_mode,
                        mode_to=pressure_mode,
                        unit_from=self.pressure_unit,
                        unit_to=pressure_unit,
                        adsorbate=self.adsorbate,
                        temp=self.temperature
                    )
                except pgError as err:
                    raise CalculationError(
                        f"The pressure cannot be read in a {pressure_mode} basis ({pressure_unit}). "
                        "Is your isotherm supercritical? "
                        "Does the adsorbate have a thermodynamical backend?"
                    ) from err

            # Select required points
            if limits and any(limits):
                ret = ret.loc[ret.between(
                    -numpy.inf if limits[0] is None else limits[0],
                    numpy.inf if limits[1] is None else limits[1]
                )]

        if indexed:
            return ret
        return ret.values

    def loading(
        self,
        branch: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
        limits: t.Tuple[float, float] = None,
        indexed: bool = False
    ) -> t.Union[numpy.ndarray, pandas.Series]:
        """
        Return loading points as an array.

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the loading to return. If ``None``, returns entire
            dataset.
        loading_unit : str, optional
            Unit in which the loading should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        loading_basis : {None, 'mass', 'volume_gas', 'volume_liquid', 'molar'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        material_unit : str, optional
            Unit in which the material should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        material_basis : {None, 'mass', 'volume', 'molar'}
            The basis on which to return the material, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        limits : [float, float], optional
            Minimum and maximum loading limits.
            Put None or -+np.inf for no limit.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series instead of an array.

        Returns
        -------
        Array or Series
            The loading slice corresponding to the parameters passed.

        """
        ret = self.data(branch=branch).loc[:, self.loading_key]

        if not ret.empty:
            # Convert if needed

            # First adsorbent is converted
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

            # Select required points
            if limits and any(limits):
                ret = ret.loc[ret.between(
                    -numpy.inf if limits[0] is None else limits[0],
                    numpy.inf if limits[1] is None else limits[1]
                )]

        if indexed:
            return ret
        return ret.values

    @property
    def other_keys(self):
        """
        Return column names of any supplementary data points.
        """
        return [
            c for c in self.data_raw.columns
            if c not in (self.pressure_key, self.loading_key, 'branch')
        ]

    def other_data(
        self,
        key: str,
        branch: str = None,
        limits: t.Tuple[float, float] = None,
        indexed: bool = False,
    ) -> t.Union[numpy.ndarray, pandas.Series]:
        """
        Return supplementary data points as an array.

        Parameters
        ----------
        key : str
            Key in the isotherm DataFrame containing the data to select.
        branch : {None, 'ads', 'des'}
            The branch of the data to return. If ``None``, returns entire
            dataset.
        limits : [float, float], optional
            Minimum and maximum data limits.
            Put None or -+np.inf for no limit.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series instead of an array.

        Returns
        -------
        array or Series
            The data slice corresponding to the parameters passed.

        """
        if key in self.other_keys:
            ret = self.data(branch=branch).loc[:, key]

            if not ret.empty:
                # Select required points
                if limits and any(limits):
                    ret = ret.loc[ret.between(
                        -numpy.inf if limits[0] is None else limits[0],
                        numpy.inf if limits[1] is None else limits[1]
                    )]

            if indexed:
                return ret
            return ret.values

        raise ParameterError(f"Isotherm does not contain any {key} data.")

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
        return not self.data(branch=branch).empty

    ##########################################################
    #   Functions that interpolate values of the isotherm data

    def pressure_at(
        self,
        loading: t.List[float],
        branch: str = 'ads',
        interpolation_type: str = 'linear',
        interp_fill: t.Union[float, t.Tuple[float, float], str] = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
    ) -> numpy.ndarray:
        """
        Interpolate isotherm to compute pressure at any loading given.

        Parameters
        ----------
        loading : float
            Loading at which to compute pressure.
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.
        interpolation_type : str
            The type of scipy.interp1d used: `linear`, `nearest`, `zero`,
            `slinear`, `quadratic`, `cubic`. It defaults to `linear`.
        interp_fill : array-like or (array-like, array_like) or “extrapolate”, optional
            Parameter to determine what to do outside data bounds.
            Passed to the scipy.interpolate.interp1d function as ``fill_value``.
            If blank, interpolation will not predict outside the bounds of data.

        pressure_unit : str
            Unit the pressure is returned in. If ``None``, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is returned in. If ``None``, it defaults to
            internal isotherm mode.

        loading_unit : str
            Unit the loading is specified in. If ``None``, it defaults to
            internal isotherm units.
        loading_basis : {None, 'mass', 'molar', 'volume_gas', 'volume_liquid'}
            The basis the loading is specified in. If ``None``,
            assumes the basis the isotherm is currently in.
        material_unit : str, optional
            Unit in which the material is passed in. If ``None``
            it defaults to which loading unit the isotherm is currently in
        material_basis : str
            The basis the loading is passed in. If ``None``, it defaults to
            internal isotherm basis.

        Returns
        -------
        float
            Predicted pressure at loading specified.

        """
        # Convert to numpy array just in case
        loading = numpy.asarray(loading)

        # Check if interpolator is applicable
        if (
            self.p_interpolator is None or self.p_interpolator.interp_branch != branch
            or self.p_interpolator.interp_kind != interpolation_type
            or self.p_interpolator.interp_fill != interp_fill
        ):
            self.p_interpolator = IsothermInterpolator(
                self.loading(branch=branch),
                self.pressure(branch=branch),
                interp_branch=branch,
                interp_kind=interpolation_type,
                interp_fill=interp_fill
            )

        # Ensure loading is in correct units and basis for the internal model
        if material_basis or material_unit:
            if not material_basis:
                material_basis = self.material_basis
            if not material_unit:
                raise ParameterError(
                    "Must specify an material unit if the input is in another basis."
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
                    "Must specify a loading unit if the input is in another basis."
                )

            loading = c_loading(
                loading,
                basis_from=loading_basis,
                basis_to=self.loading_basis,
                unit_from=loading_unit,
                unit_to=self.loading_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature,
                basis_material=self.material_basis,
                unit_material=self.material_unit,
            )

        # Interpolate using the internal interpolator
        pressure = self.p_interpolator(loading)

        # Ensure pressure is in correct units and mode requested
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode

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
        pressure: t.List[float],
        branch: str = 'ads',
        interpolation_type: str = 'linear',
        interp_fill: t.Union[float, t.Tuple[float, float], str] = None,
        pressure_unit: str = None,
        pressure_mode: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
    ) -> numpy.ndarray:
        """
        Interpolate isotherm to compute loading at any pressure given.

        Parameters
        ----------
        pressure : float or array
            Pressure at which to compute loading.
        branch : {'ads', 'des'}
            The branch the interpolation takes into account.
        interpolation_type : str
            The type of scipy.interp1d used: `linear`, `nearest`, `zero`,
            `slinear`, `quadratic`, `cubic`. It defaults to `linear`.
        interp_fill : array-like or (array-like, array_like) or “extrapolate”, optional
            Parameter to determine what to do outside data bounds.
            Passed to the scipy.interpolate.interp1d function as ``fill_value``.
            If blank, interpolation will not predict outside the bounds of data.

        pressure_unit : str
            Unit the pressure is specified in. If ``None``, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is passed in. If ``None``, it defaults to
            internal isotherm mode.

        loading_unit : str, optional
            Unit in which the loading should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        loading_basis : {None, 'mass', 'molar', 'volume_gas', 'volume_liquid'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        material_unit : str, optional
            Material unit in which the data should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        material_basis : {None, 'mass', 'volume', 'molar'}
            Material basis on which to return the data, if possible. If ``None``,
            returns on the basis the isotherm is currently in.

        Returns
        -------
        float or array
            Predicted loading at pressure P.

        """
        # Convert to a numpy array just in case
        pressure = numpy.asarray(pressure)

        # Check if interpolator is applicable
        if (
            self.l_interpolator is None or self.l_interpolator.interp_branch != branch
            or self.l_interpolator.interp_kind != interpolation_type
            or self.l_interpolator.interp_fill != interp_fill
        ):
            self.l_interpolator = IsothermInterpolator(
                self.pressure(branch=branch),
                self.loading(branch=branch),
                interp_branch=branch,
                interp_kind=interpolation_type,
                interp_fill=interp_fill
            )

        # Ensure pressure is in correct units and mode for the internal model
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.pressure_mode
            if pressure_mode == 'absolute' and not pressure_unit:
                raise ParameterError(
                    "Must specify a pressure unit if the input is in an absolute mode."
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

        # Interpolate using the internal interpolator
        loading = self.l_interpolator(pressure)

        # Ensure loading is in correct units and basis requested
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

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.loading_basis

            loading = c_loading(
                loading,
                basis_from=self.loading_basis,
                basis_to=loading_basis,
                unit_from=self.loading_unit,
                unit_to=loading_unit,
                adsorbate=self.adsorbate,
                temp=self.temperature,
                basis_material=self.material_basis,
                unit_material=self.material_unit,
            )

        return loading

    def spreading_pressure_at(
        self,
        pressure: t.List[float],
        branch: str = 'ads',
        pressure_unit: str = None,
        pressure_mode: str = None,
        loading_unit: str = None,
        loading_basis: str = None,
        material_unit: str = None,
        material_basis: str = None,
        interp_fill: t.Union[float, t.Tuple[float, float], str] = None,
    ) -> numpy.ndarray:
        r"""
        Calculate reduced spreading pressure at a bulk adsorbate pressure P.

        Use numerical quadrature on isotherm data points to compute the reduced
        spreading pressure via the integral:

        .. math::

            \Pi(p) = \int_0^p \frac{q(\hat{p})}{ \hat{p}} d\hat{p}.

        In this integral, the isotherm :math:`q(\hat{p})` is represented by a
        linear interpolation of the data.

        For in-detail explanations, check reference [#]_.

        Parameters
        ----------
        pressure : float
            Pressure (in corresponding units as data in instantiation).
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.
        loading_unit : str
            Unit the loading is specified in. If ``None``, it defaults to
            internal isotherm units.
        pressure_unit : str
            Unit the pressure is returned in. If ``None``, it defaults to
            internal isotherm units.
        material_basis : str
            The basis the loading is passed in. If ``None``, it defaults to
            internal isotherm basis.
        pressure_mode : str
            The mode the pressure is returned in. If ``None``, it defaults to
            internal isotherm mode.
        interp_fill : array-like or (array-like, array_like) or “extrapolate”, optional
            Parameter to determine what to do outside data bounds.
            Passed to the scipy.interpolate.interp1d function as ``fill_value``.
            If blank, interpolation will not predict outside the bounds of data.

        Returns
        -------
        float
            Spreading pressure, :math:`\Pi`.

        References
        ----------
        .. [#] C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution
           Theory (IAST) Python Package. Computer Physics Communications.

        """
        # Get all data points
        pressures = self.pressure(
            branch=branch, pressure_unit=pressure_unit, pressure_mode=pressure_mode
        )
        loadings = self.loading(
            branch=branch,
            loading_unit=loading_unit,
            loading_basis=loading_basis,
            material_unit=material_unit,
            material_basis=material_basis
        )

        # Check if we need to extrapolate beyond available data
        if (self.l_interpolator is not None and self.l_interpolator.interp_fill is None) & \
                (pressure > pressures.max() or pressure < pressures.min()):
            raise CalculationError(
                textwrap.dedent(
                    f"""
                To compute the spreading pressure at this bulk adsorbate pressure,
                we would need to extrapolate the isotherm since this pressure ({pressure:.3g} {self.pressure_unit})
                is outside the range of the highest pressure in your pure-component
                isotherm data ({pressures.max()} {self.pressure_unit}).

                At present, the PointIsotherm class is set to throw an exception
                when this occurs, as we do not have data outside this pressure range
                to characterize the isotherm at higher pressures.

                Option 1: fit an analytical model to extrapolate the isotherm
                Option 2: pass a `interp_fill` to the spreading pressure function of the
                    PointIsotherm object. Then, that PointIsotherm will
                    assume that the uptake beyond {pressures.max()} {self.pressure_unit} is given by
                    `interp_fill`. This is reasonable if your isotherm data exhibits
                    a plateau at the highest pressures.
                Option 3: Go back to the lab or computer to collect isotherm data
                    at higher pressures. (Extrapolation can be dangerous!)
                """
                )
            )

        # Step 1: Approximate loading up to first pressure point with Henry's law
        # loading = henry_const * P where henry_const is the initial slope
        henry_const = loadings[0] / pressures[0]

        # Step 2: Find how many points are less than target pressure P
        n_points = numpy.sum(pressures < pressure)

        if n_points == 0:
            # Step 3a: If P is between 0 and first pressure point
            # The integral simplifies to henry_const * P
            return henry_const * pressure

        # Step 3b: P > first pressure point - calculate the total area
        # Area of first segment from 0 to P_1
        area = loadings[0]

        # Step 4: Calculate area between P_1 and P_k where P_k < P < P_{k+1}
        # using linear interpolation of isotherm data
        for i in range(n_points - 1):
            slope = (loadings[i + 1] - loadings[i]) / (pressures[i + 1] - pressures[i])
            intercept = loadings[i] - slope * pressures[i]
            # Add area of this segment
            area += slope * (pressures[i + 1] - pressures[i]) + intercept * \
                numpy.log(pressures[i + 1] / pressures[i])

        # Step 5: Calculate area of final segment from P_k to P
        # Get the loading at pressure P using interpolation
        loading_at_p = self.loading_at(
            pressure,
            branch=branch,
            pressure_unit=pressure_unit,
            pressure_mode=pressure_mode,
            loading_unit=loading_unit,
            loading_basis=loading_basis,
            material_unit=material_unit,
            material_basis=material_basis,
            interp_fill=interp_fill
        )

        # Calculate the slope of the final segment
        slope = (loading_at_p - loadings[n_points - 1]) / (pressure - pressures[n_points - 1])
        intercept = loadings[n_points - 1] - slope * pressures[n_points - 1]

        # Add the area of the final segment
        area += slope * (pressure - pressures[n_points - 1]) + intercept * \
            numpy.log(pressure / pressures[n_points - 1])

        return area
