"""
Configuration file for pytest and commonly used fixtures
"""
import sys

import pandas
import pytest

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
def isotherm_parameters():
    """
    Creates a dictionary with all parameters for an model isotherm
    """

    isotherm_parameters = {
        'id': None,

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

        # other properties

        'DOI': 'dx.doi/10.0000',
        'origin': 'test',
        'test_parameter': 'parameter'
    }

    return isotherm_parameters


@pytest.fixture(scope='function')
def isotherm_data(basic_isotherm):
    """
    Creates a dataframe with all data for an model isotherm
    """

    other_key = "enthalpy"

    isotherm_data = pandas.DataFrame({
        basic_isotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
        basic_isotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
        other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
    })

    return isotherm_data


@pytest.fixture(scope='function')
def basic_isotherm(isotherm_parameters):
    """
    Creates an basic isotherm from model data
    """
    pressure_key = "pressure"
    loading_key = "loading"

    isotherm = adsutils.classes.isotherm.Isotherm(
        loading_key=loading_key,
        pressure_key=pressure_key,
        **isotherm_parameters)

    return isotherm


@pytest.fixture(scope='function')
def basic_pointisotherm(isotherm_data, basic_isotherm):
    """
    Creates an isotherm from model data
    """
    other_key = "enthalpy"
    other_keys = [other_key]

    isotherm = adsutils.PointIsotherm.from_isotherm(
        basic_isotherm,
        isotherm_data,
        other_keys=other_keys)

    return isotherm


def basic_modelisotherm(isotherm_data, basic_isotherm):
    """
    Creates an isotherm from model data
    """
    model = "Langmuir"

    isotherm = adsutils.ModelIsotherm.from_isotherm(
        basic_isotherm,
        isotherm_data,
        model)

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
                'density': 22.5,  # g/cm3
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
            'common_name': 'nitrogen',
            'molar_mass': 28.01348,
            'cross_sectional_area': 0.162,
            'polarizability': 17.4,
            'dipole_moment': 0.0,
            'quadrupole_moment': 1.52,
            'criticalp_temperature': 77.355,
            'criticalp_pressure': 34.0,
            'criticalp_density': 11.2,
            'triplep_temperature': 63.1,
            # properties for 1atm/ 77k
            'liquid_density': 0.806,
            'surface_tension': 8.8796,
            'saturation_pressure': 101325,
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
