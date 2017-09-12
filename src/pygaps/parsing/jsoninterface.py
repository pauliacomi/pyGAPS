"""
Parsing to and from json file format for isotherms
"""

import json

import pandas

from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
from ..utilities.unit_converter import _LOADING_UNITS
from ..utilities.unit_converter import _MASS_UNITS
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
        raw_dict = _to_json_nist(raw_dict)

    # Isotherm data
    isotherm_data_dict = isotherm.data().to_dict(orient='index')
    raw_dict["isotherm_data"] = {str(k): {p: str(t) for p, t in v.items()}
                                 for k, v in isotherm_data_dict.items()}

    json_isotherm = json.dumps(raw_dict, sort_keys=True)

    return json_isotherm


def isotherm_from_json(json_isotherm,
                       mode_pressure='absolute',
                       mode_adsorbent='mass',
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
    mode_adsorbent : {'mass','volume'}, optional
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
    data = pandas.DataFrame.from_dict(
        raw_dict["isotherm_data"], orient='index', dtype='float64')
    del raw_dict["isotherm_data"]

    # Rename keys and get units if needed depending on format
    if fmt == 'NIST':
        (raw_dict,
         mode_pressure,
         mode_adsorbent,
         unit_pressure,
         unit_loading) = _from_json_nist(raw_dict)

    # convert index into int (seen as string)
    data.index = data.index.map(int)

    # sort index, in case the json was not sorted
    data.sort_index(inplace=True)

    # set dataframe keys
    pressure_key = 'pressure'
    if fmt is None:
        loading_key = 'loading'
    elif fmt == 'NIST':
        loading_key = 'adsorption'

    other_keys = [column for column in data.columns.values if column not in [
        loading_key, pressure_key]]

    # generate the isotherm
    isotherm = PointIsotherm(data,
                             loading_key=loading_key,
                             pressure_key=pressure_key,
                             other_keys=other_keys,
                             mode_adsorbent=mode_adsorbent,
                             mode_pressure=mode_pressure,
                             unit_loading=unit_loading,
                             unit_pressure=unit_pressure,
                             **raw_dict)

    return isotherm


def _to_json_nist(raw_dict):
    """
    Converts an internal dictionary format to a NIST format
    """
    nist_dict = dict()

    nist_dict['adosrbentMaterial'] = raw_dict['sample_name']
    nist_dict['hashkey'] = raw_dict['sample_batch']
    nist_dict['adsorbateGas'] = raw_dict['adsorbate']
    nist_dict['temperature'] = raw_dict['t_exp']

    return nist_dict


def _from_json_nist(raw_dict):
    """
    Converts a NIST dictionary format to a internal format
    """

    nist_dict = dict()

    nist_dict['sample_name'] = raw_dict['adosrbentMaterial']
    nist_dict['sample_batch'] = raw_dict['hashkey']
    nist_dict['adsorbate'] = raw_dict['adsorbateGas']
    nist_dict['t_exp'] = raw_dict['temperature']

    # Get modes and units
    loading_string = raw_dict["adsorptionUnits"]
    comp = loading_string.split('/')
    if len(comp) != 2:
        raise ParsingError("Isotherm cannot be parsed due to loading format")

    # TODO ensure that the adsorbent unit is included later
    if comp[1] in _MASS_UNITS:
        mode_adsorbent = "mass"
    elif comp[1] in _VOLUME_UNITS:
        mode_adsorbent = "volume"
    else:
        raise ParsingError("Isotherm cannot be parsed due to adsorbent unit")

    if comp[0] in _LOADING_UNITS:
        unit_loading = comp[0]
    else:
        raise ParsingError("Isotherm cannot be parsed due to loading unit")

    mode_pressure = "absolute"

    pressure_string = loading_string = raw_dict["pressureUnits"]

    if pressure_string in _LOADING_UNITS:
        unit_pressure = pressure_string
    else:
        raise ParsingError("Isotherm cannot be parsed due to pressure unit")

    return (nist_dict,
            mode_pressure, mode_adsorbent,
            unit_pressure, unit_loading)
