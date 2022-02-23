"""Contains the Isotherm base class."""

import typing as t

from pygaps import logger
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.material import Material
from pygaps.units.converter_mode import _LOADING_MODE
from pygaps.units.converter_mode import _MATERIAL_MODE
from pygaps.units.converter_mode import _PRESSURE_MODE
from pygaps.units.converter_mode import c_temperature
from pygaps.units.converter_unit import _PRESSURE_UNITS
from pygaps.units.converter_unit import _TEMPERATURE_UNITS
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.hashgen import isotherm_to_hash

SHORTHANDS = {
    'm': "material",
    't': "temperature",
    'a': "adsorbate",
}


class BaseIsotherm():
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
    pressure_mode : str, optional
        The pressure mode, either 'absolute' pressure or 'relative'
        ('relative%') in the form of p/p0.
    pressure_unit : str, optional
        Unit of pressure, if applicable.
    loading_basis : str, optional
        Whether the adsorbed amount is in terms of either 'volume_gas'
        'volume_liquid', 'molar', 'mass', or a fractional/percent basis.
    loading_unit : str, optional
        Unit in which the loading basis is expressed.
    material_basis : str, optional
        Whether the underlying material is in terms of 'per volume'
        'per molar amount' or 'per mass' of material.
    material_unit : str, optional
        Unit in which the material basis is expressed.

    Notes
    -----
    The class is also used to prevent duplication of code within the child
    classes, by calling the common inherited function before any other specific
    implementation additions.

    The minimum arguments required to instantiate the class are
    ``material``, ``temperature', ``adsorbate``.
    """

    # strictly required attributes
    _required_params = [
        'material',
        'temperature',
        'adsorbate',
    ]
    # unit-related attributes and their defaults
    _unit_params = {
        'pressure_mode': 'absolute',
        'pressure_unit': 'bar',
        'material_basis': 'mass',
        'material_unit': 'g',
        'loading_basis': 'molar',
        'loading_unit': 'mmol',
        'temperature_unit': 'K',
    }
    # other special reserved parameters
    # subclasses extend this
    _reserved_params = [
        "_material",
        "_adsorbate",
        "_temperature",
        "m",
        "t",
        "a",
    ]

    ##########################################################
    #   Instantiation and classmethods

    def __init__(
        self,
        material: t.Union[str, dict, Material] = None,
        adsorbate: t.Union[str, Adsorbate] = None,
        temperature: t.Union[float, str] = None,
        **properties: dict,
    ):
        """
        Instantiate is done by passing a dictionary with the parameters,
        as well as the info about units, modes and data columns.

        """
        # commonly used shorthands
        for shorthand, prop in SHORTHANDS.items():
            data = properties.pop(shorthand, None)
            if data:
                if prop == "material":
                    material = data
                elif prop == "adsorbate":
                    adsorbate = data
                elif prop == "temperature":
                    temperature = data

        # Must-have properties of the isotherm
        #
        # Basic checks
        if None in [material, adsorbate, temperature]:
            raise ParameterError(
                f"Isotherm MUST have the following properties: {self._required_params}"
            )

        self.material = material
        self.adsorbate = adsorbate
        self.temperature = temperature

        # Isotherm units
        #
        for uparam, udefault in self._unit_params.items():
            if uparam not in properties:
                logger.warning(f"WARNING: '{uparam}' was not specified , assumed as '{udefault}'")
                properties[uparam] = udefault

        # TODO deprecation
        if self._unit_params['loading_basis'] == 'volume':
            self._unit_params['loading_basis'] = 'volume_gas'
            logger.warning(
                "Loading basis as 'volume' is unclear and deprecated. "
                "Assumed as 'volume_gas'."
            )

        self.pressure_mode = properties.pop('pressure_mode')
        self.pressure_unit = properties.pop('pressure_unit')
        if self.pressure_mode.startswith('relative'):
            self.pressure_unit = None
        self.material_basis = properties.pop('material_basis')
        self.material_unit = properties.pop('material_unit')
        self.loading_basis = properties.pop('loading_basis')
        self.loading_unit = properties.pop('loading_unit')
        self.temperature_unit = properties.pop('temperature_unit')

        # Check basis / mode
        if self.pressure_mode not in _PRESSURE_MODE:
            raise ParameterError(
                f"Mode selected for pressure ({self.pressure_mode}) is not an option. "
                f"See viable values: {_PRESSURE_MODE.keys()}"
            )

        if self.loading_basis not in _LOADING_MODE:
            raise ParameterError(
                f"Basis selected for loading ({self.loading_basis}) is not an option. "
                f"See viable values: {_LOADING_MODE.keys()}"
            )

        if self.material_basis not in _MATERIAL_MODE:
            raise ParameterError(
                f"Basis selected for material ({self.material_basis}) is not an option. "
                f"See viable values: {_MATERIAL_MODE.keys()}"
            )

        # Check units
        if self.pressure_mode == 'absolute' and self.pressure_unit not in _PRESSURE_UNITS:
            raise ParameterError(
                f"Unit selected for pressure ({self.pressure_unit}) is not an option. "
                f"See viable values: {_PRESSURE_UNITS.keys()}"
            )

        if self.loading_unit not in _LOADING_MODE[self.loading_basis]:
            raise ParameterError(
                f"Unit selected for loading ({self.loading_unit}) is not an option. "
                f"See viable values: {_LOADING_MODE[self.loading_basis].keys()}"
            )

        if self.material_unit not in _MATERIAL_MODE[self.material_basis]:
            raise ParameterError(
                f"Unit selected for material ({self.material_unit}) is not an option. "
                f"See viable values: {_MATERIAL_MODE[self.loading_basis].keys()}"
            )

        if self.temperature_unit not in _TEMPERATURE_UNITS:
            raise ParameterError(
                f"Unit selected for temperature ({self.temperature_unit}) is not an option. "
                f"See viable values: {_TEMPERATURE_UNITS.keys()}"
            )

        # Other named properties of the isotherm

        # Save the rest of the properties as metadata
        self.properties = properties

    ##########################################################
    #   Overloaded and own functions

    @property
    def iso_id(self) -> str:
        """Return an unique identifier of the isotherm."""
        return isotherm_to_hash(self)

    @property
    def material(self) -> Material:
        """Return underlying material."""
        return self._material

    @material.setter
    def material(self, value: t.Union[str, dict, Material]):
        if isinstance(value, dict):
            name = value.pop('name', None)
            try:
                self._material = Material.find(name)
                self._material.properties.update(**value)
            except ParameterError:
                self._material = Material(name, **value)
            return
        try:
            self._material = Material.find(value)
        except ParameterError:
            self._material = Material(value)

    @property
    def adsorbate(self) -> Adsorbate:
        """Return underlying adsorbate."""
        return self._adsorbate

    @adsorbate.setter
    def adsorbate(self, value: t.Union[str, Adsorbate]):
        try:
            self._adsorbate = Adsorbate.find(value)
        except ParameterError:
            self._adsorbate = Adsorbate(value)
            logger.warning(
                "Specified adsorbate is not in internal list "
                "(or name cannot be resolved to an existing one). "
                "CoolProp backend disabled for this gas/vapour."
            )

    @property
    def temperature(self) -> float:
        """Return underlying temperature, always in kelvin."""
        if self.temperature_unit == "K":
            return self._temperature
        return c_temperature(self._temperature, self.temperature_unit, "K")

    @temperature.setter
    def temperature(self, value: t.Union[float, str]):
        self._temperature = float(value)

    def __eq__(self, other_isotherm) -> bool:
        """
        Overload the equality operator of the isotherm.

        Since id's should be unique and representative of the
        data inside the isotherm, all we need to ensure equality
        is to compare the two hashes of the isotherms.
        """
        return self.iso_id == other_isotherm.iso_id

    def __repr__(self) -> str:
        """Print key isotherm parameters."""
        return f"<{type(self).__name__} {self.iso_id}>: '{self.adsorbate}' on '{self.material}' at {self.temperature} K"

    def __str__(self) -> str:
        """Print a short summary of all the isotherm parameters."""
        string = ""

        # Required
        string += f"Material: { str(self.material) }\n"
        string += f"Adsorbate: { str(self.adsorbate) }\n"
        string += f"Temperature: { str(self.temperature) }K\n"

        # Units/basis
        string += "Units: \n"
        string += f"\tUptake in: {self.loading_unit}/{self.material_unit}\n"
        if self.pressure_mode.startswith('relative'):
            string += "\tRelative pressure\n"
        else:
            string += f"\tPressure in: {self.pressure_unit}\n"

        if self.properties:
            string += "Other properties: \n"
        for prop, val in self.properties.items():
            string += (f"\t{prop}: {str(val)}\n")

        return string

    def to_dict(self) -> dict:
        """
        Returns a dictionary of the isotherm class
        Is the same dictionary that was used to create it.

        Returns
        -------
        dict
            Dictionary of all parameters.
        """
        parameter_dict = vars(self).copy()

        # These line are here to ensure that material/adsorbate are copied as a string
        parameter_dict['adsorbate'] = str(parameter_dict.pop('_adsorbate'))
        material = parameter_dict.pop('_material')
        if material.properties:
            parameter_dict['material'] = material.to_dict()
        else:
            parameter_dict['material'] = str(material)
        parameter_dict['temperature'] = parameter_dict.pop('_temperature')

        # Remove reserved parameters
        for param in self._reserved_params:
            parameter_dict.pop(param, None)

        # Add metadata
        parameter_dict.update(parameter_dict.pop('properties'))

        return parameter_dict

    def to_json(self, path=None, **kwargs) -> t.Union[None, str]:
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
            If path is None, returns the resulting json as a string.
            Otherwise returns None.
        """
        from pygaps.parsing.json import isotherm_to_json
        return isotherm_to_json(self, path, **kwargs)

    def to_csv(self, path=None, separator=',', **kwargs) -> t.Union[None, str]:
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
            If path is None, returns the resulting csv as a string.
            Otherwise returns None.
        """
        from pygaps.parsing.csv import isotherm_to_csv
        return isotherm_to_csv(self, path, separator, **kwargs)

    def to_xl(self, path, **kwargs):
        """
        Save the isotherm as an Excel file.

        Parameters
        ----------
        path
            Path where to save Excel file.

        """
        from pygaps.parsing.excel import isotherm_to_xl
        return isotherm_to_xl(self, path, **kwargs)

    def to_aif(self, path=None, **kwargs) -> t.Union[None, str]:
        """
        Convert the isotherm to a AIF representation.

        Parameters
        ----------
        path
            File path or object. If not specified, the result is returned as a string.

        Returns
        -------
        None or str
            If path is None, returns the resulting AIF as a string.
            Otherwise returns None.
        """
        from pygaps.parsing.aif import isotherm_to_aif
        return isotherm_to_aif(self, path, **kwargs)

    def to_db(
        self,
        db_path: str = None,
        verbose: bool = True,
        autoinsert_material: bool = True,
        autoinsert_adsorbate: bool = True,
        **kwargs
    ):
        """
        Upload the isotherm to an sqlite database.

        Parameters
        ----------
        db_path : str, None
            Path to the database. If none is specified, internal database is used.
        autoinsert_material: bool, True
            Whether to automatically insert an isotherm material if it is not found
            in the database.
        autoinsert_adsorbate: bool, True
            Whether to automatically insert an isotherm adsorbate if it is not found
            in the database.
        verbose : bool
            Extra information printed to console.

        """
        from pygaps.parsing.sqlite import isotherm_to_db
        return isotherm_to_db(
            self,
            db_path=db_path,
            autoinsert_material=autoinsert_material,
            autoinsert_adsorbate=autoinsert_adsorbate,
            verbose=verbose,
            **kwargs
        )

    def convert_temperature(
        self,
        unit_to: str,
        verbose: bool = False,
    ):
        """
        Convert isotherm temperature from one unit to another.

        Parameters
        ----------
        unit_to : str
            The unit into which the internal temperature should be converted to.
        verbose : bool
            Print out steps taken.

        """
        self._temperature = c_temperature(self._temperature, self.temperature_unit, unit_to)
        self.temperature_unit = unit_to

        if verbose:
            logger.info(f"Changed temperature unit to '{unit_to}'.")

    # Figure out the adsorption and desorption branches
    @staticmethod
    def _splitdata(data, pressure_key: bool):
        """
        Split isotherm data into an adsorption and desorption part and
        return a column which marks the transition between the two.
        """
        from pygaps.utilities.math_utilities import split_ads_data
        return split_ads_data(data, pressure_key)
