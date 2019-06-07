"""
This module contains the main class that describes an isotherm through discrete points.
"""


import matplotlib.pyplot as plt
import numpy
import pandas

import pygaps

from ..graphing.isothermgraphs import plot_iso
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.isotherm_interpolator import isotherm_interpolator
from ..utilities.unit_converter import c_adsorbent
from ..utilities.unit_converter import c_loading
from ..utilities.unit_converter import c_pressure
from .isotherm import Isotherm


class PointIsotherm(Isotherm):
    """
    Class which contains the points from an adsorption isotherm.

    This class is designed to be a complete description of a discrete isotherm.
    It extends the Isotherm class, which contains all the description of the
    isotherm parameters, but also holds the datapoints recorded during an experiment
    or simulation.

    The minimum arguments required to instantiate the class, besides those required for
    the parent Isotherm, are data, specified either as pressure and loading arrays or
    as isotherm_data (a pandas dataframe containing the discrete points), as well as
    string keys for the columns of the dataframe which have the loading and the pressure data.

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
        The title of the pressure data in the DataFrame provided.
    loading_key : str
        The title of the loading data in the DataFrame provided.
    other_keys : iterable
        Other pandas DataFrame columns which contain data to be stored.
    branch : ['guess', ads', 'des', iterable], optional
        The branch of the isotherm. The code will automatically attempt to
        guess if there's an adsorption and desorption branch.
        The user can instead tell the framework that all points are
        part of an adsorption ('ads') or desorption ('des') curve.
        Alternatively, an iterable can be passed which contains
        detailed info for each data point if adsorption points ('False')
        or desorption points ('True'). eg: [False, False, True, True...]
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

    Notes
    -----

    This class assumes that the datapoints do not contain noise.
    Detection of adsorption/desorption branches will not work if
    data is noisy.

    """

    _reserved_params = [
        'raw_data',
        'l_interpolator',
        'p_interpolator',
        'loading_key',
        'pressure_key',
        'other_keys',
    ]

##########################################################
#   Instantiation and classmethods

    def __init__(self,
                 pressure=None,
                 loading=None,
                 isotherm_data=None,
                 pressure_key=None,
                 loading_key=None,
                 other_keys=None,
                 branch='guess',

                 adsorbent_basis="mass",
                 adsorbent_unit="g",
                 loading_basis="molar",
                 loading_unit="mmol",
                 pressure_mode="absolute",
                 pressure_unit="bar",

                 **isotherm_parameters):
        """
        Instantiation is done by passing the discrete data as a pandas
        DataFrame, the column keys as string  as well as the parameters
        required by parent class.
        """
        # Checks
        if isotherm_data is not None:
            if None in [pressure_key, loading_key]:
                raise ParameterError(
                    "Pass loading_key and pressure_key, the names of the loading and"
                    " pressure columns in the DataFrame, to the constructor.")

            # Save column names
            #: Name of column in the dataframe that contains adsorbed amount.
            self.loading_key = loading_key

            #: Name of column in the dataframe that contains pressure.
            self.pressure_key = pressure_key

            #: List of column in the dataframe that contains other points.
            if other_keys:
                self.other_keys = other_keys
            else:
                self.other_keys = []

            #: Pandas DataFrame that stores the data.
            columns = [self.pressure_key, self.loading_key]
            columns.extend(self.other_keys)
            if not all([a in isotherm_data.columns for a in columns]):
                raise ParameterError(
                    "Could not find some specified columns in the adsorption DataFrame")
            self.raw_data = isotherm_data[columns].sort_index(axis=1)

        elif pressure is not None or loading is not None:
            if pressure is None or loading is None:
                raise ParameterError(
                    "If you've chosen to pass loading and pressure directly as"
                    " arrays, make sure both are specified!")
            if len(pressure) != len(loading):
                raise ParameterError(
                    "Pressure and loading arrays are not equal!")
            if other_keys:
                raise ParameterError(
                    "Cannot specify other isotherm components in this mode."
                    " Use the ``isotherm_data`` method")

            # Standard column names
            self.pressure_key = 'pressure'
            self.loading_key = 'loading'
            self.other_keys = []

            # DataFrame creation
            self.raw_data = pandas.DataFrame({self.pressure_key: pressure,
                                              self.loading_key: loading})
        else:
            raise ParameterError(
                "Pass either the isotherm data in a pandas.DataFrame as ``isotherm_data``"
                " or directly ``pressure`` and ``loading`` as arrays.")

        # Run base class constructor
        Isotherm.__init__(self,
                          adsorbent_basis=adsorbent_basis,
                          adsorbent_unit=adsorbent_unit,
                          loading_basis=loading_basis,
                          loading_unit=loading_unit,
                          pressure_mode=pressure_mode,
                          pressure_unit=pressure_unit,

                          **isotherm_parameters)

        # Deal with the isotherm branches (ads/des)
        if branch == 'guess':
            # Split the data in adsorption/desorption
            self.raw_data = self._splitdata(self.raw_data, self.pressure_key)
        elif branch == 'ads':
            self.raw_data.insert(len(self.raw_data.columns), 'branch', False)
        elif branch == 'des':
            self.raw_data.insert(len(self.raw_data.columns), 'branch', True)
        else:
            try:
                self.raw_data.insert(len(self.raw_data.columns), 'branch', branch)
            except Exception as e_info:
                raise ParameterError(e_info)

        #: The internal interpolator for loading given pressure.
        self.l_interpolator = isotherm_interpolator('loading', None, None,
                                                    interp_branch=None)

        #: The internal interpolator for pressure given loading.
        self.p_interpolator = isotherm_interpolator('pressure', None, None,
                                                    interp_branch=None)

    @classmethod
    def from_json(cls, json_string, **isotherm_parameters):
        """
        Construct a PointIsotherm from a standard json-represented isotherm.
        This function is just a wrapper around the more powerful .isotherm_from_json
        function.

        Parameters
        ----------
        json_string : str
            A json standard isotherm representation.
        isotherm_parameters :
            Any other options to be passed to the isotherm creation, like mode, basis or unit.
        """
        return pygaps.isotherm_from_json(json_string, **isotherm_parameters)

    @classmethod
    def from_isotherm(cls, isotherm,
                      pressure=None,
                      loading=None,
                      isotherm_data=None,
                      pressure_key=None,
                      loading_key=None,
                      other_keys=None):
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
        isotherm_data : DataFrame
            Pure-component adsorption isotherm data.
        loading_key : str
            Column of the pandas DataFrame where the loading is stored.
        pressure_key : str
            Column of the pandas DataFrame where the pressure is stored.
        """
        # get isotherm parameters as a dictionary
        iso_params = isotherm.to_dict()
        # insert or update values
        iso_params['pressure'] = pressure
        iso_params['loading'] = loading
        iso_params['isotherm_data'] = isotherm_data
        iso_params['pressure_key'] = pressure_key
        iso_params['loading_key'] = loading_key
        iso_params['other_keys'] = other_keys

        return cls(**iso_params)

    @classmethod
    def from_modelisotherm(cls, modelisotherm, pressure_points=None):
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
                - If a PointIsotherm is passed, the values will be calculated at each
                  of the pressure points in the passed isotherm. This is useful for
                  comparing a model overlap with the real isotherm.
        """
        if pressure_points is None:
            pressure = modelisotherm.pressure()
        elif isinstance(pressure_points, PointIsotherm):
            pressure = pressure_points.pressure(branch=modelisotherm.branch)
        else:
            pressure = pressure_points

        return PointIsotherm(
            isotherm_data=pandas.DataFrame({
                'pressure': pressure,
                'loading': modelisotherm.loading_at(pressure)
            }),
            loading_key='loading', pressure_key='pressure',
            **modelisotherm.to_dict())

    ##########################################################
    #   Conversion functions

    def convert_pressure(self, mode_to=None, unit_to=None, verbose=False):
        """
        Convert isotherm pressure from one unit to another
        and the pressure mode from absolute to relative.

        Only applicable in the case of isotherms taken below critical
        point of adsorbate.

        Parameters
        ----------
        pressure_mode : {'relative', 'absolute'}
            The mode in which the isotherm should be converted.
        unit_to : str
            The unit into which the internal pressure should be converted to.
        verbose : bool
            Print out steps taken.
        """

        if mode_to == self.pressure_mode and unit_to == self.pressure_unit:
            if verbose:
                print("Mode and units are the same, no changes made")

        else:
            if not mode_to:
                mode_to = self.pressure_mode

            self.raw_data[self.pressure_key] = c_pressure(
                self.raw_data[self.pressure_key],
                mode_from=self.pressure_mode,
                mode_to=mode_to,
                unit_from=self.pressure_unit,
                unit_to=unit_to,
                adsorbate_name=self.adsorbate,
                temp=self.t_iso)

            if unit_to != self.pressure_unit and mode_to == 'absolute':
                self.pressure_unit = unit_to
            else:
                self.pressure_unit = None
            if mode_to != self.pressure_mode:
                self.pressure_mode = mode_to

            # Re-process interpolator
            interp_branch = self.p_interpolator.interp_branch
            self.p_interpolator = isotherm_interpolator('pressure',
                                                        self.loading(
                                                            branch=interp_branch),
                                                        self.pressure(
                                                            branch=interp_branch),
                                                        interp_branch=interp_branch)

            if verbose:
                print("Changed pressure to mode {0}, unit {1}".format(
                    mode_to, unit_to))

    def convert_loading(self, basis_to=None, unit_to=None, verbose=False):
        """
        Convert isotherm loading from one unit to another
        and the basis of the isotherm loading to be
        either 'volume' or 'mass' or 'molar'.

        Parameters
        ----------
        basis : {'volume', 'mass', 'molar'}
            The basis in which the isotherm should be converted.
        unit_to : str
            The unit into which the internal loading should be converted to.
        verbose : bool
            Print out steps taken.

        """

        if basis_to == self.loading_basis and unit_to == self.loading_unit:
            if verbose:
                print("Mode and units are the same, no changes made")

        else:
            if not basis_to:
                basis_to = self.loading_basis

            self.raw_data[self.loading_key] = c_loading(
                self.raw_data[self.loading_key],
                basis_from=self.loading_basis,
                basis_to=basis_to,
                unit_from=self.loading_unit,
                unit_to=unit_to,
                adsorbate_name=self.adsorbate,
                temp=self.t_iso)

            if unit_to != self.loading_unit:
                self.loading_unit = unit_to
            if basis_to != self.loading_basis:
                self.loading_basis = basis_to

            # Re-process interpolator
            interp_branch = self.p_interpolator.interp_branch
            self.p_interpolator = isotherm_interpolator('pressure',
                                                        self.loading(
                                                            branch=interp_branch),
                                                        self.pressure(
                                                            branch=interp_branch),
                                                        interp_branch=interp_branch)

            if verbose:
                print("Changed loading to basis {0}, unit {1}".format(
                    basis_to, unit_to))

    def convert_adsorbent(self, basis_to=None, unit_to=None, verbose=False):
        """
        Converts the adsorbent of the isotherm from one unit to another
        and the basis of the isotherm loading to be
        either 'per mass' or 'per volume' or 'per mole' of adsorbent.

        Only applicable to materials that have been loaded in memory
        with a 'density' or 'molar mass' property respectively.

        Parameters
        ----------
        basis : {'volume', 'mass', 'molar'}
            The basis in which the isotherm should be converted.
        unit_to : str
            The unit into which the internal loading should be converted to.
        verbose : bool
            Print out steps taken.

        """

        if basis_to == self.adsorbent_basis and unit_to == self.adsorbent_unit:
            if verbose:
                print("Mode and units are the same, no changes made")

        else:
            if not basis_to:
                basis_to = self.adsorbent_basis

            self.raw_data[self.loading_key] = c_adsorbent(
                self.raw_data[self.loading_key],
                basis_from=self.adsorbent_basis,
                basis_to=basis_to,
                unit_from=self.adsorbent_unit,
                unit_to=unit_to,
                material_name=self.material_name,
                material_batch=self.material_batch)

            if unit_to != self.adsorbent_unit:
                self.adsorbent_unit = unit_to
            if basis_to != self.adsorbent_basis:
                self.adsorbent_basis = basis_to

            # Re-process interpolator
            interp_branch = self.p_interpolator.interp_branch
            self.p_interpolator = isotherm_interpolator('pressure',
                                                        self.loading(
                                                            branch=interp_branch),
                                                        self.pressure(
                                                            branch=interp_branch),
                                                        interp_branch=interp_branch)

            if verbose:
                print("Changed loading to basis {0}, unit {1}".format(
                    basis_to, unit_to))

###########################################################
#   Info function

    def print_info(self, show=True, **plot_iso_args):
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
            y2_data=self.other_keys[0] if self.other_keys else None,
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
    #   Functions that return parts of the isotherm data

    def data(self, raw=False, branch=None):
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
        if raw:
            return self.raw_data
        elif branch is None:
            return self.raw_data.drop('branch', axis=1)
        elif branch == 'ads':
            return self.raw_data.loc[~self.raw_data['branch']].drop('branch', axis=1)
        elif branch == 'des':
            return self.raw_data.loc[self.raw_data['branch']].drop('branch', axis=1)
        else:
            return None

    def pressure(self, branch=None,
                 pressure_unit=None, pressure_mode=None,
                 min_range=None, max_range=None, indexed=False):
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
        array or Series
            The pressure slice corresponding to the parameters passed.

        """
        ret = self.data(branch=branch).loc[:, self.pressure_key]

        if not ret.empty:
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

            # Select required points
            if max_range is not None or min_range is not None:
                if min_range is None:
                    min_range = min(ret)
                if max_range is None:
                    max_range = max(ret)

                ret = ret.loc[lambda x: x >=
                              min_range].loc[lambda x: x <= max_range]

        if indexed:
            return ret
        else:
            return ret.values

    def loading(self, branch=None,
                loading_unit=None, loading_basis=None,
                adsorbent_unit=None, adsorbent_basis=None,
                min_range=None, max_range=None, indexed=False):
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
        loading_basis : {None, 'mass', 'volume', 'molar'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        adsorbent_basis : {None, 'mass', 'volume', 'molar'}
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
        Array or Series
            The loading slice corresponding to the parameters passed.

        """
        ret = self.data(branch=branch).loc[:, self.loading_key]

        if not ret.empty:
            # Convert if needed
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

            # Select required points
            if max_range is not None or min_range is not None:
                if min_range is None:
                    min_range = min(ret)
                if max_range is None:
                    max_range = max(ret)
                ret = ret.loc[lambda x: x >=
                              min_range].loc[lambda x: x <= max_range]

        if indexed:
            return ret
        else:
            return ret.values

    def other_data(self, key, branch=None,
                   min_range=None, max_range=None, indexed=False):
        """
        Return supplementary data points as an array.

        Parameters
        ----------
        key : str
            Key in the isotherm DataFrame containing the data to select.
        branch : {None, 'ads', 'des'}
            The branch of the data to return. If ``None``, returns entire
            dataset.
        min_range : float, optional
            The lower limit for the data to select.
        max_range : float, optional
            The higher limit for the data to select.
        indexed : bool, optional
            If this is specified to true, then the function returns an indexed
            pandas.Series with the columns requested instead of an array.

        Returns
        -------
        array or Series
            The data slice corresponding to the parameters passed.

        """
        if key in self.other_keys:
            ret = self.data(branch=branch).loc[:, key]

            if not ret.empty:
                # Select required points
                if max_range is not None or min_range is not None:
                    if min_range is None:
                        min_range = min(ret)
                    if max_range is None:
                        max_range = max(ret)
                    ret = ret.loc[lambda x: x >=
                                  min_range].loc[lambda x: x <= max_range]

            if indexed:
                return ret
            else:
                return ret.values

        else:
            return None

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
        if self.data(branch=branch).empty:
            return False
        else:
            return True

    ##########################################################
    #   Functions that interpolate values of the isotherm data

    def loading_at(self, pressure,
                   branch='ads',
                   interpolation_type='linear',
                   interp_fill=None,

                   pressure_unit=None, pressure_mode=None,
                   loading_unit=None, loading_basis=None,
                   adsorbent_unit=None, adsorbent_basis=None,
                   ):
        """
        Interpolate isotherm to compute loading at any pressure P.

        Parameters
        ----------
        pressure : float or array
            Pressure at which to compute loading.
        branch : {'ads','des'}
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
        loading_basis : {None, 'mass', 'volume', 'molar'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        adsorbent_basis : {None, 'mass', 'volume', 'molar'}
            The basis on which to return the adsorbent, if possible. If ``None``,
            returns on the basis the isotherm is currently in.

        Returns
        -------
        float or array
            Predicted loading at pressure P.

        """
        # Convert to a numpy array just in case
        pressure = numpy.asarray(pressure)

        # Check if interpolator is good
        if branch != self.l_interpolator.interp_branch or \
                interpolation_type != self.l_interpolator.interp_kind or \
                interp_fill != self.l_interpolator.interp_fill:

            self.l_interpolator = isotherm_interpolator('loading',
                                                        self.pressure(
                                                            branch=branch),
                                                        self.loading(
                                                            branch=branch),
                                                        interp_branch=branch,
                                                        interp_kind=interpolation_type,
                                                        interp_fill=interp_fill)

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

        # Interpolate using the internal interpolator
        loading = self.l_interpolator(pressure)

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

    def pressure_at(self, loading,
                    branch='ads',
                    interpolation_type='linear',
                    interp_fill=None,

                    pressure_unit=None, pressure_mode=None,
                    loading_unit=None, loading_basis=None,
                    adsorbent_unit=None, adsorbent_basis=None,
                    ):
        """
        Interpolate isotherm to compute pressure at any loading n.

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
        loading_basis : {None, 'mass', 'volume'}
            The basis the loading is specified in. If ``None``,
            assumes the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent is passed in. If ``None``
            it defaults to which loading unit the isotherm is currently in
        adsorbent_basis : str
            The basis the loading is passed in. If ``None``, it defaults to
            internal isotherm basis.

        Returns
        -------
        float
            Predicted pressure at loading specified.

        """
        # Convert to numpy array just in case
        loading = numpy.asarray(loading)

        # Check if interpolator branch is good
        if branch != self.p_interpolator.interp_branch or \
                interpolation_type != self.p_interpolator.interp_kind or \
                interp_fill != self.p_interpolator.interp_fill:

            self.p_interpolator = isotherm_interpolator('pressure',
                                                        self.loading(
                                                            branch=branch),
                                                        self.pressure(
                                                            branch=branch),
                                                        interp_branch=branch,
                                                        interp_kind=interpolation_type,
                                                        interp_fill=interp_fill)

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

        # Interpolate using the internal interpolator
        pressure = self.p_interpolator(loading)

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

    def spreading_pressure_at(self, pressure,
                              branch='ads',

                              pressure_unit=None,
                              pressure_mode=None,
                              loading_unit=None,
                              loading_basis=None,
                              adsorbent_unit=None,
                              adsorbent_basis=None,
                              interp_fill=None):
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
        adsorbent_basis : str
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
        pressures = self.pressure(branch=branch,
                                  pressure_unit=pressure_unit,
                                  pressure_mode=pressure_mode)
        loadings = self.loading(branch=branch,
                                loading_unit=loading_unit,
                                loading_basis=loading_basis,
                                adsorbent_unit=adsorbent_unit,
                                adsorbent_basis=adsorbent_basis)

        # throw exception if interpolating outside the range.
        if (self.l_interpolator.interp_fill is None) & (pressure > pressures.max() or pressure < pressures.min()):
            raise CalculationError(
                """
            To compute the spreading pressure at this bulk
            adsorbate pressure, we would need to extrapolate the isotherm since this
            pressure is outside the range of the highest pressure in your
            pure-component isotherm data, {0}.

            At present, the PointIsotherm object is set to throw an
            exception when this occurs, as we do not have data outside this
            pressure range to characterize the isotherm at higher pressures.

            Option 1: fit an analytical model to extrapolate the isotherm
            Option 2: pass a `interp_fill` to the spreading pressure function of the
                PointIsotherm object. Then, that PointIsotherm will
                assume that the uptake beyond pressure {0} is given by
                `interp_fill`. This is reasonable if your isotherm data exhibits
                a plateau at the highest pressures.
            Option 3: Go back to the lab or computer to collect isotherm data
                at higher pressures. (Extrapolation can be dangerous!)
                """.format(pressures.max())
            )

        # approximate loading up to first pressure point with Henry's law
        # loading = henry_const * P
        # henry_const is the initial slope in the adsorption isotherm
        henry_const = loadings[0] / pressures[0]

        # get how many of the points are less than pressure P
        n_points = numpy.sum(pressures < pressure)

        if n_points == 0:
            # if this pressure is between 0 and first pressure point...
            # \int_0^P henry_const P /P dP = henry_const * P ...
            return henry_const * pressure

        # P > first pressure point
        area = loadings[0]  # area of first segment \int_0^P_1 n(P)/P dP

        # get area between P_1 and P_k, where P_k < P < P_{k+1}
        for i in range(n_points - 1):
            # linear interpolation of isotherm data
            slope = (loadings[i + 1] - loadings[i]) / (pressures[i + 1] -
                                                       pressures[i])
            intercept = loadings[i] - slope * pressures[i]
            # add area of this segment
            area += slope * (pressures[i + 1] - pressures[i]) + intercept * \
                numpy.log(pressures[i + 1] / pressures[i])

        # finally, area of last segment
        slope = (
            self.loading_at(pressure,
                            branch=branch,
                            pressure_unit=pressure_unit,
                            pressure_mode=pressure_mode,

                            loading_unit=loading_unit,
                            loading_basis=loading_basis,
                            adsorbent_unit=adsorbent_unit,
                            adsorbent_basis=adsorbent_basis,
                            interp_fill=interp_fill) - loadings[n_points - 1]) / (
            pressure - pressures[n_points - 1])
        intercept = loadings[n_points - 1] - \
            slope * pressures[n_points - 1]
        area += slope * (pressure - pressures[n_points - 1]) + intercept * \
            numpy.log(pressure / pressures[n_points - 1])

        return area
