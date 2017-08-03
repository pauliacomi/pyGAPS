"""
Configuration file for pytest and commonly used fixtures
"""
import sys
import pytest
import pandas
import adsutils

windows = pytest.mark.skipif(
    sys.platform != 'win32', reason="requires windows")


@pytest.fixture(scope='function')
def isotherm_data():
    """
    Creates an class with all data for an model isotherm
    """

    class IsothermData():
        pressure_key = "Pressure"
        loading_key = "Loading"

        other_key = "enthalpy_key"
        other_keys = {other_key: "Enthalpy"}

        isotherm_df = pandas.DataFrame({
            pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
            loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
            other_keys[other_key]: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        })

        info = {'id': 0,
                'sample_name': 'TEST',
                'sample_batch': 'TB',
                't_exp': 100,
                'gas': 'N2',

                'date': '26/06/92',
                't_act': 100,
                'lab': 'TL',
                'comment': 'test comment',

                'user': 'TU',
                'project': 'TP',
                'machine': 'M1',
                'is_real': 'True',
                'exp_type': 'Calorimetry',

                'other_properties': {
                    'DOI': 'dx.doi/10.0000',
                    'origin': 'test',
                }
                }

    return IsothermData()


@pytest.fixture(scope='function')
def basic_isotherm(isotherm_data):
    """
    Creates an isotherm from model data
    """
    data = isotherm_data

    isotherm = adsutils.PointIsotherm(
        data.isotherm_df,
        loading_key=data.loading_key,
        pressure_key=data.pressure_key,
        other_keys=data.other_keys,
        **data.info)

    return isotherm
