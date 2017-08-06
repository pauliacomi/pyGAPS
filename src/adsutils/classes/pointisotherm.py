"""
This module contains the main class that describes an isotherm through discrete points
"""

__author__ = 'Paul A. Iacomi'

import copy
import hashlib

import pandas

import adsutils

from . import SAMPLE_LIST
from ..graphing.isothermgraphs import plot_iso
from .gas import saturation_pressure_at_temperature
from .modelisotherm import ModelIsotherm

_LOADING_UNITS = {"mmol": 0.001, "cm3 STP": 4.461e-5}
_PRESSURE_UNITS = {"bar": 100000, "Pa": 1, "atm": 101325}

_MATERIAL_MODE = ["mass", "volume"]
_PRESSURE_MODE = ["absolute", "relative"]

_ADS_DES_CHECK = "des_check"


class PointIsotherm(object):
    '''
    Class which contains the points from an adsorption isotherm and microcalorimetry
    '''

    def __init__(self, isotherm_data,
                 loading_key=None,
                 pressure_key=None,
                 other_keys=None,  # TODO make this general
                 mode_adsorbent="mass",
                 mode_pressure="absolute",
                 unit_loading="mmol",
                 unit_pressure="bar",
                 **isotherm_parameters):
        '''
        Instatiation of the class from a DataFrame so it can be easily referenced

        :param data: DataFrame containing isotherm and enthalpy datapoints
        :param info: Dictionary containing all experiment parameters
        :param loading_key: String key for loading column in df
        :param pressure_key: String key for pressure column in df
        :param enthalpy_key: String key for enthalpy column in df

        :param mode_adsorbent: Mode for the adsorbent considered: per mass or per volume
        :param mode_pressure: Mode for the pressure

        :param unit_loading: Unit for the amount of gas loaded
        :param unit_pressure: Unit for the pressure

        :return: self
        :rtype: PointIsotherm
        '''
        # Start construction process
        self._instantiated = False

        # Checks
        if any(k not in isotherm_parameters
                for k in ('sample_name', 'sample_batch', 't_exp', 'gas')):
            raise Exception(
                "Isotherm MUST have the following information in the properties dictionary:"
                "'sample_name', 'sample_batch', 't_exp', 'gas'")

        if None in [loading_key, pressure_key]:
            raise Exception(
                "Pass loading_key, pressure_key as sample_names of the loading,"
                " pressure and enthalpy columns in the DataFrame, to the constructor.")

        if mode_adsorbent is None or mode_pressure is None:
            raise Exception("One of the modes is not specified. See viable"
                            "modes in _MATERIAL_MODE and _PRESSURE_MODE")

        if mode_adsorbent not in _MATERIAL_MODE:
            raise Exception("Mode selected for adsorbent is not an option. See viable"
                            "modes in _MATERIAL_MODE")

        if mode_pressure not in _PRESSURE_MODE:
            raise Exception("Mode selected for pressure is not an option. See viable"
                            "modes in _PRESSURE_MODE")

        if unit_loading is None or unit_pressure is None:
            raise Exception("One of the units is not specified. See viable"
                            "units in _LOADING_UNITS and _PRESSURE_UNITS")

        if unit_loading not in _LOADING_UNITS:
            raise Exception("Unit selected for loading is not an option. See viable"
                            "units in _LOADING_UNITS")

        if unit_pressure not in _PRESSURE_UNITS:
            raise Exception("Unit selected for pressure is not an option. See viable"
                            "units in _PRESSURE_UNITS")

        #: Pandas DataFrame to store the data
        self._data = isotherm_data

        #: Name of column in the dataframe that contains adsorbed amount
        self.loading_key = loading_key
        #: Name of column in the dataframe that contains pressure
        self.pressure_key = pressure_key

        #: List of column in the dataframe that contains other points
        self.other_keys = other_keys

        #: mode for the adsorbent
        self.mode_adsorbent = mode_adsorbent
        #: mode for the pressure
        self.mode_pressure = mode_pressure
        #: units for loading
        self.unit_loading = unit_loading
        #: units for pressure
        self.unit_pressure = unit_pressure

        #: Must-have properties of the isotherm
        if 'id' not in isotherm_parameters:
            self.id = None
        else:
            self.id = isotherm_parameters.get('id')

        #: Isotherm sample sample_name
        self.sample_name = isotherm_parameters.get('sample_name')
        #: Isotherm sample sample_batch
        self.sample_batch = isotherm_parameters.get('sample_batch')
        #: Isotherm experimental temperature
        self.t_exp = isotherm_parameters.get('t_exp')
        #: Isotherm gas used
        self.gas = isotherm_parameters.get('gas')

        #: Good-to-have properties of the isotherm
        #: Isotherm experiment date
        self.date = isotherm_parameters.get('date')
        #: Isotherm sample activation temperature
        self.t_act = isotherm_parameters.get('t_act')
        #: Isotherm lab
        self.lab = isotherm_parameters.get('lab')
        #: Isotherm comments
        self.comment = isotherm_parameters.get('comment')

        # Other properties
        #: Isotherm user
        self.user = isotherm_parameters.get('user')
        #: Isotherm project
        self.project = isotherm_parameters.get('project')
        #: Isotherm machine used
        self.machine = isotherm_parameters.get('machine')
        #: Isotherm physicality (real or simulation)
        self.is_real = isotherm_parameters.get('is_real')
        #: Isotherm type (calorimetry/isotherm)
        self.exp_type = isotherm_parameters.get('exp_type')

        self.other_properties = isotherm_parameters.get('other_properties')

        # Split the data in adsorption/desorption
        self._data = self._splitdata(self._data)

        # Now that all data has been saved, generate the unique id if needed
        if self.id is None:
            # Generate the unique id using md5
            sha_hasher = hashlib.md5(
                adsutils.isotherm_to_json(self).encode('utf-8'))
            self.id = sha_hasher.hexdigest()

        self._instantiated = True

    def __setattr__(self, name, value):
        """
        We overlad the usual class setter to make sure that the id is always
        representative of the data inside the isotherm

        The '_instantiated' attribute gets set to true after isotherm __init__
        From then afterwards, each call to modify the isotherm properties
        recalculates the md5 hash.
        This is done to ensure uniqueness and also to allow isotherm objects to
        be easily compared to each other.
        """
        object.__setattr__(self, name, value)

        if self._instantiated and name not in ['id', '_instantiated']:
            # Generate the unique id using md5
            self.id = None
            md_hasher = hashlib.md5(
                adsutils.isotherm_to_json(self).encode('utf-8'))
            self.id = md_hasher.hexdigest()

    def __eq__(self, other_isotherm):
        """
        We overload the equality operator of the isotherm. Since id's are unique and
        representative of the data inside the isotherm, all we need to ensure equality
        is to compare the two hashes of the isotherms.
        """

        return self.id == other_isotherm.id

    #: Figure out the adsorption and desorption branches
    def _splitdata(self, _data):
        '''
        Splits isotherm data into an adsorption and desorption part and adds a column to mark it
        '''
        increasing = _data.loc[:, self.pressure_key].diff().fillna(0) < 0
        increasing.rename(_ADS_DES_CHECK, inplace=True)

        return pandas.concat([_data, increasing], axis=1)


##########################################################
#   Conversion functions

    def convert_loading(self, unit_to):
        '''
        Converts the loading of the isotherm from one unit to another
        '''

        if unit_to not in _LOADING_UNITS:
            raise Exception("Unit selected for loading is not an option. See viable"
                            "models in _LOADING_UNITS")

        if unit_to == self.unit_loading:
            print("Unit is the same, no changes made")
            return

        self._data[self.loading_key] = self._data[self.loading_key].apply(
            lambda x: x * _LOADING_UNITS[self.unit_loading] / _LOADING_UNITS[unit_to])

        self.unit_loading = unit_to

        return

    def convert_pressure(self, unit_to):
        '''
        Converts the pressure values of the isotherm from one unit to another
        '''

        if unit_to not in _PRESSURE_UNITS:
            raise Exception("Unit selected for loading is not an option. See viable"
                            "models in _PRESSURE_UNITS")

        if unit_to == self.unit_pressure:
            print("Unit is the same, no changes made")
            return

        self._data[self.pressure_key] = self._data[self.pressure_key].apply(
            lambda x: x * _PRESSURE_UNITS[self.unit_pressure] / _PRESSURE_UNITS[unit_to])

        self.unit_pressure = unit_to

        return

    def convert_pressure_mode(self, mode_pressure):
        '''
        Converts the pressure values of the isotherm from one unit to another
        '''

        if mode_pressure not in _PRESSURE_MODE:
            raise Exception("Mode selected for pressure is not an option. See viable"
                            "models in _PRESSURE_MODE")

        if mode_pressure == self.mode_pressure:
            print("Mode is the same, no changes made")
            return

        # TODO Make sure that if the division is made in the correct units, currently only bar

        if mode_pressure == "absolute":
            self._data[self.pressure_key] = self._data[self.pressure_key].apply(
                lambda x: x * saturation_pressure_at_temperature(self.t_exp, self.gas))
        elif mode_pressure == "relative":
            self._data[self.pressure_key] = self._data[self.pressure_key].apply(
                lambda x: x / saturation_pressure_at_temperature(self.t_exp, self.gas))

        self.mode_pressure = mode_pressure

        return

    def convert_adsorbent_mode(self, mode_adsorbent):
        '''
        Converts the pressure values of the isotherm from one unit to another
        '''

        # Syntax checks
        if mode_adsorbent not in _MATERIAL_MODE:
            raise Exception("Mode selected for adsorbent is not an option. See viable"
                            "models in _MATERIAL_MODE")

        if mode_adsorbent == self.mode_adsorbent:
            print("Mode is the same, no changes made")
            return

        # Checks to see if sample exists in master list
        if not any(self.sample_name == sample.sample_name and self.sample_batch == sample.sample_batch
                   for sample in SAMPLE_LIST):
            raise Exception("Sample %s %s does not exist in sample list. "
                            "First populate adsutils.SAMPLE_LIST "
                            "with desired sample class"
                            % (self.sample_name, self.sample_batch))

        sample = [sample for sample in SAMPLE_LIST
                  if self.sample_name == sample.sample_name and self.sample_batch == sample.sample_batch]

        if len(sample) > 1:
            raise Exception("More than one sample %s %s found in sample list. "
                            "Samples must be unique on (sample_name + sample_batch)"
                            % (self.sample_name, self.sample_batch))

        try:
            density = sample[0].properties["density"]
        except:
            raise Exception("The density entry was not found in the "
                            "sample.properties dictionary "
                            "for sample %s %s"
                            % (self.sample_name, self.sample_batch))

        if mode_adsorbent == "volume":
            self._data[self.loading_key] = self._data[self.loading_key].apply(
                lambda x: x * density)
        elif mode_adsorbent == "mass":
            self._data[self.loading_key] = self._data[self.loading_key].apply(
                lambda x: x / density)

        self.mode_adsorbent = mode_adsorbent

        return

###########################################################
#   Info functions

    def print_info(self, logarithmic=False):
        '''
        Prints a short summary of all the isotherm parameters and a graph

        '''

        if self.is_real:
            print("Experimental isotherm")
        else:
            print("Simulated isotherm")

        print("Sample:", self.sample_name)
        print("sample_batch:", self.sample_batch)
        print("Experiment type:", self.exp_type)
        print("Gas used:", self.gas)
        print("Experiment date:", self.date)
        print("Machine:", self.machine)
        print("User:", self.user)
        print("Activation temperature:", self.t_act, "°C")
        print("Experiment temperature:", self.t_exp, "K")

        print("\n")
        print("Experiment comments:", self.comment)

        if 'enthalpy_key' in self.other_keys:
            plot_type = 'iso-enth'
        else:
            plot_type = 'isotherm'

        plot_iso([self], plot_type=plot_type, branch=["ads", "des"],
                 logarithmic=logarithmic, color=True, fig_title=self.gas)

        return


###########################################################
#   Modelling functions

    def get_model_isotherm(self, model):
        '''
        Returns a pyiast modelled isotherm based on the parent isotherm

        '''

        model_isotherm = ModelIsotherm(self.adsdata(),
                                       loading_key=self.loading_key,
                                       pressure_key=self.pressure_key,
                                       model=model)

        point_model_isotherm = copy.deepcopy(self)
        point_model_isotherm.type = "sym"

        # Generate isotherm based on loading
        sym_loading = point_model_isotherm.adsdata().apply(
            lambda x: model_isotherm.loading(
                x[point_model_isotherm.pressure_key]),
            axis=1)  # yaxis - downwards
        point_model_isotherm.adsdata(
        )[point_model_isotherm.loading_key] = sym_loading

        return point_model_isotherm


##########################################################
#   Functions that return parts of the isotherm data

    def data(self):
        '''Returns all data'''
        return self._data.drop(_ADS_DES_CHECK, axis=1)

    def adsdata(self):
        '''Returns adsorption part of data'''
        return self._data.loc[~self._data[_ADS_DES_CHECK]].drop(_ADS_DES_CHECK, axis=1)

    def desdata(self):
        '''Returns desorption part of data'''
        return self._data.loc[self._data[_ADS_DES_CHECK]].drop(_ADS_DES_CHECK, axis=1)

    def has_ads(self):
        '''
        Returns if the isotherm has an adsorption branch
        '''
        if self.adsdata() is None:
            return False
        else:
            return True

    def has_des(self):
        '''
        Returns if the isotherm has an desorption branch
        '''
        if self.desdata() is None:
            return False
        else:
            return True

    def pressure_ads(self, max_range=None):
        '''
        Returns adsorption pressure points as an array
        '''
        if self.adsdata() is None:
            return None
        else:
            ret = self.adsdata().loc[:, self.pressure_key].values
            if max_range is None:
                return ret
            else:
                return [x for x in ret if x < max_range]

    def loading_ads(self, max_range=None):
        '''
        Returns adsorption amount adsorbed points as an array
        '''
        if self.adsdata() is None:
            return None
        else:
            ret = self.adsdata().loc[:, self.loading_key].values
            if max_range is None:
                return ret
            else:
                return [x for x in ret if x < max_range]

    def other_key_ads(self, key, max_range=None):
        '''
        Returns adsorption enthalpy points as an array
        '''
        if self.adsdata() is None:
            return None
        elif key not in self.other_keys:
            return None
        else:
            ret = self.adsdata().loc[:, self.other_keys.get(key)].values
            if max_range is None:
                return ret
            else:
                return [x for x in ret if x < max_range]

    def pressure_des(self, max_range=None):
        '''
        Returns desorption pressure points as an array
        '''
        if self.desdata() is None:
            return None
        else:
            ret = self.desdata().loc[:, self.pressure_key].values
            if max_range is None:
                return ret
            else:
                return [x for x in ret if x < max_range]

    def loading_des(self, max_range=None):
        '''
        Returns desorption amount adsorbed points as an array
        '''
        if self.desdata() is None:
            return None
        else:
            ret = self.desdata().loc[:, self.loading_key].values
            if max_range is None:
                return ret
            else:
                return [x for x in ret if x < max_range]

    def other_key_des(self, key, max_range=None):
        '''
        Returns desorption key points as an array
        '''
        if self.desdata() is None:
            return None
        elif key not in self.other_keys:
            return None
        else:
            ret = self.desdata().loc[:, self.other_keys.get(key)].values
            if max_range is None:
                return ret
            else:
                return [x for x in ret if x < max_range]

    def pressure_all(self):
        '''
        Returns all pressure points as an array
        '''
        return self._data.loc[:, self.pressure_key].values

    def loading_all(self):
        '''
        Returns all amount adsorbed points as an array
        '''
        return self._data.loc[:, self.loading_key].values

    def other_key_all(self, key):
        '''
        Returns all enthalpy points as an array
        '''
        if self.other_keys.get(key) in self._data.columns:
            return self._data.loc[:, self.other_keys.get(key)].values
        else:
            return None
