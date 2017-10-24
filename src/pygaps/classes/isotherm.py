"""
This module contains the main class that describes an isotherm
"""

import pandas

from ..classes.adsorbate import _PRESSURE_MODE
from ..classes.sample import _MATERIAL_MODE
from ..utilities.exceptions import ParameterError
from ..utilities.unit_converter import _LOADING_UNITS
from ..utilities.unit_converter import _MASS_UNITS
from ..utilities.unit_converter import _PRESSURE_UNITS
from ..utilities.unit_converter import _VOLUME_UNITS


class Isotherm(object):
    """
    Class which contains the general data for an isotherm, real or model

    The isotherm class is the parent class that both PointIsotherm and
    ModelIsotherm inherit. It is designed to contain the information about
    an isotherm, such as material, adsorbate, data units etc., but without
    any of the data itself.

    Parameters
    ----------
    basis_adsorbent : str, optional
        Whether the adsorption is read in terms of either 'per volume'
        or 'per mass'.
    unit_adsorbent : str, optional
        Unit of loading.
    basis_loading : str, optional
        Loading basis.
    unit_loading : str, optional
        Unit of loading.
    mode_pressure : str, optional
        The pressure mode, either absolute pressures or relative in
        the form of p/p0.
    unit_pressure : str, optional
        Unit of pressure.
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

        The info dictionary must contain an entry for 'sample_name',
        'sample_batch', 'adsorbate' and 't_exp'

    Notes
    -----

    The class is also used to prevent duplication of code within the child
    classes, by calling the common inherited function before any other specific
    implementation additions.

    The minimum arguments required to instantiate the class are
    'sample_name', 'sample_batch', 't_exp', 'adsorbate'. Pass these values in
    the ``**isotherm_parameters`` dictionary
    """

    def __init__(self,
                 loading_key=None,
                 pressure_key=None,

                 basis_adsorbent="mass",
                 unit_adsorbent="g",
                 basis_loading="molar",
                 unit_loading="mmol",
                 mode_pressure="absolute",
                 unit_pressure="bar",

                 **isotherm_parameters):
        """
        Instantiation is done by passing a dictionary with the parameters,
        as well as the info about units, modes and data columns.
        """

        # Checks
        if any(k not in isotherm_parameters
               for k in ('sample_name', 'sample_batch', 't_exp', 'adsorbate')):
            raise ParameterError(
                "Isotherm MUST have the following information in the properties dictionary:"
                "'sample_name', 'sample_batch', 't_exp', 'adsorbate'")

        # Basis and mode
        if basis_adsorbent is None or mode_pressure is None or basis_loading is None:
            raise ParameterError(
                "One of the modes or bases is not specified.")

        if basis_adsorbent not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for adsorbent is not an option. See viable"
                "values: {0}".format(_MATERIAL_MODE))

        if basis_loading not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for loading is not an option. See viable"
                "values: {0}".format(_MATERIAL_MODE))

        if mode_pressure not in _PRESSURE_MODE:
            raise ParameterError(
                "Mode selected for pressure is not an option. See viable"
                "values: {0}".format(_PRESSURE_MODE))

        # Units
        if unit_loading is None or unit_pressure is None or unit_adsorbent is None:
            raise ParameterError(
                "One of the units is not specified.")

        if unit_loading not in _LOADING_UNITS:
            raise ParameterError(
                "Unit selected for loading is not an option. See viable"
                "values: {0}".format(_LOADING_UNITS))

        if unit_pressure not in _PRESSURE_UNITS:
            raise ParameterError(
                "Unit selected for pressure is not an option. See viable"
                "values: {0}".format(_PRESSURE_UNITS))

        if unit_adsorbent not in _VOLUME_UNITS and unit_adsorbent not in _MASS_UNITS:
            raise ParameterError(
                "Unit selected for adsorbent is not an option. See viable"
                "values: {0} {1}".format(_VOLUME_UNITS,  _MASS_UNITS))

        # Column titles
        if None in [loading_key, pressure_key]:
            raise ParameterError(
                "Pass loading_key and pressure_key, the names of the loading and"
                " pressure columns in the DataFrame, to the constructor.")

        #: basis for the adsorbent
        self.basis_adsorbent = str(basis_adsorbent)
        #: unit for the adsorbent
        self.unit_adsorbent = str(unit_adsorbent)
        #: basis for the loading
        self.basis_loading = str(basis_loading)
        #: units for loading
        self.unit_loading = str(unit_loading)
        #: mode for the pressure
        self.mode_pressure = str(mode_pressure)
        #: units for pressure
        self.unit_pressure = str(unit_pressure)

        # Save column names
        #: Name of column in the dataframe that contains adsorbed amount
        self.loading_key = loading_key

        #: Name of column in the dataframe that contains pressure
        self.pressure_key = pressure_key

        # Must-have properties of the isotherm
        if 'id' not in isotherm_parameters:
            self.id = None
        else:
            self.id = isotherm_parameters.pop('id', None)

        #: Isotherm material name
        self.sample_name = str(isotherm_parameters.pop('sample_name', None))
        #: Isotherm material batch
        self.sample_batch = str(isotherm_parameters.pop('sample_batch', None))
        #: Isotherm experimental temperature
        self.t_exp = float(isotherm_parameters.pop('t_exp', None))
        #: Isotherm adsorbate used
        self.adsorbate = str(isotherm_parameters.pop('adsorbate', None))

        # Good-to-have properties of the isotherm
        #: Isotherm experiment date
        self.date = None
        date = isotherm_parameters.pop('date', None)
        if date:
            self.date = str(date)

        #: Isotherm sample activation temperature
        self.t_act = None
        t_act = isotherm_parameters.pop('t_act', None)
        if t_act:
            self.t_act = float(t_act)

        #: Isotherm lab
        self.lab = None
        lab = isotherm_parameters.pop('lab', None)
        if lab:
            self.lab = str(lab)

        #: Isotherm comments
        self.comment = None
        comment = isotherm_parameters.pop('comment', None)
        if comment:
            self.comment = str(comment)

        #
        # Other properties
        #: Isotherm user
        self.user = None
        user = isotherm_parameters.pop('user', None)
        if user:
            self.user = str(user)

        #: Isotherm project
        self.project = None
        project = isotherm_parameters.pop('project', None)
        if project:
            self.project = str(project)

        #: Isotherm machine used
        self.machine = None
        machine = isotherm_parameters.pop('machine', None)
        if machine:
            self.machine = str(machine)

        #: Isotherm physicality (real or simulation)
        self.is_real = None
        is_real = isotherm_parameters.pop('is_real', None)
        if is_real:
            self.is_real = bool(is_real)

        #: Isotherm type (calorimetry/isotherm)
        self.exp_type = None
        exp_type = isotherm_parameters.pop('exp_type', None)
        if exp_type:
            self.exp_type = str(exp_type)

        # Save the rest of the properties as an extra dict
        # now that the named properties were taken out of
        #: Other properties of the isotherm
        self.other_properties = isotherm_parameters

    ###########################################################
    #   Info functions

    def __str__(self):
        '''
        Prints a short summary of all the isotherm parameters
        '''
        string = ""

        if self.is_real:
            string += ("Experimental isotherm" + '\n')
        else:
            string += ("Simulated isotherm" + '\n')

        # Required
        string += ("Material: " + str(self.sample_name) + '\n')
        string += ("Batch: " + str(self.sample_batch) + '\n')
        string += ("Adsorbate used: " + str(self.adsorbate) + '\n')
        string += ("Isotherm temperature: " + str(self.t_exp) + "K" + '\n')

        if self.exp_type:
            string += ("Isotherm type: " + str(self.exp_type) + '\n')
        if self.date:
            string += ("Isotherm date: " + str(self.date) + '\n')
        if self.machine:
            string += ("Machine: " + str(self.machine) + '\n')
        if self.user:
            string += ("User: " + str(self.user) + '\n')
        if self.t_act:
            string += ("Activation temperature: " +
                       str(self.t_act) + "°C" + '\n')
        if self.comment:
            string += ("Isotherm comments: " + str(self.comment) + '\n')

        # Units/basis
        string += ("Units: \n")
        string += ("Unit for loading: " + str(self.unit_loading) +
                   "/" + str(self.unit_adsorbent) + '\n')
        if self.mode_pressure == 'relative':
            string += ("Relative pressure \n")
        else:
            string += ("Unit for pressure: " + str(self.unit_pressure) + '\n')

        string += ("Other properties: \n")
        for prop in self.other_properties:
            string += (prop + ": " + str(self.other_properties[prop]) + '\n')

        return string

    def to_dict(self):
        """
        Returns a dictionary of the isotherm class
        Is the same dictionary that was used to create it

        Returns
        -------
        dict
            dictionary of all parameters
        """
        parameter_dict = {}

        # Get the named properties
        if self.id:
            parameter_dict.update({'id': self.id})
        if self.sample_name:
            parameter_dict.update({'sample_name': self.sample_name})
        if self.sample_batch:
            parameter_dict.update({'sample_batch': self.sample_batch})
        if self.t_exp:
            parameter_dict.update({'t_exp': self.t_exp})
        if self.adsorbate:
            parameter_dict.update({'adsorbate': self.adsorbate})

        if self.date:
            parameter_dict.update({'date': str(self.date)})
        if self.t_act:
            parameter_dict.update({'t_act': self.t_act})
        if self.lab:
            parameter_dict.update({'lab': self.lab})
        if self.comment:
            parameter_dict.update({'comment': self.comment})

        if self.user:
            parameter_dict.update({'user': self.user})
        if self.project:
            parameter_dict.update({'project': self.project})
        if self.machine:
            parameter_dict.update({'machine': self.machine})
        if self.is_real:
            parameter_dict.update({'is_real': self.is_real})
        if self.exp_type:
            parameter_dict.update({'exp_type': self.exp_type})

        # Get the units
        parameter_dict.update({'pressure_unit': self.unit_pressure})
        parameter_dict.update({'pressure_mode': self.mode_pressure})
        parameter_dict.update({'adsorbent_unit': self.unit_adsorbent})
        parameter_dict.update({'adsorbent_basis': self.basis_adsorbent})
        parameter_dict.update({'loading_unit': self.unit_loading})
        parameter_dict.update({'loading_basis': self.basis_loading})

        # Now add the rest
        parameter_dict.update(self.other_properties)

        return parameter_dict

    # Figure out the adsorption and desorption branches
    def _splitdata(self, _data):
        """
        Splits isotherm data into an adsorption and desorption part and
        adds a column to mark the transition between the two
        """
        increasing = _data.loc[:, self.pressure_key].diff().fillna(0) < 0
        increasing.rename('check', inplace=True)

        return pandas.concat([_data, increasing], axis=1)
