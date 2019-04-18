"""Contains the Isotherm base class."""

import warnings

import pandas

import pygaps

from ..utilities.exceptions import ParameterError
from ..utilities.hashgen import isotherm_to_hash
from ..utilities.unit_converter import _MATERIAL_MODE
from ..utilities.unit_converter import _PRESSURE_MODE
from ..utilities.unit_converter import _PRESSURE_UNITS


class Isotherm():
    """
    Class which contains the general data for an isotherm, real or model.

    The isotherm class is the parent class that both PointIsotherm and
    ModelIsotherm inherit. It is designed to contain the information about
    an isotherm, such as material, adsorbate, data units etc., but without
    any of the data itself.

    Think of this class as a extended python dictionary.

    Parameters
    ----------
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
    The class is also used to prevent duplication of code within the child
    classes, by calling the common inherited function before any other specific
    implementation additions.

    The minimum arguments required to instantiate the class are
    ``material_name``, ``material_batch``, ``t_iso', ``adsorbate``.
    """

    _required_params = [
        'material_name',
        'material_batch',
        't_iso',
        'adsorbate'
    ]
    _named_params = {
        'iso_type': str,
    }

    _unit_params = [
        'pressure_unit',
        'pressure_mode',
        'adsorbent_unit',
        'adsorbent_basis',
        'loading_unit',
        'loading_basis',
    ]

    _reserved_params = []

    _db_columns = ['id'] + _required_params + list(_named_params)
    _id_params = _required_params + _unit_params

##########################################################
#   Instantiation and classmethods

    def __init__(self,
                 adsorbent_basis="mass",
                 adsorbent_unit="g",
                 loading_basis="molar",
                 loading_unit="mmol",
                 pressure_mode="absolute",
                 pressure_unit="bar",

                 **properties):
        """
        Instantiate is done by passing a dictionary with the parameters,
        as well as the info about units, modes and data columns.

        """
        # Checks
        if any(k not in properties
               for k in self._required_params):
            raise ParameterError(
                "Isotherm MUST have the following properties:{0}".format(self._required_params))

        # Basis and mode
        if adsorbent_basis is None or pressure_mode is None or loading_basis is None:
            raise ParameterError(
                "One of the modes or bases is not specified.")

        if adsorbent_basis not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for adsorbent ({0}) is not an option."
                "See viable values: {1}".format(adsorbent_basis, list(_MATERIAL_MODE.keys())))

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

        #: Isotherm material name.
        self.material_name = str(properties.pop('material_name'))
        #: Isotherm material batch.
        self.material_batch = str(properties.pop('material_batch'))
        #: Isotherm experimental temperature.
        self.t_iso = float(properties.pop('t_iso'))
        #: Isotherm adsorbate used.
        self.adsorbate = str(properties.pop('adsorbate'))

        if self.adsorbate.lower() not in pygaps.ADSORBATE_NAME_LIST:
            if not properties.pop('no_warn', False):
                warnings.warn(
                    ("Specified adsorbent is not in internal list"
                     "(or name cannot be resolved to an existing one)."
                     "CoolProp backend disabled for this adsorbent.")
                )
        else:
            self.adsorbate = pygaps.Adsorbate.find(self.adsorbate)

        # Named properties of the isotherm
        for named_prop in self._named_params:
            prop_val = properties.pop(named_prop, None)
            if prop_val:
                prop_val = self._named_params[named_prop](prop_val)
                setattr(self, named_prop, prop_val)

        # Save the rest of the properties as members
        #: Other properties of the isotherm.
        for attr in properties:
            if hasattr(self, attr):
                raise ParameterError("Cannot override standard class member '{}'".format(attr))
            setattr(self, attr, properties[attr])

    ##########################################################
    #   Overloaded and private functions

    @property
    def iso_id(self):
        return isotherm_to_hash(self)

    def __eq__(self, other_isotherm):
        """
        Overload the equality operator of the isotherm.

        Since id's should be unique and representative of the
        data inside the isotherm, all we need to ensure equality
        is to compare the two hashes of the isotherms.
        """
        return self.iso_id == other_isotherm.iso_id

    def __repr__(self):
        """Print key isotherm parameters."""
        return "{0}: '{1} - {2}' with '{3}' at {4} K".format(
            self.iso_id, self.material_name, self.material_batch, self.adsorbate, self.t_iso)

    def __str__(self):
        """Print a short summary of all the isotherm parameters."""
        string = ""

        # Required
        string += ("Material: " + str(self.material_name) + '\n')
        string += ("Batch: " + str(self.material_batch) + '\n')
        string += ("Adsorbate used: " + str(self.adsorbate) + '\n')
        string += ("Isotherm temperature: " + str(self.t_iso) + "K" + '\n')

        # Named
        for param in self._named_params:
            param_val = getattr(self, param, None)
            if param_val:
                string += (param + ': ' + str(param_val) + '\n')

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
            if prop not in self._required_params + list(self._named_params) + self._unit_params + self._reserved_params:
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

        # This line is here to ensure that adsorbate is copied as a string
        parameter_dict['adsorbate'] = str(parameter_dict['adsorbate'])

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
        if inflexion != _data.index[0]:
            # If the first point is where the isotherm starts decreasing
            # Then it is a complete desorption curve
            if inflexion == _data.index[1]:
                inflexion = 0

            # Set all instances after the inflexion point to True
            increasing[inflexion:] = True

        # Return the new array with the branch column
        return pandas.concat([_data, increasing.rename('branch')], axis=1)
