"""Define and perform conversions between different units used."""

from .exceptions import ParameterError

_MOLAR_UNITS = {
    "mmol": 0.001,
    "mol": 1,
    "kmol": 1000,
    "cm3(STP)": 4.461e-5,
    "ml(STP)": 4.461e-5,
}
_MASS_UNITS = {
    'amu': 1.66054e-27,
    'mg': 0.001,
    'cg': 0.01,
    'dg': 0.1,
    'g': 1,
    'kg': 1000,
}
_VOLUME_UNITS = {
    'cm3': 1,
    'mL': 1,
    'dm3': 1e3,
    'L': 1e3,
    'm3': 1e6,
}
_PRESSURE_UNITS = {
    "Pa": 1,
    "kPa": 1000,
    "MPa": 1000000,
    "mbar": 100,
    "bar": 100000,
    "atm": 101325,
    "mmHg": 133.322,
    "torr": 133.322,
}
_TEMPERATURE_UNITS = {
    "K": 0,
    "C": 273.15,
}


def c_unit(unit_list, value, unit_from, unit_to, sign=1):
    """
    Convert units based on their proportions in a dictionary.

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
            f"Units selected for conversion (from {unit_from} to {unit_to}) are not an option. "
            f"Viable units are {unit_list.keys()}"
        )

    return value * \
        (unit_list[unit_from] / unit_list[unit_to]) ** sign
