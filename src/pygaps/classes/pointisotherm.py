"""
This module contains the main class that describes an isotherm through discrete points
"""


import hashlib

import numpy
import pandas
from scipy.interpolate import interp1d

import pygaps

from ..graphing.isothermgraphs import plot_iso
from ..utilities.unit_converter import convert_loading
from ..utilities.unit_converter import convert_pressure
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from .adsorbate import Adsorbate
from .isotherm import Isotherm
from .sample import Sample


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
        column of the pandas DataFrame where the loading is stored
    pressure_key : str
        column of the pandas DataFrame where the pressure is stored
    other_keys : iterable
        other pandas DataFrame columns with data
    mode_adsorbent : str, optional
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

        The info dictionary must contain an entry for 'sample_name',  'sample_batch',
        'adsorbate' and 't_exp'

    Notes
    -----

    """

##########################################################
#   Instantiation and classmethods

    def __init__(self, isotherm_data,
                 loading_key=None,
                 pressure_key=None,
                 other_keys=None,
                 mode_adsorbent="mass",
                 mode_pressure="absolute",
                 unit_loading="mmol",
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
                          mode_adsorbent,
                          mode_pressure,
                          unit_loading,
                          unit_pressure,
                          **isotherm_parameters)

        if None in [loading_key, pressure_key]:
            raise ParameterError(
                "Pass loading_key and pressure_key, the names of the loading and"
                " pressure columns in the DataFrame, to the constructor.")

        # Save column names
        #: Name of column in the dataframe that contains adsorbed amount
        self.loading_key = loading_key

        #: Name of column in the dataframe that contains pressure
        self.pressure_key = pressure_key

        #: Pandas DataFrame that stores the data
        self._data = isotherm_data.sort_index(axis=1)

        #: List of column in the dataframe that contains other points
        self.other_keys = other_keys

        # Split the data in adsorption/desorption
        self._data = self._splitdata(self._data)

        #: The internal interpolator function. This is generated
        #: the first time it is needed to make calculations faster
        self.interp_fun = None
        #: the branch the internal interpolator is branched on
        self.interp_branch = None
        #: the kind of interpolator in the internal interpolator
        self.interp_kind = None
        #: value of loading to assume beyond highest pressure in the data
        self.interp_fill = None

        # Now that all data has been saved, generate the unique id if needed
        if self.id is None:
            # Generate the unique id using md5
            sha_hasher = hashlib.md5(
                pygaps.isotherm_to_json(self).encode('utf-8'))
            self.id = sha_hasher.hexdigest()

        self._instantiated = True

    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data,
                      loading_key, pressure_key, other_keys=None):
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
                   loading_key=loading_key,
                   pressure_key=pressure_key,
                   other_keys=other_keys,
                   mode_adsorbent=isotherm.mode_adsorbent,
                   mode_pressure=isotherm.mode_pressure,
                   unit_loading=isotherm.unit_loading,
                   unit_pressure=isotherm.unit_pressure,
                   **isotherm.to_dict())

    @classmethod
    def from_json(cls, json_string,
                  mode_adsorbent="mass",
                  mode_pressure="absolute",
                  unit_loading="mmol",
                  unit_pressure="bar",):
        """
        Constructs a PointIsotherm from a standard json-represented isotherm.
        This function is just a wrapper around the more powerful .isotherm_from_json
        function

        Parameters
        ----------
        json_string : str
            A json standard isotherm representation.
        mode_adsorbent : {'relative', 'absolute'}, optional
            Whether the adsorption is read in terms of either 'per volume'
            or 'per mass'.
        mode_pressure : {'mass','volume'}, optional
            The pressure mode, either absolute pressures or relative in
            the form of p/p0.
        unit_loading : str, optional
            Unit of loading.
        unit_pressure : str, optional
            Unit of pressure.
        """
        return pygaps.isotherm_from_json(json_string,
                                         mode_adsorbent=mode_adsorbent,
                                         mode_pressure=mode_pressure,
                                         unit_loading=unit_loading,
                                         unit_pressure=unit_pressure)

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

        # TODO change from not in to in a known array of parameters
        if self._instantiated and name not in ['id', '_instantiated']:
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

    # Figure out the adsorption and desorption branches
    def _splitdata(self, _data):
        """
        Splits isotherm data into an adsorption and desorption part and
        adds a column to mark the transition between the two
        """
        increasing = _data.loc[:, self.pressure_key].diff().fillna(0) < 0
        increasing.rename('check', inplace=True)

        return pandas.concat([_data, increasing], axis=1)


##########################################################
#   Conversion functions

    def convert_unit_loading(self, unit_to):
        """
        Converts the loading of the isotherm from one unit to another

        Parameters
        ----------
        unit_to : str
            the unit into which the internal loading should be converted to
        """

        self._data[self.loading_key] = convert_loading(
            self._data[self.loading_key],
            self.unit_loading,
            unit_to)

        self.unit_loading = unit_to

        return

    def convert_unit_pressure(self, unit_to):
        """
        Converts the pressure values of the isotherm from one unit to another

        Parameters
        ----------
        unit_to : str
            the unit into which the internal pressure should be converted to
        """

        self._data[self.pressure_key] = convert_pressure(
            self._data[self.pressure_key],
            self.unit_pressure,
            unit_to)

        self.unit_pressure = unit_to

        return

    def convert_mode_pressure(self, mode_pressure):
        """
        Converts the pressure mode from absolute to relative.
        Only applicable in the case of isotherms taken below critical
        point of adsorbate.

        Parameters
        ----------
        mode_pressure : {'relative', 'absolute'}
            the mode in which the isotherm should be put
        """

        if mode_pressure not in self._PRESSURE_MODE:
            raise ParameterError(
                "Mode selected for pressure is not an option. See viable"
                "models in self._PRESSURE_MODE")

        if mode_pressure == self.mode_pressure:
            print("Mode is the same, no changes made")
            return

        if mode_pressure == "absolute":
            sign = 1
        elif mode_pressure == "relative":
            sign = -1

        self._data[self.pressure_key] = self._data[self.pressure_key].apply(
            lambda x: x *
            (Adsorbate.from_list(self.adsorbate).saturation_pressure(self.t_exp, unit=self.unit_pressure)) ** sign)

        self.mode_pressure = mode_pressure

        return

    def convert_mode_adsorbent(self, mode_adsorbent):
        """
        Converts the mode of the isotherm loading to be
        either 'per mass' or 'per volume' of adsorbent. Only
        applicable to absorbents that have been loaded in memory
        with a 'density' property.

        Parameters
        ----------
        mode_adsorbent : {'volume', 'mass'}
            the mode in which the isotherm should be put
        """

        # Syntax checks
        if mode_adsorbent not in self._MATERIAL_MODE:
            raise ParameterError(
                "Mode selected for adsorbent is not an option. See viable"
                "models in self._MATERIAL_MODE")

        if mode_adsorbent == self.mode_adsorbent:
            print("Mode is the same, no changes made")
            return

        if mode_adsorbent == 'volume':
            sign = 1
        elif mode_adsorbent == 'mass':
            sign = -1

        self._data[self.loading_key] = self._data[self.loading_key].apply(
            lambda x: x * (Sample.from_list(self.sample_name, self.sample_batch).get_prop('density'))**sign)

        self.mode_adsorbent = mode_adsorbent

        return

###########################################################
#   Info function

    def print_info(self, logarithmic=False):
        """
        Prints a short summary of all the isotherm parameters and a graph of the isotherm

        Parameters
        ----------
        logarithmic : bool, optional
            Specifies if the graph printed is logarithmic or not
        """

        print(self)

        if 'enthalpy' in self.other_keys:
            plot_type = 'iso-enth'
        else:
            plot_type = 'isotherm'

        plot_iso([self], plot_type=plot_type, branch=["ads", "des"],
                 logarithmic=logarithmic, color=True, fig_title=self.adsorbate)

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

    def pressure(self, unit=None, min_range=None, max_range=None, branch=None):
        """
        Returns pressure points as an array

        Parameters
        ----------
        unit : str, optional
            Unit in which the pressure should be returned. If None
            it defaults to which pressure unit the isotherm is currently in
        min_range : float, optional
            The lower limit for the pressure to select.
        max_range : float, optional
            The higher limit for the pressure to select.
        branch : {None, 'ads', 'des'}
            The branch of the pressure to return. If None, returns entire
            dataset

        Returns
        -------
        array
            The pressure slice corresponding to the parameters passesd
        """
        ret = self.data(branch=branch).loc[:, self.pressure_key].values

        # Convert in required unit
        if unit is not None:
            ret = convert_pressure(ret, self.unit_pressure, unit)

        # Select required points
        if max_range is None or min_range is None:
            return ret
        else:
            if min_range is None:
                min_range = 0
            if max_range is None:
                max_range = max(ret)
            return [x for x in ret if (min_range <= x and x <= max_range)]

    def loading(self, unit=None, min_range=None, max_range=None, branch=None):
        """
        Returns loading points as an array

        Parameters
        ----------
        unit : str, optional
            Unit in which the loading should be returned. If None
            it defaults to which loading unit the isotherm is currently in
        min_range : float, optional
            The lower limit for the loading to select.
        max_range : float, optional
            The higher limit for the loading to select.
        branch : {None, 'ads', 'des'}
            The branch of the loading to return. If None, returns entire
            dataset

        Returns
        -------
        array
            The loading slice corresponding to the parameters passesd
        """
        ret = self.data(branch=branch).loc[:, self.loading_key].values

        # Convert in required unit
        if unit is not None:
            ret = convert_loading(ret, self.unit_loading, unit)

        # Select required points
        if max_range is None or min_range is None:
            return ret
        else:
            if min_range is None:
                min_range = 0
            if max_range is None:
                max_range = max(ret)
            return [x for x in ret if (min_range <= x and x <= max_range)]

    def other_data(self, key, min_range=None, max_range=None, branch=None):
        """
        Returns adsorption enthalpy points as an array

        Parameters
        ----------
        key : str
            Key in the isotherm DataFrame containing the data to select
        unit : str, optional
            Unit in which the data should be returned. If None
            it defaults to which data unit the isotherm is currently in
        min_range : float, optional
            The lower limit for the data to select.
        max_range : float, optional
            The higher limit for the data to select.
        branch : {None, 'ads', 'des'}
            The branch of the data to return. If None, returns entire
            dataset

        Returns
        -------
        array
            The data slice corresponding to the parameters passesd
        """
        if key in self.other_keys:
            ret = self.data(branch=branch).loc[:, key].values

            # Select required points
            if max_range is None or min_range is None:
                return ret
            else:
                if min_range is None:
                    min_range = 0
                if max_range is None:
                    max_range = max(ret)
                return [x for x in ret if (min_range <= x and x <= max_range)]
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
                   unit=None,
                   branch='ads',
                   interp_fill=None,
                   interpolation_type='linear'):
        """
        Interpolate isotherm to compute loading at any pressure P.

        Parameters
        ----------
        pressure : float or array
            pressure at which to compute loading
        unit : str
            Unit the pressure is returned in. If None, it defaults to
            internal isotherm units.
        branch : {'ads','des'}
            The branch the interpolation takes into account.
        interp_fill : float
            Maximum value until which the interpolation is done. If blank,
            interpolation will not predict outside the bounds of data.
        interpolation_type : str
            The type of scipi.interp1d used: `linear`, `nearest`, `zero`,
            `slinear`, `quadratic`, `cubic`. It defaults to `linear`.

        Returns
        -------
        float or array
            predicted loading at pressure P
        """
        # Check to see if interpolator is already generated
        if self.interp_fun is None or \
                self.interp_branch != branch or  \
                self.interp_kind != interpolation_type or \
                self.interp_fill != interp_fill:

            #: the branch the internal interpolator is branched on
            self.interp_branch = branch
            #: the kind of interpolator in the internal interpolator
            self.interp_kind = interpolation_type
            #: value of loading to assume beyond highest pressure in the data
            self.interp_fill = interp_fill

            # Generate the interpolator object
            if self.interp_fill is None:
                self.interp_fun = interp1d(self.pressure(branch=branch),
                                           self.loading(branch=branch),
                                           kind=interpolation_type)
            else:
                self.interp_fun = interp1d(self.pressure(branch=branch),
                                           self.loading(branch=branch),
                                           fill_value=self.interp_fill, bounds_error=False,
                                           kind=interpolation_type)

        # Now interpolate and return the value
        if unit is None:
            return self.interp_fun(pressure)
        else:
            return convert_loading(self.interp_fun(pressure), self.unit_loading, unit)

    def pressure_at(self, loading, unit=None, branch='ads'):
        """
        Interpolate isotherm to compute pressure at any loading n.

        Parameters
        ----------
        loading : float
            loading at which to compute pressure
        unit : str, optional
            Unit in which the data should be returned. If None
            it defaults to which data unit the isotherm is currently in
        branch : {'ads', 'des'}
            The branch of the use for calculation. Defaults to adsorption.

        Returns
        -------
        float
            predicted pressure at loading n
        """

        # TODO implement
        raise NotImplementedError

    def spreading_pressure(self, pressure, interp_fill=None):
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

        Returns
        -------
        float
            spreading pressure, :math:`\\Pi`
        """
        # throw exception if interpolating outside the range.
        if (self.interp_fill is None) & \
                (pressure > self._data[self.pressure_key].max()):
            raise CalculationError("""
            To compute the spreading pressure at this bulk
            adsorbate pressure, we would need to extrapolate the isotherm since this
            pressure is outside the range of the highest pressure in your
            pure-component isotherm data, %f.

            At present, your InterpolatorIsotherm object is set to throw an
            exception when this occurs, as we do not have data outside this
            pressure range to characterize the isotherm at higher pressures.

            Option 1: fit an analytical model to extrapolate the isotherm
            Option 2: pass a `interp_fill` to the construction of the
                InterpolatorIsotherm object. Then, InterpolatorIsotherm will
                assume that the uptake beyond pressure %f is equal to
                `interp_fill`. This is reasonable if your isotherm data exhibits
                a plateau at the highest pressures.
            Option 3: Go back to the lab or computer to collect isotherm data
                at higher pressures. (Extrapolation can be dangerous!)"""
                                   % (self._data[self.pressure_key].max(),
                                      self._data[self.pressure_key].max()))

        # Get all data points that are at nonzero pressures
        pressures = self._data[self.pressure_key].values[
            self._data[self.pressure_key].values != 0.0]
        loadings = self._data[self.loading_key].values[
            self._data[self.pressure_key].values != 0.0]

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
            slope = (self.loading_at(pressure) - loadings[n_points - 1]) / (
                pressure - pressures[n_points - 1])
            intercept = loadings[n_points - 1] - \
                slope * pressures[n_points - 1]
            area += slope * (pressure - pressures[n_points - 1]) + intercept * \
                numpy.log(pressure / pressures[n_points - 1])

            return area
