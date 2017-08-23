"""
This module contains the main class that describes an isotherm
"""

__author__ = 'Paul A. Iacomi'


class Isotherm(object):
    '''
    Class which contains the general data for an isotherm, real or model
    '''

    _LOADING_UNITS = {"mol": 1, "mmol": 0.001, "cm3 STP": 4.461e-5}
    _PRESSURE_UNITS = {"bar": 100000, "Pa": 1, "atm": 101325}

    _MATERIAL_MODE = ["mass", "volume"]
    _PRESSURE_MODE = ["absolute", "relative"]

    def __init__(self,
                 loading_key,
                 pressure_key,
                 mode_adsorbent="mass",
                 mode_pressure="absolute",
                 unit_loading="mmol",
                 unit_pressure="bar",
                 **isotherm_parameters):

        # Checks
        if None in [loading_key, pressure_key]:
            raise Exception(
                "Pass loading_key and pressure_key, the names of the loading and"
                " pressure columns in the DataFrame, to the constructor.")

        if any(k not in isotherm_parameters
               for k in ('sample_name', 'sample_batch', 't_exp', 'gas')):
            raise Exception(
                "Isotherm MUST have the following information in the properties dictionary:"
                "'sample_name', 'sample_batch', 't_exp', 'gas'")

        if mode_adsorbent is None or mode_pressure is None:
            raise Exception("One of the modes is not specified. See viable"
                            "modes in _MATERIAL_MODE and _PRESSURE_MODE")

        if mode_adsorbent not in self._MATERIAL_MODE:
            raise Exception("Mode selected for adsorbent is not an option. See viable"
                            "modes in _MATERIAL_MODE")

        if mode_pressure not in self._PRESSURE_MODE:
            raise Exception("Mode selected for pressure is not an option. See viable"
                            "modes in _PRESSURE_MODE")

        if unit_loading is None or unit_pressure is None:
            raise Exception("One of the units is not specified. See viable"
                            "units in _LOADING_UNITS and _PRESSURE_UNITS")

        if unit_loading not in self._LOADING_UNITS:
            raise Exception("Unit selected for loading is not an option. See viable"
                            "units in _LOADING_UNITS")

        if unit_pressure not in self._PRESSURE_UNITS:
            raise Exception("Unit selected for pressure is not an option. See viable"
                            "units in _PRESSURE_UNITS")

        #: Save column names
        #: Name of column in the dataframe that contains adsorbed amount
        self.loading_key = loading_key
        #: Name of column in the dataframe that contains pressure
        self.pressure_key = pressure_key

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
            self.id = isotherm_parameters.pop('id', None)

        #: Isotherm sample sample_name
        self.sample_name = isotherm_parameters.pop('sample_name', None)
        #: Isotherm sample sample_batch
        self.sample_batch = isotherm_parameters.pop('sample_batch', None)
        #: Isotherm experimental temperature
        self.t_exp = isotherm_parameters.pop('t_exp', None)
        #: Isotherm gas used
        self.gas = isotherm_parameters.pop('gas', None)

        #: Good-to-have properties of the isotherm
        #: Isotherm experiment date
        self.date = isotherm_parameters.pop('date', None)
        #: Isotherm sample activation temperature
        self.t_act = isotherm_parameters.pop('t_act', None)
        #: Isotherm lab
        self.lab = isotherm_parameters.pop('lab', None)
        #: Isotherm comments
        self.comment = isotherm_parameters.pop('comment', None)

        # Other properties
        #: Isotherm user
        self.user = isotherm_parameters.pop('user', None)
        #: Isotherm project
        self.project = isotherm_parameters.pop('project', None)
        #: Isotherm machine used
        self.machine = isotherm_parameters.pop('machine', None)
        #: Isotherm physicality (real or simulation)
        self.is_real = isotherm_parameters.pop('is_real', None)
        #: Isotherm type (calorimetry/isotherm)
        self.exp_type = isotherm_parameters.pop('exp_type', None)

        # Save the rest of the properties as an extra dict
        # now that the named properties were taken out of
        self.other_properties = isotherm_parameters

    ###########################################################
    #   Info functions

    def print_info(self):
        '''
        Prints a short summary of all the isotherm parameters
        '''

        if self.is_real:
            print("Experimental isotherm")
        else:
            print("Simulated isotherm")

        print("Material:", self.sample_name)
        print("Sample Batch:", self.sample_batch)
        print("Isotherm type:", self.exp_type)
        print("Gas used:", self.gas)
        print("Isotherm date:", self.date)
        print("Machine:", self.machine)
        print("User:", self.user)
        print("Activation temperature:", self.t_act, "°C")
        print("Isotherm temperature:", self.t_exp, "K")

        print("\n")
        print("Isotherm comments:", self.comment)

        return

    def to_dict(self):
        """Returns a dictionary with the isotherm parameters"""

        # Get the named properties
        parameters_dict = {
            'id': self.id,

            'sample_name': self.sample_name,
            'sample_batch': self.sample_batch,
            't_exp': self.t_exp,
            'gas': self.gas,

            'date': self.date,
            't_act': self.t_act,
            'lab': self.lab,
            'comment': self.comment,

            'user': self.user,
            'project': self.project,
            'machine': self.machine,
            'is_real': self.is_real,
            'exp_type': self.exp_type,
        }

        # Now add the rest
        parameters_dict.update(self.other_properties)

        return parameters_dict
