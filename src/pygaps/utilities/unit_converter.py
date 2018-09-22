"""
Module performing the conversions between different units used.
"""

import pygaps

from .exceptions import ParameterError

_MOLAR_UNITS = {
    "mol": 1,
    "mmol": 0.001,
    "kmol": 1000,
    "cm3(STP)": 4.461e-5,
    "ml": 4.461e-5,
}
_MASS_UNITS = {
    'mg': 0.001,
    'g': 1,
    'kg': 1000,
}
_VOLUME_UNITS = {
    'cm3': 1,
    'ml': 1,
    'dm3': 1e3,
    'l': 1e3,
    'm3': 1e6,
}
_PRESSURE_UNITS = {
    "bar": 100000,
    "Pa": 1,
    "kPa": 1000,
    "atm": 101325,
    "mmHg": 133.322
}

_PRESSURE_MODE = {
    "absolute": _PRESSURE_UNITS,
    "relative": None,
}

_MATERIAL_MODE = {
    "mass": _MASS_UNITS,
    "volume": _VOLUME_UNITS,
    "molar": _MOLAR_UNITS,
}


def c_pressure(value,
               mode_from, mode_to,
               unit_from, unit_to,
               adsorbate_name=None, temp=None):
    """
    Converts pressure units and modes.
    Adsorbate name and temperature have to be
    specified when converting between modes.

    Parameters
    ----------
    value : float
        The value to convert.
    mode_from : str
        Whether to convert from a mode.
    mode_to: str
        Whether to convert to a mode.
    unit_from : str
        Unit from which to convert.
    unit_from : str
        Unit to which to convert.
    adsorbate_name : str
        Name of the adsorbate on which the pressure is to be
        converted.
    temp : float
        Temperature at which the pressure is measured, in K.

    Returns
    -------
    float
        Pressure converted as requested.

    Raises
    ------
    ``ParameterError``
        If the mode selected is not an option.
    """
    if mode_from != mode_to:

        if mode_to not in _PRESSURE_MODE:
            raise ParameterError(
                "Mode selected for pressure ({}) is not an option. Viable"
                " modes are {}".format(mode_to, _PRESSURE_MODE.keys()))

        if mode_to == "absolute":
            if not unit_to:
                raise ParameterError("Specify unit to convert to.")
            if unit_to not in _PRESSURE_UNITS:
                raise ParameterError(
                    "Unit to is not an option. Viable"
                    " units are {}".format(_PRESSURE_UNITS.keys()))

            unit = unit_to
            sign = 1
        elif mode_to == "relative":
            unit = unit_from
            sign = -1

        value = value * \
            pygaps.classes.adsorbate.Adsorbate.from_list(adsorbate_name).saturation_pressure(
                temp, unit=unit) ** sign

    elif unit_to and mode_from == 'absolute':
        value = c_unit(_PRESSURE_MODE[mode_from], value, unit_from, unit_to)

    return value


def c_loading(value,
              basis_from, basis_to,
              unit_from, unit_to,
              adsorbate_name=None, temp=None):
    """
    Converts loading units and basis.

    Adsorbate name and temperature have to be
    specified when converting between basis.

    Parameters
    ----------
    value : float
        The value to convert.
    basis_from : str
        Whether to convert from a basis.
    basis_to: str
        Whether to convert to a basis.
    unit_from : str
        Unit from which to convert.
    unit_from : str
        Unit to which to convert.
    adsorbate_name : str
        Name of the adsorbate on which the pressure is to be
        converted.
    temp : float
        Temperature at which the pressure is measured, in K.

    Returns
    -------
    float
        Loading converted as requested.

    Raises
    ------
    ``ParameterError``
        If the mode selected is not an option.
    """
    if basis_from != basis_to:

        if basis_to not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for loading ({}) is not an option. Viable"
                " modes are {}".format(basis_to, _MATERIAL_MODE.keys()))

        if not unit_to or not unit_from:
            raise ParameterError("Specify both from and to units")

        if unit_to not in _MATERIAL_MODE[basis_to]:
            raise ParameterError(
                "Unit to is not an option. Viable"
                " units are {}".format(_MATERIAL_MODE[basis_to].keys()))

        if unit_from not in _MATERIAL_MODE[basis_from]:
            raise ParameterError(
                "Unit from is not an option. Viable"
                " units are {}".format(_MATERIAL_MODE[basis_from].keys()))

        if basis_from == 'mass':
            if basis_to == 'volume':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).gas_density(temp=temp)
                sign = -1
            elif basis_to == 'molar':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).molar_mass()
                sign = -1
        elif basis_from == 'volume':
            if basis_to == 'mass':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).gas_density(temp=temp)
                sign = 1
            elif basis_to == 'molar':
                adsorbate = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name)
                constant = adsorbate.gas_density(
                    temp=temp) / adsorbate.molar_mass()
                sign = -1
        elif basis_from == 'molar':
            if basis_to == 'mass':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).molar_mass()
                sign = 1
            elif basis_to == 'volume':
                adsorbate = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name)
                constant = adsorbate.gas_density(
                    temp=temp) / adsorbate.molar_mass()
                sign = -1

        value = value * _MATERIAL_MODE[basis_from][unit_from] \
            * constant ** sign \
            / _MATERIAL_MODE[basis_to][unit_to]

    elif unit_to and unit_from != unit_to:
        value = c_unit(_MATERIAL_MODE[basis_from], value, unit_from, unit_to)

    return value


def c_adsorbent(value,
                basis_from, basis_to,
                unit_from, unit_to,
                sample_name=None, sample_batch=None):
    """
    Converts adsorbent units and basis.

    The name and batch of the sample have to be
    specified when converting between basis.

    Parameters
    ----------
    value : float
        The value to convert.
    basis_from : str
        Whether to convert from a basis.
    basis_to: str
        Whether to convert to a basis.
    unit_from : str
        Unit from which to convert.
    unit_from : str
        Unit to which to convert.
    sample_name : str
        Name of the sample on which the value is based.
    sample_batch : float
        Batch of the sample on which the value is based.

    Returns
    -------
    float
        Loading converted as requested.

    Raises
    ------
    ``ParameterError``
        If the mode selected is not an option.

    """
    if basis_from != basis_to:

        if basis_to not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for adsorbent ({}) is not an option. Viable"
                " modes are {}".format(basis_to, _MATERIAL_MODE.keys()))

        if not unit_to or not unit_from:
            raise ParameterError("Specify both from and to units")

        if unit_to not in _MATERIAL_MODE[basis_to]:
            raise ParameterError(
                "Unit to is not an option. Viable"
                " units are {}".format(_MATERIAL_MODE[basis_to].keys()))

        if unit_from not in _MATERIAL_MODE[basis_from]:
            raise ParameterError(
                "Unit from is not an option. Viable"
                " units are {}".format(_MATERIAL_MODE[basis_from].keys()))

        if basis_from == 'mass':
            if basis_to == 'volume':
                constant = pygaps.classes.sample.Sample.from_list(
                    sample_name, sample_batch).get_prop('density')
                sign = -1
            elif basis_to == 'molar':
                constant = pygaps.classes.sample.Sample.from_list(
                    sample_name, sample_batch).get_prop('molar_mass')
                sign = -1
        elif basis_from == 'volume':
            if basis_to == 'mass':
                constant = pygaps.classes.sample.Sample.from_list(
                    sample_name, sample_batch).get_prop('density')
                sign = 1
            elif basis_to == 'molar':
                sample = pygaps.classes.sample.Sample.from_list(
                    sample_name, sample_batch)
                constant = sample.get_prop(
                    'density') / sample.get_prop('molar_mass')
                sign = -1
        elif basis_from == 'molar':
            if basis_to == 'mass':
                constant = pygaps.classes.sample.Sample.from_list(
                    sample_name, sample_batch).get_prop('molar_mass')
                sign = 1
            elif basis_to == 'volume':
                sample = pygaps.classes.sample.Sample.from_list(
                    sample_name, sample_batch)
                constant = sample.get_prop(
                    'density') / sample.get_prop('molar_mass')
                sign = -1

        value = value / _MATERIAL_MODE[basis_from][unit_from] \
            / constant ** sign \
            * _MATERIAL_MODE[basis_to][unit_to]

    elif unit_to and unit_from != unit_to:
        value = c_unit(_MATERIAL_MODE[basis_from],
                       value, unit_from, unit_to, sign=-1)

    return value


def c_unit(unit_list, value, unit_from, unit_to, sign=1):
    """
    Converts a units based on their proportions in
    a dictionary.

    Parameters
    ----------
    unit_list : dict
        The dictionary with the units and their relationship.
    value : dict
        The value to convert.
    unit_from : str
        Unit from which to convert.
    unit_from : str
        Unit to which to convert.
    sign : int
        If the conversion is inverted or not.

    Returns
    -------
    float
        Value converted as requested.

    Raises
    ------
    ``ParameterError``
        If the unit selected is not an option.
    """

    if unit_to not in unit_list or unit_from not in unit_list:
        raise ParameterError(
            "Units selected for conversion (from {} to {}) are not an option. Viable"
            " units are {}".format(unit_from, unit_to, unit_list.keys()))

    value = value * \
        (unit_list[unit_from] / unit_list[unit_to]) ** sign

    return value


def find_basis(unit):
    """Finds the basis of a given unit."""

    if unit in _VOLUME_UNITS:
        basis = 'molar'
    elif unit in _MASS_UNITS:
        basis = 'mass'
    elif unit in _MOLAR_UNITS:
        basis = 'molar'
    else:
        raise ParameterError('Unit is in unknown basis')

    return basis


def find_mode(unit):
    """Finds the mode of a given pressure."""

    if unit in _PRESSURE_UNITS:
        mode = 'absolute'
    elif unit == 'p/p0':
        mode = 'relative'
    else:
        raise ParameterError('Unit is unknown')

    return mode
