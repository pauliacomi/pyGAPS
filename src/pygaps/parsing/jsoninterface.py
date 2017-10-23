"""
Parsing to and from json file format for isotherms
"""

import json

import pandas

from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
from ..utilities.unit_converter import _LOADING_UNITS
from ..utilities.unit_converter import _MASS_UNITS
from ..utilities.unit_converter import _PRESSURE_UNITS
from ..utilities.unit_converter import _VOLUME_UNITS


def isotherm_to_json(isotherm, fmt=None):
    """
    Converts an isotherm object to a json structure
    Structure is inspired by the NIST format

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to be written to json.
    fmt : {None, 'NIST'}, optional
        If the format is set to NIST, then the json format a specific version
        used by the NIST database of adsorbents

    Returns
    -------
    str
        A string with the json format of the Isotherm.
    """

    # Isotherm properties
    raw_dict = isotherm.to_dict()

    if fmt == 'NIST':
        raw_dict = _to_json_nist(raw_dict,
                                 isotherm.mode_pressure,
                                 isotherm.basis_adsorbent,
                                 isotherm.unit_pressure,
                                 isotherm.unit_loading)

    # Isotherm data
    isotherm_data_dict = isotherm.data().to_dict(orient='index')
    raw_dict["isotherm_data"] = [{p: str(t) for p, t in v.items()}
                                 for k, v in isotherm_data_dict.items()]

    json_isotherm = json.dumps(raw_dict, sort_keys=True)

    return json_isotherm


def isotherm_from_json(json_isotherm,
                       pressure_key='pressure',
                       loading_key='loading',

                       basis_adsorbent='mass',
                       mode_pressure='absolute',
                       unit_pressure='bar',
                       unit_loading='mmol',
                       fmt=None):
    """
    Converts a json isotherm format to a internal format
    Structure is inspired by the NIST format

    Parameters
    ----------
    json_isotherm : str
        The isotherm in the json format, as string.
    mode_pressure : {'relative', 'absolute'}, optional
        Whether the adsorption is read in terms of either 'per volume'
        or 'per mass'. Defults to absolute.
    basis_adsorbent : {'mass','volume'}, optional
        The pressure mode, either absolute pressures or relative in
        the form of p/p0. Defults to mass.
    unit_pressure : str, optional
        Unit of pressure, Defults to bar.
    unit_loading : str, optional
        Unit of loading. Defults to mmol.
    fmt : {None, 'NIST'}, optional
        If the format is set to NIST, then the json format a specific version
        used by the NIST database of adsorbents.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the json
    """

    # Parse isotherm in dictionary
    raw_dict = json.loads(json_isotherm)

    # Build pandas dataframe of data
    data = pandas.DataFrame(raw_dict.pop("isotherm_data"), dtype='float64')

    # Rename keys and get units if needed depending on format
    if fmt == 'NIST':
        loading_key = 'adsorption'
        (raw_dict,
         mode_pressure,
         basis_adsorbent,
         unit_pressure,
         unit_loading) = _from_json_nist(raw_dict)

    # get the other data in the json
    other_keys = [column for column in data.columns.values
                  if column not in [loading_key, pressure_key]]

    # generate the isotherm
    isotherm = PointIsotherm(data,
                             loading_key=loading_key,
                             pressure_key=pressure_key,
                             other_keys=other_keys,
                             basis_adsorbent=basis_adsorbent,
                             mode_pressure=mode_pressure,
                             unit_loading=unit_loading,
                             unit_pressure=unit_pressure,
                             **raw_dict)

    return isotherm


NIST_ADSORBATES = {
    'Hydrogen': 'H2',
    'Helium': 'He',
    'Neon': 'Ne',
    'Argon': 'Ar',
    'Xenon': 'Xe',
    'Krypton': 'Kr',

    'Nitrogen': 'N2',
    'Oxygen': 'O2',
    'Carbon monoxide': 'CO',
    'Carbon Dioxide': 'CO2',

    'Methane': 'CH4',
    'Ethane': 'C2H6',
    'Ethene': 'C2H4',
    'Acetylene': 'C2H2',

    'N-propane': 'C3H8',
    'Propene': 'C3H6',
    'N-Butane': 'C4H10',

    'Ammonia': 'NH3',
    'Water': 'H2O',
    'Methanol': 'CH3OH',
    'Ethanol': 'CH3CH2OH',
}


def _to_json_nist(raw_dict,
                  mode_pressure, basis_adsorbent,
                  unit_pressure, unit_loading):
    """
    Converts an internal dictionary format to a NIST format
    """
    nist_dict = dict()

    nist_dict['adsorbentMaterial'] = raw_dict.pop('sample_name')
    nist_dict['hashkey'] = raw_dict.pop('sample_batch')
    nist_dict['temperature'] = raw_dict.pop('t_exp')

    internal_adsorbate = raw_dict.pop('adsorbate')
    nist_adsorbate = [k for k, v in NIST_ADSORBATES.items()
                      if v == internal_adsorbate]
    nist_dict['adsorbateGas'] = nist_adsorbate

    nist_dict["adsorptionUnits"] = '/'.join([unit_loading, basis_adsorbent])
    nist_dict["pressureUnits"] = unit_pressure

    # Add all the rest of the parameters
    nist_dict.update(raw_dict)

    return nist_dict


def _from_json_nist(raw_dict):
    """
    Converts a NIST dictionary format to a internal format
    """

    nist_dict = dict()

    # Get regular isotherm parameters
    nist_dict['sample_name'] = raw_dict.pop('adsorbentMaterial')
    nist_dict['sample_batch'] = raw_dict.pop('hashkey')
    nist_dict['t_exp'] = raw_dict.pop('temperature')

    # Get adsorbate
    nist_adsorbate = raw_dict.pop('adsorbateGas')
    internal_adsorbate = NIST_ADSORBATES.get(nist_adsorbate)

    if not internal_adsorbate:
        raise ParsingError(
            "Isotherm cannot be parsed due to non-recognised adsorbate")

    nist_dict['adsorbate'] = internal_adsorbate

    # Get loading basis and unit
    loading_string = raw_dict.pop("adsorptionUnits")
    comp = loading_string.split('/')
    if len(comp) != 2:
        raise ParsingError(
            "Isotherm cannot be parsed due to loading string format")

    if comp[0] in _LOADING_UNITS:
        unit_loading = comp[0]
    else:
        raise ParsingError("Isotherm cannot be parsed due to loading unit")

    if comp[1] in _MASS_UNITS:
        basis_adsorbent = "mass"
    elif comp[1] in _VOLUME_UNITS:
        basis_adsorbent = "volume"
    else:
        raise ParsingError("Isotherm cannot be parsed due to adsorbent basis")

    # Get pressure mode and unit
    mode_pressure = "absolute"
    pressure_string = raw_dict.pop("pressureUnits")

    if pressure_string in _PRESSURE_UNITS:
        unit_pressure = pressure_string
    else:
        raise ParsingError("Isotherm cannot be parsed due to pressure unit")

    # Add all the rest of the parameters
    nist_dict.update(raw_dict)

    return (nist_dict,
            mode_pressure, basis_adsorbent,
            unit_pressure, unit_loading)
