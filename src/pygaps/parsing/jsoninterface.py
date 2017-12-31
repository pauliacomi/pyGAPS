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

    if fmt == 'NIST':
        raw_dict = _to_json_nist(raw_dict)

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
        # Build pandas dataframe of data
        data = pandas.DataFrame(data, dtype='float64')

        # Rename keys and get units if needed depending on format
        if fmt == 'NIST':
            loading_key = 'adsorption'
            pressure_key = 'pressure'
            raw_dict = _from_json_nist(raw_dict)

        # get the other data in the json
        other_keys = [column for column in data.columns.values
                      if column not in [loading_key, pressure_key]]

        # generate the isotherm
        isotherm = PointIsotherm(data,
                                 loading_key=loading_key,
                                 pressure_key=pressure_key,
                                 other_keys=other_keys,
                                 **raw_dict)
    elif model:
        pass
    else:
        # generate the isotherm
        isotherm = Isotherm(**raw_dict)

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


def _to_json_nist(raw_dict):
    """
    Converts an internal dictionary format to a NIST format.
    """
    nist_dict = dict()

    adsorbent_basis = raw_dict.pop('adsorbent_basis')
    # adsorbent_unit = raw_dict.pop('adsorbent_unit')
    # loading_basis = raw_dict.pop('loading_basis')
    loading_unit = raw_dict.pop('loading_unit')
    # pressure_mode = raw_dict.pop('pressure_mode')
    pressure_unit = raw_dict.pop('pressure_unit')

    nist_dict['adsorbentMaterial'] = raw_dict.pop('sample_name')
    nist_dict['hashkey'] = raw_dict.pop('sample_batch')
    nist_dict['temperature'] = raw_dict.pop('t_exp')

    internal_adsorbate = raw_dict.pop('adsorbate')
    nist_adsorbate = [k for k, v in NIST_ADSORBATES.items()
                      if v == internal_adsorbate]
    nist_dict['adsorbateGas'] = nist_adsorbate

    nist_dict["adsorptionUnits"] = '/'.join([loading_unit, adsorbent_basis])
    nist_dict["pressureUnits"] = pressure_unit

    # Add all the rest of the parameters
    nist_dict.update(raw_dict)

    return nist_dict


def _from_json_nist(raw_dict):
    """
    Converts a NIST dictionary format to a internal format.
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

    if comp[0] in _MOLAR_UNITS:
        loading_unit = comp[0]
        loading_basis = 'molar'
    elif comp[0] in _MASS_UNITS:
        loading_unit = comp[0]
        loading_basis = 'mass'
    elif comp[0] in _VOLUME_UNITS:
        loading_unit = comp[0]
        loading_basis = 'volume'
    else:
        raise ParsingError("Isotherm cannot be parsed due to loading unit")

    if comp[1] in _MASS_UNITS:
        adsorbent_unit = comp[1]
        adsorbent_basis = "mass"
    elif comp[1] in _VOLUME_UNITS:
        adsorbent_unit = comp[1]
        adsorbent_basis = "volume"
    elif comp[1] in _MOLAR_UNITS:
        adsorbent_unit = comp[1]
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
