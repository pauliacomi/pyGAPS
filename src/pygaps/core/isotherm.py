"""Contains the Isotherm base class."""

import warnings

import numpy

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
    an isotherm (such as material, adsorbate, data units etc.) but without
    any of the data itself.

    Think of this class as a extended python dictionary.

    Parameters
    ----------
    material : str
        Name of the material on which the isotherm is measured.
    adsorbate : str
        Isotherm adsorbate.
    temperature : float
        Isotherm temperature.

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
    ``material``, ``temperature', ``adsorbate``.
    """

    # strictly required attributes
    _required_params = ['material', 'temperature', 'adsorbate']
    # unit-related attributes
    _unit_params = {
        'pressure_unit': 'bar',
        'pressure_mode': 'absolute',
        'adsorbent_unit': 'g',
        'adsorbent_basis': 'mass',
        'loading_unit': 'mmol',
        'loading_basis': 'molar',
    }
    # other special reserved parameters
    # subclasses overwrite this
    _reserved_params = []

    ##########################################################
    #   Instantiation and classmethods

    def __init__(self, **properties):
        """
        Instantiate is done by passing a dictionary with the parameters,
        as well as the info about units, modes and data columns.

        """
        # Must-have properties of the isotherm
        #
        # Basic checks
        if any(k not in properties for k in self._required_params):
            raise ParameterError(
                f"Isotherm MUST have the following properties:{self._required_params}"
            )

        #: Isotherm material name.
        self.material = str(properties.pop('material'))
        #: Isotherm experimental temperature.
        self.temperature = float(properties.pop('temperature'))
        #: Isotherm adsorbate.
        self.adsorbate = properties.pop('adsorbate')
        try:
            self.adsorbate = pygaps.Adsorbate.find(self.adsorbate)
        except pygaps.ParameterError:
            warnings.warn((
                "Specified adsorbent is not in internal list "
                "(or name cannot be resolved to an existing one). "
                "CoolProp backend disabled for this adsorbent."
            ))

        # Isotherm units
        #
        # We create a custom warning format that only displays the message.
        def custom_formatwarning(msg, *args, **kwargs):
            # ignore everything except the message
            return str(msg) + '\n'

        old_formatter = warnings.formatwarning
        warnings.formatwarning = custom_formatwarning

        for k in self._unit_params:
            if k not in properties:
                warnings.warn(
                    f"WARNING: '{k}' was not specified , assumed as '{self._unit_params[k]}'"
                )
                properties[k] = self._unit_params[k]

        warnings.formatwarning = old_formatter

        self.pressure_mode = properties.pop('pressure_mode', None)
        self.pressure_unit = properties.pop('pressure_unit', None)
        if self.pressure_mode == 'relative':
            self.pressure_unit = None
        self.adsorbent_basis = properties.pop('adsorbent_basis', None)
        self.adsorbent_unit = properties.pop('adsorbent_unit', None)
        self.loading_basis = properties.pop('loading_basis', None)
        self.loading_unit = properties.pop('loading_unit', None)

        # Check basis
        if self.adsorbent_basis not in _MATERIAL_MODE:
            raise ParameterError(
                f"Basis selected for adsorbent ({self.adsorbent_basis}) is not an option. "
                f"See viable values: {_MATERIAL_MODE.keys()}"
            )

        if self.loading_basis not in _MATERIAL_MODE:
            raise ParameterError(
                f"Basis selected for loading ({self.loading_basis}) is not an option. "
                f"See viable values: {_MATERIAL_MODE.keys()}"
            )

        if self.pressure_mode not in _PRESSURE_MODE:
            raise ParameterError(
                f"Mode selected for pressure ({self.pressure_mode}) is not an option. "
                f"See viable values: {_PRESSURE_MODE.keys()}"
            )

        # Check units
        if self.loading_unit not in _MATERIAL_MODE[self.loading_basis]:
            raise ParameterError(
                f"Unit selected for loading ({self.loading_unit}) is not an option. "
                f"See viable values: {_MATERIAL_MODE[self.loading_basis].keys()}"
            )

        if self.pressure_mode == 'absolute' and self.pressure_unit not in _PRESSURE_UNITS:
            raise ParameterError(
                f"Unit selected for pressure ({self.pressure_unit}) is not an option. "
                f"See viable values: {_PRESSURE_UNITS.keys()}"
            )

        if self.adsorbent_unit not in _MATERIAL_MODE[self.adsorbent_basis]:
            raise ParameterError(
                f"Unit selected for adsorbent ({self.adsorbent_unit}) is not an option. "
                f"See viable values: {_MATERIAL_MODE[self.loading_basis].keys()}"
            )

        # Other named properties of the isotherm

        # Isotherm material batch, deprecated.
        self.material_batch = str(properties.pop('material_batch', None))

        # Save the rest of the properties as members
        for attr in properties:
            if hasattr(self, attr):
                raise ParameterError(
                    "Cannot override standard Isotherm class member '{}'"
                    .format(attr)
                )
            setattr(self, attr, properties[attr])

    ##########################################################
    #   Overloaded and private functions

    @property
    def iso_id(self):
        """Return an unique identifier of the isotherm."""
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
        return f"{self.iso_id}: '{self.adsorbate}' on '{self.material}' at {self.temperature} K"

    def __str__(self):
        """Print a short summary of all the isotherm parameters."""
        string = ""

        # Required
        string += ("Material: " + str(self.material) + '\n')
        string += ("Adsorbate: " + str(self.adsorbate) + '\n')
        string += ("Temperature: " + str(self.temperature) + "K" + '\n')

        # Units/basis
        string += ("Units: \n")
        string += (
            "\tUptake in: " + str(self.loading_unit) + "/" +
            str(self.adsorbent_unit) + '\n'
        )
        if self.pressure_mode == 'relative':
            string += ("\tRelative pressure \n")
        else:
            string += ("\tPressure in: " + str(self.pressure_unit) + '\n')

        string += ("Other properties: \n")
        for prop in vars(self):
            if prop not in self._required_params + \
                    list(self._unit_params) + self._reserved_params:
                string += (
                    '\t' + prop + ": " + str(getattr(self, prop)) + '\n'
                )

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
            parameter_dict.pop(param, None)

        return parameter_dict

    def to_json(self, path=None, **kwargs):
        """
        Convert the isotherm to a JSON representation.

        Parameters
        ----------
        path
            File path or object. If not specified, the result is returned as a string.
        kwargs
            Custom arguments to be passed to "json.dump", like `indent`.

        Returns
        -------
        None or str
            If path is None, returns the resulting json format as a string.
            Otherwise returns None.
        """
        return pygaps.isotherm_to_json(self, path, **kwargs)

    def to_csv(self, path=None, separator=',', **kwargs):
        """
        Convert the isotherm to a CSV representation.

        Parameters
        ----------
        path
            File path or object. If not specified, the result is returned as a string.
        separator : str, optional
            Separator used int the csv file. Defaults to '',''.

        Returns
        -------
        None or str
            If path is None, returns the resulting json format as a string.
            Otherwise returns None.
        """
        return pygaps.isotherm_to_csv(self, path, separator, **kwargs)

    def to_xl(self, path, **kwargs):
        """
        Save the isotherm as an Excel file.

        Parameters
        ----------
        path
            Path where to save Excel file.

        """
        return pygaps.isotherm_to_xl(self, path, **kwargs)

    # Figure out the adsorption and desorption branches
    @staticmethod
    def _splitdata(data, pressure_key):
        """
        Split isotherm data into an adsorption and desorption part and
        return a column which marks the transition between the two.
        """
        # Generate array
        split = numpy.array([False for p in range(0, len(data.index))])

        # Get the maximum pressure point (assume where desorption starts)
        inflexion = data.index.get_loc(data[pressure_key].idxmax()) + 1

        # If the maximum is not the last point
        if inflexion != len(split):

            # If the first point is the maximum, then it is purely desorption
            if inflexion == data.index[0]:
                inflexion = 0

            # Set all instances after the inflexion point to True
            split[inflexion:] = True

        # Return the new array with the branch column
        return split
