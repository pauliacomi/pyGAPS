"""
Configuration file for pytest and commonly used fixtures
"""
import sys
import pytest
import pandas
import adsutils

# Run only on windows
windows = pytest.mark.skipif(
    sys.platform != 'win32', reason="requires windows")

# Incremental tests


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


# Global fixtures
@pytest.fixture(scope='function')
def isotherm_data():
    """
    Creates an class with all data for an model isotherm
    """

    class IsothermData():
        pressure_key = "pressure"
        loading_key = "loading"

        other_key = "enthalpy_key"
        other_keys = {other_key: "enthalpy"}

        isotherm_df = pandas.DataFrame({
            pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
            loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
            other_keys[other_key]: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        })

        info = {
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
            'machine': 'TM',
            'is_real': 'True',
            'exp_type': 'calorimetry',

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


@pytest.fixture(scope='function')
def sample_data():
    """
    Creates an dict with all data for an model sample
    """
    sample_data = {
        'name': 'TEST',
        'batch': 'TB',
        'owner': 'TU',
        'contact': 'TU',
        'source_lab': 'TL',
        'project': 'TP',
        'struct': 'MOF-1',
        'type': 'MOF',
        'form': 'powder',
        'comment': 'test comment',

        'properties': {
                'density': 22.5,
                'poresize': 14,
        }
    }

    return sample_data


@pytest.fixture(scope='function')
def basic_sample(sample_data):
    """
    Creates an sample from model data
    """
    sample = adsutils.Sample(sample_data)

    return sample


@pytest.fixture(scope='session')
def gas_data():
    """
    Creates an dict with all data for an model gas
    """
    gas_data = {
        'nick': 'N2',
        'formula': 'N2',

        'properties': {
            'molar_mass': 14,
            'polarizability': 22.5,
            'dipole': 14,
            'quadrupole': 14,
            'critical_t': 14,
        }
    }

    return gas_data


@pytest.fixture(scope='function')
def basic_gas(gas_data):
    """
    Creates an sample from model data
    """
    gas = adsutils.Gas(gas_data)

    return gas
