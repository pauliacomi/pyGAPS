"""
This test module has tests relating to parser classes
"""

import pytest
import json
import adsutils


@pytest.fixture
def basic_isotherm_json(isotherm_data):
    """
    Gives a json of the isotherm from model data
    """
    data = isotherm_data

    isotherm_dict = data.info

    isotherm_data_dict = data.isotherm_df.to_dict(orient='index')
    isotherm_data_dict = {str(k): {p: str(t) for p, t in v.items()}
                          for k, v in isotherm_data_dict.items()}
    isotherm_dict["isotherm_data"] = isotherm_data_dict

    return json.dumps(isotherm_dict)


def test_isotherm_to_json(basic_isotherm, basic_isotherm_json):
    """Tests the parsing of an isotherm to json"""

    test_isotherm_json = adsutils.isotherm_to_json(basic_isotherm)

    assert basic_isotherm_json == test_isotherm_json

    return


def test_isotherm_from_json(basic_isotherm, basic_isotherm_json):

    test_isotherm = adsutils.isotherm_from_json(basic_isotherm_json)

    assert basic_isotherm.id == test_isotherm.id
    assert basic_isotherm.sample_name == test_isotherm.sample_name
    assert basic_isotherm.sample_batch == test_isotherm.sample_batch
    assert basic_isotherm.t_exp == test_isotherm.t_exp
    assert basic_isotherm.gas == test_isotherm.gas

    assert basic_isotherm.data().equals(test_isotherm.data())

    return
