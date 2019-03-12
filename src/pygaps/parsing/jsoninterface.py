"""
Parsing to and from json file format for isotherms.
"""

import json

import pandas

from ..classes.isotherm import Isotherm
from ..classes.modelisotherm import ModelIsotherm
from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
from ..utilities.unit_converter import _MASS_UNITS
from ..utilities.unit_converter import _MOLAR_UNITS
from ..utilities.unit_converter import _PRESSURE_UNITS
from ..utilities.unit_converter import _VOLUME_UNITS


def isotherm_to_json(isotherm, fmt=None):
    """
    Converts an isotherm object to a json structure.
    Structure is inspired by the NIST format.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to be written to json.
    fmt : {None, 'NIST'}, optional
        If the format is set to NIST, then the json format a specific version
        used by the NIST database of adsorbents.

    Returns
    -------
    str
        A string with the json-formatted Isotherm.
    """

    # Isotherm properties
    raw_dict = isotherm.to_dict()

    # Isotherm data
    if isinstance(isotherm, PointIsotherm):
        isotherm_data_dict = isotherm.data().to_dict(orient='index')
        raw_dict["isotherm_data"] = [{p: str(t) for p, t in v.items()}
                                     for k, v in isotherm_data_dict.items()]
    elif isinstance(isotherm, ModelIsotherm):
        raw_dict["isotherm_model"] = {
            'model': isotherm.model.name,
            'parameters': isotherm.model.params,
        }

    json_isotherm = json.dumps(raw_dict, sort_keys=True)

    return json_isotherm


def isotherm_from_json(json_isotherm, fmt=None,
                       loading_key='loading', pressure_key='pressure',
                       **isotherm_parameters):
    """
    Converts a json isotherm format to a internal format.
    Structure is inspired by the NIST format.

    Parameters
    ----------
    json_isotherm : str
        The isotherm in the json format, as string.
    loading_key : str
        The title of the pressure data in the json provided.
    pressure_key
        The title of the loading data in the json provided.
    fmt : {None, 'NIST'}, optional
        If the format is set to NIST, then the json format a specific version
        used by the NIST database of adsorbents.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the json
    """

    # Parse isotherm in dictionary
    raw_dict = json.loads(json_isotherm)

    # Update dictionary with passed parameters
    raw_dict.update(isotherm_parameters)

    data = raw_dict.pop("isotherm_data", None)
    model = raw_dict.pop("isotherm_model", None)

    if data:
        # Rename keys and get units if needed depending on format
        if fmt == 'NIST':
            loading_key = 'total_adsorption'
            pressure_key = 'pressure'
            raw_dict = _from_json_nist(raw_dict)
            data = _from_data_nist(data)

        # Build pandas dataframe of data
        data = pandas.DataFrame(data, dtype='float64')

        # get the other data in the json
        other_keys = [column for column in data.columns.values
                      if column not in [loading_key, pressure_key]]

        # generate the isotherm
        isotherm = PointIsotherm(isotherm_data=data,
                                 loading_key=loading_key,
                                 pressure_key=pressure_key,
                                 other_keys=other_keys,
                                 **raw_dict)
    elif model:
        raise NotImplementedError
    else:
        # generate the isotherm
        isotherm = Isotherm(**raw_dict)

    return isotherm


def _from_json_nist(raw_dict):
    """
    Converts a NIST dictionary format to a internal format.
    """

    nist_dict = dict()

    # Get regular isotherm parameters
    nist_dict['material_name'] = raw_dict['adsorbent']['name']
    nist_dict['material_batch'] = raw_dict.pop('adsorbent')['hashkey']
    nist_dict['t_iso'] = raw_dict.pop('temperature')

    # Get adsorbate
    if len(raw_dict['adsorbates']) > 1:
        raise ParsingError('Cannot currently read multicomponent isotherms')
    nist_dict['adsorbate'] = raw_dict.pop('adsorbates')[0]['name']

    # Get loading basis and unit
    loading_string = raw_dict.pop("adsorptionUnits")
    comp = loading_string.split('/')
    if len(comp) != 2:
        raise ParsingError(
            "Isotherm cannot be parsed due to loading string format")

    loading_unit = comp[0]
    if loading_unit in _MOLAR_UNITS:
        loading_basis = 'molar'
    elif loading_unit in _MASS_UNITS:
        loading_basis = 'mass'
    elif loading_unit in _VOLUME_UNITS:
        loading_basis = 'volume'
    else:
        raise ParsingError("Isotherm cannot be parsed due to loading unit")

    adsorbent_unit = comp[1]
    if adsorbent_unit in _MASS_UNITS:
        adsorbent_basis = "mass"
    elif adsorbent_unit in _VOLUME_UNITS:
        adsorbent_basis = "volume"
    elif adsorbent_unit in _MOLAR_UNITS:
        adsorbent_basis = "molar"
    else:
        raise ParsingError("Isotherm cannot be parsed due to adsorbent basis")

    # Get pressure mode and unit
    pressure_mode = "absolute"
    pressure_string = raw_dict.pop("pressureUnits")

    if pressure_string in _PRESSURE_UNITS:
        pressure_unit = pressure_string
    else:
        raise ParsingError("Isotherm cannot be parsed due to pressure unit")

    # Add all the rest of the parameters
    nist_dict['iso_type'] = raw_dict.pop('category')      # exp/sim/mod/qua
    nist_dict['iso_ref'] = raw_dict.pop('isotherm_type')  # excess/absolute
    nist_dict.update(raw_dict)

    nist_dict.update({
        'adsorbent_basis': adsorbent_basis,
        'adsorbent_unit': adsorbent_unit,
        'loading_basis': loading_basis,
        'loading_unit': loading_unit,
        'pressure_mode': pressure_mode,
        'pressure_unit': pressure_unit,
    })

    return nist_dict


def _from_data_nist(raw_data):
    """
    Converts a NIST data format to a internal format.
    """

    for point in raw_data:
        point.pop('species_data')

    return raw_data
