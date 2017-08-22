"""
Parsing to and from json file format for isotherms
"""

import json

import pandas

from ..classes.pointisotherm import PointIsotherm


def isotherm_to_json(isotherm):
    """
    Converts an isotherm object to a json structure
    Structure is inspired by the NIST format
    """

    # Isotherm properties
    raw_dict = isotherm.to_dict()

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
                       ):
    """
    Converts a json isotherm format to a internal format
    Structure is inspired by the NIST format
    """

    # Parse isotherm in dictionary
    raw_dict = json.loads(json_isotherm)

    # Build pandas dataframe of data
    data = pandas.DataFrame.from_dict(
        raw_dict["isotherm_data"], orient='index', dtype='float64')
    del raw_dict["isotherm_data"]

    # convert index into int (seen as string)
    data.index = data.index.map(int)

    # sort index, in case the json was not sorted
    data.sort_index(inplace=True)

    # set dataframe keys
    loading_key = 'loading'
    pressure_key = 'pressure'
    other_keys = [column for column in data.columns.values if column not in [
        'loading', 'pressure']]

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


# def isotherm_from_json_nist(json_isotherm):
#     """
#     Converts a json isotherm format to a internal format
#     Structure is taken from the NIST format
#     """

#     # Parse isotherm in dictionary
#     raw_dict = json.loads(json_isotherm)

#     # Build info dictionary for internal format
#     info_dict = dict()

#     info_dict["exp_type"] = raw_dict['isotherm_type']
#     info_dict["name"] = raw_dict["adsorbentMaterial"]
#     info_dict["batch"] = raw_dict["DOI"]
#     info_dict["gas"] = raw_dict["adsorbateGas"]
#     info_dict["t_exp"] = raw_dict["temperature"]

#     # Get modes and units
#     mode_pressure = "absolute"  # raw_dict[""]
#     mode_adsorbent = "mass"    # raw_dict["mass"]
#     unit_pressure = raw_dict["pressureUnits"]
#     unit_loading = "mmol"      # raw_dict["mmol"]

#     # Build pandas dataframe of data

#     # Build pandas dataframe of data
#     data = pandas.DataFrame.from_dict(
#         raw_dict["isotherm_data"], orient='index', dtype='float64')
#     del raw_dict["isotherm_data"]

#     # convert index into int (seen as string)
#     data.index = data.index.map(int)

#     # sort index, in case the json was not sorted
#     data.sort_index(inplace=True)

#     # set dataframe keys
#     loading_key = "Loading"
#     pressure_key = "Pressure"

#     isotherm = PointIsotherm(data,
#                              loading_key=loading_key,
#                              pressure_key=pressure_key,
#                              mode_adsorbent=mode_adsorbent,
#                              mode_pressure=mode_pressure,
#                              unit_loading=unit_loading,
#                              unit_pressure=unit_pressure,
#                              **raw_dict)

#     return isotherm
