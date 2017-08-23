"""
This test module has tests relating to parser classes
"""

import json

import pytest

import adsutils


@pytest.fixture
def basic_isotherm_json(isotherm_data, basic_pointisotherm):
    """
    Gives a json of the isotherm from model data
    """

    isotherm_dict = basic_pointisotherm.to_dict()
    isotherm_dict.update({'id': basic_pointisotherm.id})

    isotherm_data_dict = basic_pointisotherm.data().to_dict(orient='index')
    isotherm_data_dict = {str(k): {p: str(t) for p, t in v.items()}
                          for k, v in isotherm_data_dict.items()}
    isotherm_dict["isotherm_data"] = isotherm_data_dict

    return json.dumps(isotherm_dict, sort_keys=True)


def test_isotherm_to_json(basic_pointisotherm, basic_isotherm_json):
    """Tests the parsing of an isotherm to json"""

    test_isotherm_json = adsutils.isotherm_to_json(basic_pointisotherm)

    assert basic_isotherm_json == test_isotherm_json

    return


def test_isotherm_from_json(basic_pointisotherm, basic_isotherm_json):

    test_isotherm = adsutils.isotherm_from_json(basic_isotherm_json)
    assert basic_pointisotherm == test_isotherm

    return
