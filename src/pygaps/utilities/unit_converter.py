"""Module containing the conversions between different units used"""

from .exceptions import ParameterError

import pygaps

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
    Converts absolute pressure to relative and vice-versa.
    Only possible if in the subcritical region.

    Parameters
    ----------
    pygaps.classes.adsorbate.Adsorbate : Adsorbate
        The dsorbate for which the mode is changed.
    mode : {'relative', 'absolute'}
        Whether to convert to relative from absolute or to absolute
        from relative.
    pressure : float
        The absolute pressure which is to be converted into
        relative pressure.
    temp : float
        Temperature at which the pressure is measured, in K
    unit : optional
        Unit in which the absolute presure is passed.
        If not specifies defaults to Pascal.

    Returns
    -------
    float
        Pressure in the mode requested.

    Raises
    ------
    ``ParameterError``
        If the mode selected is not an option
    ``CalculationError``
        If it cannot be calculated, due to a physical reason.
    """
    if mode_from != mode_to:

        if mode_to not in _PRESSURE_MODE:
            raise ParameterError(
                "Mode selected for pressure ({}) is not an option. Viable"
                " modes are {}".format(mode_to, _PRESSURE_MODE.keys()))

        if mode_to == "absolute":
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
    """
    if basis_from != basis_to:

        if basis_to not in _MATERIAL_MODE:
            raise ParameterError(
                "Basis selected for loading ({}) is not an option. Viable"
                " modes are {}".format(basis_to, _MATERIAL_MODE.keys()))

        if not unit_to:
            if basis_to == 'mass':
                unit_to = 'g'
            elif basis_to == 'molar':
                unit_to = 'mmol'
            elif basis_to == 'volume':
                unit_to = 'cm3'

        if basis_from == 'mass':
            if basis_to == 'volume':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).liquid_density(temp=temp)
                sign = -1
            elif basis_to == 'molar':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).molar_mass()
                sign = -1
        elif basis_from == 'volume':
            if basis_to == 'mass':
                constant = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name).liquid_density(temp=temp)
                sign = 1
            elif basis_to == 'molar':
                adsorbate = pygaps.classes.adsorbate.Adsorbate.from_list(
                    adsorbate_name)
                constant = adsorbate.liquid_density(
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
                constant = adsorbate.liquid_density(
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
    Converts mass to volume of adsorbent and vice-versa.
    Requires a `density` key in the pygaps.classes.sample.Sample properties dictionary.

    Parameters
    ----------
    adsorbent : pygaps.classes.sample.Sample
        The pygaps.classes.sample.Sample to use when converting basis.
    basis_to : {'mass', 'volume'}
        Whether to convert to a mass basis from a volume basis or
        to a volume basis from a mass basis
    basis_value : float
        The weight or the volume of the pygaps.classes.sample.Sample, respectively
    unit : str, optional
        Unit in which the basis is specified in the pygaps.classes.sample.Sample.

    Returns
    -------
    float
        Value in the basis requested.

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

        if not unit_to:
            if basis_to == 'mass':
                unit_to = 'g'
            elif basis_to == 'molar':
                unit_to = 'mmol'
            elif basis_to == 'volume':
                unit_to = 'cm3'

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
    Converts units depending on unit type

    Parameters
    """

    if unit_to not in unit_list or unit_from not in unit_list:
        raise ParameterError(
            "Units selected for conversion (from {} to {}) are not an option. Viable"
            " units are {}".format(unit_from, unit_to, unit_list.keys()))

    value = value * \
        (unit_list[unit_from] / unit_list[unit_to]) ** sign

    return value
