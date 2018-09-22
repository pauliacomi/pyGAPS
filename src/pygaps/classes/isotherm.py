"""
This module contains the main class that describes an isotherm.
"""

import pandas

from ..utilities.exceptions import ParameterError
from ..utilities.hashgen import isotherm_to_hash
from ..utilities.unit_converter import _MATERIAL_MODE
from ..utilities.unit_converter import _PRESSURE_MODE
from ..utilities.unit_converter import _PRESSURE_UNITS


class Isotherm(object):
    """
    Class which contains the general data for an isotherm, real or model.

    The isotherm class is the parent class that both PointIsotherm and
    ModelIsotherm inherit. It is designed to contain the information about
    an isotherm, such as material, adsorbate, data units etc., but without
    any of the data itself.

    Think of this class as a extended python dictionary.

    Parameters
    ----------

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

    The class is also used to prevent duplication of code within the child
    classes, by calling the common inherited function before any other specific
    implementation additions.

    The minimum arguments required to instantiate the class are
    ``sample_name``, ``sample_batch``, ``t_exp', ``adsorbate``.
    """

    _named_params = [
        # required
        'sample_name',
        'sample_batch',
        't_exp',
        'adsorbate',

        # others
        'user',
        'machine',
        'exp_type',
        'date',
        'is_real',
        't_act',
        'lab',
        'project',
        'comment',
    ]

    _unit_params = [
        'pressure_unit',
        'pressure_mode',
        'adsorbent_unit',
        'adsorbent_basis',
        'loading_unit',
        'loading_basis',
    ]

    _reserved_params = [
        '_instantiated',
    ]

    _db_columns = ['id'] + _named_params
    _id_params = _named_params + _unit_params

##########################################################
#   Instantiation and classmethods

    def __init__(self,
                 adsorbent_basis="mass",
                 adsorbent_unit="g",
                 loading_basis="molar",
                 loading_unit="mmol",
                 pressure_mode="absolute",
                 pressure_unit="bar",

                 **isotherm_parameters):
        """
        Instantiation is done by passing a dictionary with the parameters,
        as well as the info about units, modes and data columns.
        """

        # Checks
        if any(k not in isotherm_parameters
               for k in ('sample_name', 'sample_batch', 't_exp', 'adsorbate')):
            raise ParameterError(
                "Isotherm MUST have the following properties:"
                "'sample_name', 'sample_batch', 't_exp', 'adsorbate'")

        # Basis and mode
        if adsorbent_basis is None or pressure_mode is None or loading_basis is None:
            raise ParameterError(
                "One of the modes or bases is not specified.")

        if adsorbent_basis not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for adsorbent ({}) is not an option. See viable "
                "values: {}".format(adsorbent_basis, list(_MATERIAL_MODE.keys())))

        if loading_basis not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for loading ({}) is not an option. See viable "
                "values: {}".format(loading_basis, list(_MATERIAL_MODE.keys())))

        if pressure_mode not in _PRESSURE_MODE:
            raise ParameterError(
                "Mode selected for pressure ({}) is not an option. See viable "
                "values: {}".format(pressure_mode, list(_PRESSURE_MODE.keys())))

        # Units
        if loading_unit is None or adsorbent_unit is None:
            raise ParameterError(
                "One of the units is not specified.")

        if loading_unit not in _MATERIAL_MODE[loading_basis]:
            raise ParameterError(
                "Unit selected for loading ({}) is not an option. See viable "
                "values: {}".format(loading_unit, list(_MATERIAL_MODE[loading_basis].keys())))

        if pressure_mode == 'absolute' and pressure_unit not in _PRESSURE_UNITS:
            raise ParameterError(
                "Unit selected for pressure ({}) is not an option. See viable "
                "values: {}".format(pressure_unit, list(_PRESSURE_UNITS.keys())))

        if adsorbent_unit not in _MATERIAL_MODE[adsorbent_basis]:
            raise ParameterError(
                "Unit selected for adsorbent ({}) is not an option. See viable "
                "values: {}".format(adsorbent_unit, list(_MATERIAL_MODE[loading_basis].keys())))

        #: Basis for the adsorbent.
        self.adsorbent_basis = str(adsorbent_basis)
        #: Unit for the adsorbent.
        self.adsorbent_unit = str(adsorbent_unit)
        #: Basis for the loading.
        self.loading_basis = str(loading_basis)
        #: Units for loading.
        self.loading_unit = str(loading_unit)
        #: Mode for the pressure.
        self.pressure_mode = str(pressure_mode)
        if pressure_mode == 'relative':
            #: Units for pressure.
            self.pressure_unit = None
        else:
            #: Units for pressure.
            self.pressure_unit = str(pressure_unit)

        # Must-have properties of the isotherm
        #

        # ID
        self.id = isotherm_parameters.pop('id', None)
        #: Isotherm material name.
        self.sample_name = str(isotherm_parameters.pop('sample_name', None))
        #: Isotherm material batch.
        self.sample_batch = str(isotherm_parameters.pop('sample_batch', None))
        #: Isotherm experimental temperature.
        self.t_exp = float(isotherm_parameters.pop('t_exp', None))
        #: Isotherm adsorbate used.
        self.adsorbate = str(isotherm_parameters.pop('adsorbate', None))

        # Good-to-have properties of the isotherm
        #: Isotherm experiment date.
        self.date = None
        date = isotherm_parameters.pop('date', None)
        if date:
            self.date = str(date)

        #: Isotherm sample activation temperature.
        self.t_act = None
        t_act = isotherm_parameters.pop('t_act', None)
        if t_act:
            self.t_act = float(t_act)

        #: Isotherm lab.
        self.lab = None
        lab = isotherm_parameters.pop('lab', None)
        if lab:
            self.lab = str(lab)

        #: Isotherm comments.
        self.comment = None
        comment = isotherm_parameters.pop('comment', None)
        if comment:
            self.comment = str(comment)

        #
        # Other properties
        #: Isotherm user.
        self.user = None
        user = isotherm_parameters.pop('user', None)
        if user:
            self.user = str(user)

        #: Isotherm project.
        self.project = None
        project = isotherm_parameters.pop('project', None)
        if project:
            self.project = str(project)

        #: Isotherm machine used.
        self.machine = None
        machine = isotherm_parameters.pop('machine', None)
        if machine:
            self.machine = str(machine)

        #: Isotherm physicality (real or simulation).
        self.is_real = None
        is_real = isotherm_parameters.pop('is_real', None)
        if is_real:
            self.is_real = bool(is_real)

        #: Isotherm type (calorimetry/isotherm).
        self.exp_type = None
        exp_type = isotherm_parameters.pop('exp_type', None)
        if exp_type:
            self.exp_type = str(exp_type)

        # Save the rest of the properties as an extra dict
        # now that the named properties were taken out of
        #: Other properties of the isotherm.
        for attr in isotherm_parameters:
            setattr(self, attr, isotherm_parameters[attr])

        # Finish instantiation process
        # (check if none in case its part of a Point/Model Isotherm instantiation)
        if not hasattr(self, '_instantiated'):
            self._instantiated = True
            if self.id is None:
                self._check_if_hash(True, [True])

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
        self._check_if_hash(name)

    def _check_if_hash(self, name, extra_params=[]):
        """Checks if the hash needs to be generated"""
        if getattr(self, '_instantiated', False) and name in self._id_params + extra_params:
            # Generate the unique hash
            self.id = isotherm_to_hash(self)

    def __eq__(self, other_isotherm):
        """
        We overload the equality operator of the isotherm. Since id's should be unique and
        representative of the data inside the isotherm, all we need to ensure equality
        is to compare the two hashes of the isotherms.
        """

        return self.id == other_isotherm.id

    ###########################################################
    #   Info functions

    def __str__(self):
        '''
        Prints a short summary of all the isotherm parameters.
        '''
        string = ""

        if self.is_real is True:
            string += ("Experimental isotherm" + '\n')
        elif self.is_real is False:
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
        if self.lab:
            string += ("Source: " +
                       str(self.lab) + '\n')
        if self.comment:
            string += ("Isotherm comments: " + str(self.comment) + '\n')

        # Units/basis
        string += ("Units: \n")
        string += ("\tUnit for loading: " + str(self.loading_unit) +
                   "/" + str(self.adsorbent_unit) + '\n')
        if self.pressure_mode == 'relative':
            string += ("\tRelative pressure \n")
        else:
            string += ("\tUnit for pressure: " + str(self.pressure_unit) + '\n')

        string += ("Other properties: \n")
        for prop in vars(self):
            if prop not in self._named_params + self._unit_params + self._reserved_params:
                string += ('\t' + prop + ": " + str(getattr(self, prop)) + '\n')

        return string

    def to_dict(self):
        """
        Returns a dictionary of the isotherm class
        Is the same dictionary that was used to create it.

        Returns
        -------
        dict
            Dictionary of all parameters.
        """
        parameter_dict = vars(self).copy()

        # Remove reserved parameters
        for param in self._reserved_params:
            if param in parameter_dict:
                parameter_dict.pop(param, None)

        return parameter_dict

    # Figure out the adsorption and desorption branches
    def _splitdata(self, _data, pressure_key):
        """
        Splits isotherm data into an adsorption and desorption part and
        adds a column to mark the transition between the two.
        """
        # Get a column where all increasing are False and all decreasing are True
        increasing = _data.loc[:, pressure_key].diff().fillna(0) < 0
        # Get the first inflexion point (assume where des starts)
        inflexion = increasing.idxmax()

        # If there is an inflexion point
        if inflexion != 0:
            # If the first point is where the isotherm starts decreasing
            # Then it is a complete desorption curve
            if inflexion == 1:
                inflexion = 0

            # Set all instances after the inflexion point to True
            increasing[inflexion:] = True

        # Return the new array with the branch column
        return pandas.concat([_data, increasing.rename('branch')], axis=1)
