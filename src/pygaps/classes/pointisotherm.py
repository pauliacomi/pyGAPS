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
    the parent Isotherm, are isotherm_data, as the pandas dataframe containing the
    discrete points, as well as string keys for the columns of the dataframe which have
    the loading and the pressure data.

    Parameters
    ----------
    isotherm_data : DataFrame
        Pure-component adsorption isotherm data.
    loading_key : str
        The title of the pressure data in the DataFrame provided.
    pressure_key : str
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
        '_instantiated',
        '_data',
        'l_interpolator',
        'p_interpolator',
        'loading_key',
        'pressure_key',
        'other_keys',
    ]

##########################################################
#   Instantiation and classmethods

    def __init__(self,
                 isotherm_data,
                 loading_key=None,
                 pressure_key=None,
                 other_keys=[],
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

        # Start construction process
        self._instantiated = False

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

        # Save column names
        #: Name of column in the dataframe that contains adsorbed amount.
        self.loading_key = loading_key

        #: Name of column in the dataframe that contains pressure.
        self.pressure_key = pressure_key

        #: Pandas DataFrame that stores the data.
        columns = [pressure_key, loading_key]
        columns.extend(other_keys)
        self._data = isotherm_data[columns].sort_index(axis=1)

        #: List of column in the dataframe that contains other points.
        self.other_keys = other_keys

        # Deal with the branches
        if branch == 'guess':
            # Split the data in adsorption/desorption
            self._data = self._splitdata(self._data, pressure_key)
        elif branch == 'ads':
            self._data.insert(len(self._data.columns), 'branch', False)
        elif branch == 'des':
            self._data.insert(len(self._data.columns), 'branch', True)
        else:
            try:
                self._data.insert(len(self._data.columns), 'branch', branch)
            except Exception as e_info:
                raise ParameterError(e_info)

        #: The internal interpolator for loading given pressure.
        self.l_interpolator = isotherm_interpolator('loading', None, None,
                                                    interp_branch=None)

        #: The internal interpolator for pressure given loading.
        self.p_interpolator = isotherm_interpolator('pressure', None, None,
                                                    interp_branch=None)

        # Finish instantiation process
        self._instantiated = True

        # Now that all data has been saved, generate the unique id if needed.
        if self.id is None:
            self._check_if_hash(True, [True])

    @classmethod
    def from_json(cls, json_string, **isotherm_parameters):
        """
        Constructs a PointIsotherm from a standard json-represented isotherm.
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
    def from_isotherm(cls, isotherm, isotherm_data,
                      loading_key=None,
                      pressure_key=None,
                      other_keys=[]):
        """
        Constructs a point isotherm using a parent isotherm as the template for
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
        """
        # get isotherm parameters as a dictionary
        iso_params = isotherm.to_dict()
        # remove ID - a new one will be generated
        iso_params.pop('id', None)
        # insert or update values
        iso_params['loading_key'] = loading_key
        iso_params['pressure_key'] = pressure_key
        iso_params['other_keys'] = other_keys

        return cls(isotherm_data, **iso_params)

    @classmethod
    def from_modelisotherm(cls, modelisotherm, pressure_points=None,
                           pressure_key='pressure',
                           loading_key='loading',
                           ):
        """
        Constructs a PointIsotherm from a ModelIsothem class.
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

        loading_key : str, optional
            The title of the pressure data in the DataFrame provided.
        pressure_key : str, optional
            The title of the loading data in the DataFrame provided.
        """

        if pressure_points is None:
            pressure = modelisotherm.pressure()
        elif isinstance(pressure_points, PointIsotherm):
            pressure = pressure_points.pressure(branch=modelisotherm.branch)
        else:
            pressure = pressure_points

        iso_data = pandas.DataFrame(
            {
                pressure_key: pressure,
                loading_key: modelisotherm.loading_at(pressure)
            }
        )

        iso_params = modelisotherm.to_dict()
        iso_params.pop('id', None)
        return PointIsotherm(iso_data,
                             loading_key=loading_key,
                             pressure_key=pressure_key,
                             **iso_params)

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
        self._check_if_hash(name, ['_data'])


##########################################################
#   Conversion functions

    def convert_pressure(self, mode_to=None, unit_to=None, verbose=False):
        """
        Converts the pressure values of the isotherm from one unit to another
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

            self._data[self.pressure_key] = c_pressure(
                self._data[self.pressure_key],
                mode_from=self.pressure_mode,
                mode_to=mode_to,
                unit_from=self.pressure_unit,
                unit_to=unit_to,
                adsorbate_name=self.adsorbate,
                temp=self.t_exp)

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

        return

    def convert_loading(self, basis_to=None, unit_to=None, verbose=False):
        """
        Converts the loading of the isotherm from one unit to another
        and the basis of the isotherm loading to be
        either 'per mass' or 'per volume' of adsorbent.

        Only applicable to adsorbents that have been loaded in memory
        with a 'density' property.

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

            self._data[self.loading_key] = c_loading(
                self._data[self.loading_key],
                basis_from=self.loading_basis,
                basis_to=basis_to,
                unit_from=self.loading_unit,
                unit_to=unit_to,
                adsorbate_name=self.adsorbate,
                temp=self.t_exp)

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

        return

    def convert_adsorbent(self, basis_to=None, unit_to=None, verbose=False):
        """
        Converts the adsorbent of the isotherm from one unit to another
        and the basis of the isotherm loading to be
        either 'per mass' or 'per volume' of adsorbent.

        Only applicable to adsorbents that have been loaded in memory
        with a 'density' property.

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

            self._data[self.loading_key] = c_adsorbent(
                self._data[self.loading_key],
                basis_from=self.adsorbent_basis,
                basis_to=basis_to,
                unit_from=self.adsorbent_unit,
                unit_to=unit_to,
                sample_name=self.sample_name,
                sample_batch=self.sample_batch)

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

        return

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

        secondary_data = None
        if self.other_keys:
            secondary_data = self.other_keys[0]

        plot_dict = dict(
            secondary_data=secondary_data,
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


##########################################################
#   Functions that return parts of the isotherm data

    def data(self, branch=None):
        """
        Returns all data.

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
        if branch is None:
            return self._data.drop('branch', axis=1)
        elif branch == 'ads':
            return self._data.loc[~self._data['branch']].drop('branch', axis=1)
        elif branch == 'des':
            return self._data.loc[self._data['branch']].drop('branch', axis=1)
        else:
            return None

    def pressure(self, branch=None,
                 pressure_unit=None, pressure_mode=None,
                 min_range=None, max_range=None, indexed=False):
        """
        Returns pressure points as an array.

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
                                 temp=self.t_exp
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
        Returns loading points as an array.

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the loading to return. If ``None``, returns entire
            dataset.
        loading_unit : str, optional
            Unit in which the loading should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        loading_basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If ``None``
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
        array or Series
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
        Returns adsorption enthalpy points as an array.

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
            The type of scipi.interp1d used: `linear`, `nearest`, `zero`,
            `slinear`, `quadratic`, `cubic`. It defaults to `linear`.
        interp_fill : float
            Maximum value until which the interpolation is done. If blank,
            interpolation will not predict outside the bounds of data.

        pressure_unit : str
            Unit the pressure is specified in. If ``None``, it defaults to
            internal isotherm units.
        pressure_mode : str
            The mode the pressure is passed in. If ``None``, it defaults to
            internal isotherm mode.

        loading_unit : str, optional
            Unit in which the loading should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        loading_basis : {None, 'mass', 'volume'}
            The basis on which to return the loading, if possible. If ``None``,
            returns on the basis the isotherm is currently in.
        adsorbent_unit : str, optional
            Unit in which the adsorbent should be returned. If ``None``
            it defaults to which loading unit the isotherm is currently in.
        adsorbent_basis : {None, 'mass', 'volume'}
            The basis on which to return the adsorbent, if possible. If ``None``,
            returns on the basis the isotherm is currently in.

        Returns
        -------
        float or array
            Predicted loading at pressure P.
        """

        # Convert to numpy array just in case
        pressure = numpy.array(pressure)

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
                                  temp=self.t_exp)

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
            The type of scipi.interp1d used: `linear`, `nearest`, `zero`,
            `slinear`, `quadratic`, `cubic`. It defaults to `linear`.
        interp_fill : float
            Maximum value until which the interpolation is done. If blank,
            interpolation will not predict outside the bounds of data.

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
            predicted pressure at loading specified
        """

        # Convert to numpy array just in case
        loading = numpy.array(loading)

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
                                  temp=self.t_exp)

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
        """
        Calculate reduced spreading pressure at a bulk adsorbate pressure P.
        (see Tarafder eqn 4)

        Use numerical quadrature on isotherm data points to compute the reduced
        spreading pressure via the integral:

        .. math::

            \\Pi(p) = \\int_0^p \\frac{q(\\hat{p})}{ \\hat{p}} d\\hat{p}.

        In this integral, the isotherm :math:`q(\\hat{p})` is represented by a
        linear interpolation of the data.

        See reference [#]_.

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
        interp_fill : float
            Maximum value until which the interpolation is done. If blank,
            interpolation will not predict outside the bounds of data.

        Returns
        -------
        float
            spreading pressure, :math:`\\Pi`

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
        if (self.l_interpolator.interp_fill is None) & (pressure > pressures.max()):
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
                PointIsotherm object. Then, PointIsotherm will
                assume that the uptake beyond pressure {0} is equal to
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
        else:
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
