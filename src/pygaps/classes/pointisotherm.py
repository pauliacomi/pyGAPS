"""
This module contains the main class that describes an isotherm through discrete points
"""


import hashlib

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
    Class which contains the points from an adsorption isotherm

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
        pure-component adsorption isotherm data
    loading_key : str
        The title of the pressure data in the DataFrame provided.
    pressure_key
        The title of the loading data in the DataFrame provided.
    other_keys : iterable
        Other pandas DataFrame columns which contain data to be stored.
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
    basis_adsorbent : str, optional
        Whether the adsorption is read in terms of either 'per volume'
        'per molar amount' or 'per mass' of material.
    unit_adsorbent : str, optional
        Unit in which the adsorbent basis is expressed.
    basis_loading : str, optional
        Whether the adsorbed material is read in terms of either 'volume'
        'molar' or 'mass'.
    unit_loading : str, optional
        Unit in which the loading basis is expressed.
    mode_pressure : str, optional
        The pressure mode, either 'absolute' pressures or 'relative' in
        the form of p/p0.
    unit_pressure : str, optional
        Unit of pressure.


    Notes
    -----

    """

##########################################################
#   Instantiation and classmethods

    def __init__(self,
                 isotherm_data,
                 loading_key=None,
                 pressure_key=None,
                 other_keys=None,

                 basis_adsorbent="mass",
                 unit_adsorbent="g",
                 basis_loading="molar",
                 unit_loading="mmol",
                 mode_pressure="absolute",
                 unit_pressure="bar",

                 **isotherm_parameters):
        """
        Instantiation is done by passing the discrete data as a pandas
        DataFrame, the column keys as string  as well as the parameters
        required by parent class
        """

        # Start construction process
        self._instantiated = False

        # Run base class constructor
        Isotherm.__init__(self,
                          loading_key=loading_key,
                          pressure_key=pressure_key,

                          basis_adsorbent=basis_adsorbent,
                          unit_adsorbent=unit_adsorbent,
                          basis_loading=basis_loading,
                          unit_loading=unit_loading,
                          mode_pressure=mode_pressure,
                          unit_pressure=unit_pressure,

                          **isotherm_parameters)

        #: Pandas DataFrame that stores the data
        self._data = isotherm_data.sort_index(axis=1)

        #: List of column in the dataframe that contains other points
        self.other_keys = other_keys

        # Split the data in adsorption/desorption
        self._data = self._splitdata(self._data)

        interp_branch = 'ads'
        #: The internal interpolator for loading given pressure
        self.l_interpolator = isotherm_interpolator('loading',
                                                    self.pressure(
                                                        branch=interp_branch),
                                                    self.loading(
                                                        branch=interp_branch),
                                                    interp_branch=interp_branch)

        #: The internal interpolator for pressure given loading
        self.p_interpolator = isotherm_interpolator('pressure',
                                                    self.loading(
                                                        branch=interp_branch),
                                                    self.pressure(
                                                        branch=interp_branch),
                                                    interp_branch=interp_branch)

        # Now that all data has been saved, generate the unique id if needed
        if self.id is None:
            # Generate the unique id using md5
            sha_hasher = hashlib.md5(
                pygaps.isotherm_to_json(self).encode('utf-8'))
            self.id = sha_hasher.hexdigest()

        self._instantiated = True

    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data,
                      other_keys=None):
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
        return cls(isotherm_data,
                   other_keys=other_keys,

                   pressure_key=isotherm.pressure_key,
                   loading_key=isotherm.loading_key,
                   **isotherm.to_dict())

    @classmethod
    def from_json(cls, json_string, **isotherm_parameters):
        """
        Constructs a PointIsotherm from a standard json-represented isotherm.
        This function is just a wrapper around the more powerful .isotherm_from_json
        function

        Parameters
        ----------
        json_string : str
            A json standard isotherm representation.
        isotherm_parameters :
            Any other options to be passed to the isotherm creation, like mode, basis or unit.
        """
        return pygaps.isotherm_from_json(json_string, **isotherm_parameters)

    @classmethod
    def from_modelisotherm(cls, modelisotherm, pressure_points=None):
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

                - If None, the PointIsotherm returned has a fixed number of
                  equidistant points
                - If an array, the PointIsotherm returned has points at each of the
                  values of the array
                - If a PointIsotherm is passed, the values will be calculated at each
                  of the pressure points in the passed isotherm. This is useful for
                  comparing a model overlap with the real isotherm.
        """

        if not pressure_points:
            pressure = modelisotherm.pressure()
        elif isinstance(pressure_points, PointIsotherm):
            pressure = pressure_points.pressure(branch=modelisotherm.branch)
        else:
            pressure = pressure_points

        iso_data = pandas.DataFrame(
            {
                modelisotherm.pressure_key: pressure,
                modelisotherm.loading_key: modelisotherm.loading_at(pressure)
            }
        )

        return PointIsotherm(iso_data,
                             loading_key=modelisotherm.loading_key,
                             pressure_key=modelisotherm.pressure_key,
                             **modelisotherm.to_dict())

##########################################################
#   Overloaded and private functions

    def __setattr__(self, name, value):
        """
        We overload the usual class setter to make sure that the id is always
        representative of the data inside the isotherm

        The '_instantiated' attribute gets set to true after isotherm __init__
        From then afterwards, each call to modify the isotherm properties
        recalculates the md5 hash.
        This is done to ensure uniqueness and also to allow isotherm objects to
        be easily compared to each other.
        """
        object.__setattr__(self, name, value)

        if self._instantiated and name in [
            'sample_name',
            'sample_batch',
            'adsorbent',
            't_exp',

            'date',
            't_act',
            'lab',
            'comment',
            'user',
            'project',
            'machine',
            'is_real',
            'exp_type',

            'other_properties',
            '_data',
            'unit_pressure',
            'unit_adsorbent',
            'unit_loading'
            'mode_pressure'
            'basis_adsorbent'
            'basis_loading'
        ]:
            # Generate the unique id using md5
            self.id = None
            md_hasher = hashlib.md5(
                pygaps.isotherm_to_json(self).encode('utf-8'))
            self.id = md_hasher.hexdigest()

    def __eq__(self, other_isotherm):
        """
        We overload the equality operator of the isotherm. Since id's should be unique and
        representative of the data inside the isotherm, all we need to ensure equality
        is to compare the two hashes of the isotherms.
        """

        return self.id == other_isotherm.id


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
        mode_pressure : {'relative', 'absolute'}
            the mode in which the isotherm should be put
        unit_to : str
            the unit into which the internal pressure should be converted to
        """

        if mode_to == self.mode_pressure and unit_to == self.unit_pressure:
            if verbose:
                print("Mode and units are the same, no changes made")

        else:
            if not mode_to:
                mode_to = self.mode_pressure
            if not unit_to:
                unit_to = self.unit_pressure

            self._data[self.pressure_key] = c_pressure(
                self._data[self.pressure_key],
                mode_from=self.mode_pressure,
                mode_to=mode_to,
                unit_from=self.unit_pressure,
                unit_to=unit_to,
                adsorbate_name=self.adsorbate,
                temp=self.t_exp)

            if unit_to != self.unit_pressure:
                self.unit_pressure = unit_to
            if mode_to != self.mode_pressure:
                self.mode_pressure = mode_to

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

        Only applicable to absorbents that have been loaded in memory
        with a 'density' property.

        Parameters
        ----------
        basis : {'volume', 'mass', 'molar'}
            the basis in which the isotherm should be converted.
        unit_to : str
            the unit into which the internal loading should be converted to

        """

        if basis_to == self.basis_loading and unit_to == self.unit_loading:
            if verbose:
                print("Mode and units are the same, no changes made")

        else:
            if not basis_to:
                basis_to = self.basis_loading

            self._data[self.loading_key] = c_loading(
                self._data[self.loading_key],
                basis_from=self.basis_loading,
                basis_to=basis_to,
                unit_from=self.unit_loading,
                unit_to=unit_to,
                adsorbate_name=self.adsorbate,
                temp=self.t_exp)

            if unit_to != self.unit_loading:
                self.unit_loading = unit_to
            if basis_to != self.basis_loading:
                self.basis_loading = basis_to

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

        Only applicable to absorbents that have been loaded in memory
        with a 'density' property.

        Parameters
        ----------
        basis : {'volume', 'mass', 'molar'}
            the basis in which the isotherm should be converted.
        unit_to : str
            the unit into which the internal loading should be converted to

        """

        if basis_to == self.basis_adsorbent and unit_to == self.unit_adsorbent:
            if verbose:
                print("Mode and units are the same, no changes made")

        else:
            if not basis_to:
                basis_to = self.basis_adsorbent

            self._data[self.loading_key] = c_adsorbent(
                self._data[self.loading_key],
                basis_from=self.basis_adsorbent,
                basis_to=basis_to,
                unit_from=self.unit_adsorbent,
                unit_to=unit_to,
                sample_name=self.sample_name,
                sample_batch=self.sample_batch)

            if unit_to != self.unit_adsorbent:
                self.unit_adsorbent = unit_to
            if basis_to != self.basis_adsorbent:
                self.basis_adsorbent = basis_to

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

    def print_info(self, logarithmic=False, show=True):
        """
        Prints a short summary of all the isotherm parameters and a graph of the isotherm

        Parameters
        ----------
        logarithmic : bool, optional
            Specifies if the graph printed is logarithmic or not
        show : bool, optional
            Specifies if the graph is shown automatically or not
        """

        print(self)

        if self.other_keys:
            plot_type = 'combined'
            secondary_key = self.other_keys[0]
        else:
            plot_type = 'isotherm'
            secondary_key = None

        plot_iso([self], plot_type=plot_type, branch=["ads", "des"],
                 logx=logarithmic, secondary_key=secondary_key,

                 basis_adsorbent=self.basis_adsorbent,
                 unit_adsorbent=self.unit_adsorbent,
                 basis_loading=self.basis_loading,
                 unit_loading=self.unit_loading,
                 unit_pressure=self.unit_pressure,
                 mode_pressure=self.mode_pressure,

                 )

        if show:
            plt.show()

        return


##########################################################
#   Functions that return parts of the isotherm data

    def data(self, branch=None):
        """
        Returns all data

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the isotherm to return. If None, returns entire
            dataset

        Returns
        -------
        DataFrame
            The pandas DataFrame containing all isotherm data

        """
        if branch is None:
            return self._data.drop('check', axis=1)
        elif branch == 'ads':
            return self._data.loc[~self._data['check']].drop('check', axis=1)
        elif branch == 'des':
            return self._data.loc[self._data['check']].drop('check', axis=1)
        else:
            return None

    def pressure(self, branch=None,
                 pressure_unit=None, pressure_mode=None,
                 min_range=None, max_range=None, indexed=False):
        """
        Returns pressure points as an array

        Parameters
        ----------
        branch : {None, 'ads', 'des'}
            The branch of the pressure to return. If None, returns entire
            dataset
        pressure_unit : str, optional
            Unit in which the pressure should be returned. If None
            it defaults to which pressure unit the isotherm is currently in
        pressure_mode : {None, 'absolute', 'relative'}
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
        array or Series
            The pressure slice corresponding to the parameters passesd
        """
        ret = self.data(branch=branch).loc[:, self.pressure_key]

        # Convert if needed
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.mode_pressure
            if not pressure_unit:
                pressure_unit = self.unit_pressure

            ret = c_pressure(ret,
                             mode_from=self.mode_pressure,
                             mode_to=pressure_mode,
                             unit_from=self.unit_pressure,
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
        Returns loading points as an array

        Parameters
        ----------
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
        array or Series
            The loading slice corresponding to the parameters passesd
        """
        ret = self.data(branch=branch).loc[:, self.loading_key]

        # Convert if needed
        if adsorbent_basis or adsorbent_unit:
            if not adsorbent_basis:
                adsorbent_basis = self.basis_adsorbent

            ret = c_adsorbent(ret,
                              basis_from=self.basis_adsorbent,
                              basis_to=adsorbent_basis,
                              unit_from=self.unit_adsorbent,
                              unit_to=adsorbent_unit,
                              sample_name=self.sample_name,
                              sample_batch=self.sample_batch
                              )

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.basis_loading

            ret = c_loading(ret,
                            basis_from=self.basis_loading,
                            basis_to=loading_basis,
                            unit_from=self.unit_loading,
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
        Returns adsorption enthalpy points as an array

        Parameters
        ----------
        key : str
            Key in the isotherm DataFrame containing the data to select
        branch : {None, 'ads', 'des'}
            The branch of the data to return. If None, returns entire
            dataset
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
            The data slice corresponding to the parameters passesd
        """
        if key in self.other_keys:
            ret = self.data(branch=branch).loc[:, key]

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

        if self.data(branch=branch) is None:
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
                pressure_mode = self.mode_pressure
            if not pressure_unit:
                pressure_unit = self.unit_pressure
            if not pressure_unit and self.mode_pressure == 'relative':
                raise ParameterError("Must specify a pressure unit if the input"
                                     " is in an absolute mode")

            pressure = c_pressure(pressure,
                                  mode_from=pressure_mode,
                                  mode_to=self.mode_pressure,
                                  unit_from=pressure_unit,
                                  unit_to=self.unit_pressure,
                                  adsorbate_name=self.adsorbate,
                                  temp=self.t_exp)

        # Interpolate using the internal interpolator
        loading = self.l_interpolator(pressure)

        # Ensure loading is in correct units and basis requested
        if adsorbent_basis or adsorbent_unit:
            if not adsorbent_basis:
                adsorbent_basis = self.basis_adsorbent

            loading = c_adsorbent(loading,
                                  basis_from=self.basis_adsorbent,
                                  basis_to=adsorbent_basis,
                                  unit_from=self.unit_adsorbent,
                                  unit_to=adsorbent_unit,
                                  sample_name=self.sample_name,
                                  sample_batch=self.sample_batch
                                  )

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.basis_loading

            loading = c_loading(loading,
                                basis_from=self.basis_loading,
                                basis_to=loading_basis,
                                unit_from=self.unit_loading,
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
            loading at which to compute pressure
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.
        interpolation_type : str
            The type of scipi.interp1d used: `linear`, `nearest`, `zero`,
            `slinear`, `quadratic`, `cubic`. It defaults to `linear`.
        interp_fill : float
            Maximum value until which the interpolation is done. If blank,
            interpolation will not predict outside the bounds of data.

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
                adsorbent_basis = self.basis_adsorbent
            if not adsorbent_unit:
                raise ParameterError("Must specify an adsorbent unit if the input"
                                     " is in another basis")

            loading = c_adsorbent(loading,
                                  basis_from=adsorbent_basis,
                                  basis_to=self.basis_adsorbent,
                                  unit_from=adsorbent_unit,
                                  unit_to=self.unit_adsorbent,
                                  sample_name=self.sample_name,
                                  sample_batch=self.sample_batch
                                  )

        if loading_basis or loading_unit:
            if not loading_basis:
                loading_basis = self.basis_loading
            if not loading_unit:
                raise ParameterError("Must specify a loading unit if the input"
                                     " is in another basis")

            loading = c_loading(loading,
                                basis_from=loading_basis,
                                basis_to=self.basis_loading,
                                unit_from=loading_unit,
                                unit_to=self.unit_loading,
                                adsorbate_name=self.adsorbate,
                                temp=self.t_exp
                                )

        # Interpolate using the internal interpolator
        pressure = self.p_interpolator(loading)

        # Ensure pressure is in correct units and mode requested
        if pressure_mode or pressure_unit:
            if not pressure_mode:
                pressure_mode = self.mode_pressure
            if not pressure_unit:
                pressure_unit = self.unit_pressure

            pressure = c_pressure(pressure,
                                  mode_from=self.mode_pressure,
                                  mode_to=pressure_mode,
                                  unit_from=self.unit_pressure,
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

        See C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution
        Theory (IAST) Python Package. Computer Physics Communications.

        Parameters
        ----------
        pressure : float
            pressure (in corresponding units as data in instantiation)
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.
        loading_unit : str
            Unit the loading is specified in. If None, it defaults to
            internal isotherm units.
        pressure_unit : str
            Unit the pressure is returned in. If None, it defaults to
            internal isotherm units.
        adsorbent_basis : str
            The basis the loading is passed in. If None, it defaults to
            internal isotherm basis.
        pressure_mode : str
            The mode the pressure is returned in. If None, it defaults to
            internal isotherm mode.
        interp_fill : float
            Maximum value until which the interpolation is done. If blank,
            interpolation will not predict outside the bounds of data.

        Returns
        -------
        float
            spreading pressure, :math:`\\Pi`
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
