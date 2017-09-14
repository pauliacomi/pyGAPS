"""
This module contains the main class that describes an isotherm
"""

from ..utilities.exceptions import ParameterError
from ..utilities.unit_converter import _LOADING_UNITS
from ..utilities.unit_converter import _PRESSURE_UNITS
from ..classes.adsorbate import _PRESSURE_MODE
from ..classes.sample import _MATERIAL_MODE


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
                 basis_adsorbent="mass",
                 mode_pressure="absolute",
                 unit_loading="mmol",
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

        if basis_adsorbent is None or mode_pressure is None:
            raise ParameterError(
                "One of the modes is not specified. See viable"
                "modes in _MATERIAL_MODE and _PRESSURE_MODE")

        if basis_adsorbent not in _MATERIAL_MODE:
            raise ParameterError(
                "Mode selected for adsorbent is not an option. See viable"
                "modes in _MATERIAL_MODE")

        if mode_pressure not in _PRESSURE_MODE:
            raise ParameterError(
                "Mode selected for pressure is not an option. See viable"
                "modes in _PRESSURE_MODE")

        if unit_loading is None or unit_pressure is None:
            raise ParameterError(
                "One of the units is not specified. See viable"
                "units in _LOADING_UNITS and _PRESSURE_UNITS")

        if unit_loading not in _LOADING_UNITS:
            raise ParameterError(
                "Unit selected for loading is not an option. See viable"
                "units in _LOADING_UNITS")

        if unit_pressure not in _PRESSURE_UNITS:
            raise ParameterError(
                "Unit selected for pressure is not an option. See viable"
                "units in _PRESSURE_UNITS")

        #: basis for the adsorbent
        self.basis_adsorbent = str(basis_adsorbent)
        #: mode for the pressure
        self.mode_pressure = str(mode_pressure)
        #: units for loading
        self.unit_loading = str(unit_loading)
        #: units for pressure
        self.unit_pressure = str(unit_pressure)

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
        self.date = str(isotherm_parameters.pop('date', None))
        #: Isotherm sample activation temperature
        self.t_act = float(isotherm_parameters.pop('t_act', None))
        #: Isotherm lab
        self.lab = str(isotherm_parameters.pop('lab', None))
        #: Isotherm comments
        self.comment = str(isotherm_parameters.pop('comment', None))

        # Other properties
        #: Isotherm user
        self.user = str(isotherm_parameters.pop('user', None))
        #: Isotherm project
        self.project = str(isotherm_parameters.pop('project', None))
        #: Isotherm machine used
        self.machine = str(isotherm_parameters.pop('machine', None))
        #: Isotherm physicality (real or simulation)
        self.is_real = bool(isotherm_parameters.pop('is_real', None))
        #: Isotherm type (calorimetry/isotherm)
        self.exp_type = str(isotherm_parameters.pop('exp_type', None))

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

        string += ("Material:" + str(self.sample_name) + '\n')
        string += ("Sample Batch:" + str(self.sample_batch) + '\n')
        string += ("Isotherm type:" + str(self.exp_type) + '\n')
        string += ("Adsorbate used:" + str(self.adsorbate) + '\n')
        string += ("Isotherm date:" + str(self.date) + '\n')
        string += ("Machine:" + str(self.machine) + '\n')
        string += ("User:" + str(self.user) + '\n')
        string += ("Activation temperature:" + str(self.t_act) + "°C" + '\n')
        string += ("Isotherm temperature:" + str(self.t_exp) + "K" + '\n')
        string += ("Isotherm comments:" + str(self.comment) + '\n')

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

        # Get the named properties
        parameters_dict = {
            'id': self.id,

            'sample_name': self.sample_name,
            'sample_batch': self.sample_batch,
            't_exp': self.t_exp,
            'adsorbate': self.adsorbate,

            'date': str(self.date),
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
