"""
Configuration file for pytest and commonly used fixtures
"""
import matplotlib.pyplot as plt
import pandas
import pytest

import pygaps

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

# matplotlib functionality


@pytest.fixture(scope='function')
def noplot():
    plt.ioff()
    return


@pytest.fixture(scope='function')
def doplot():
    plt.ion()
    return

# Global fixtures


LOADING_KEY = 'loading'
PRESSURE_KEY = 'pressure'
OTHER_KEY = "enthalpy"


@pytest.fixture(scope='function')
def isotherm_parameters():
    """
    Creates a dictionary with all parameters for an model isotherm
    """

    parameters = {

        'sample_name': 'TEST',
        'sample_batch': 'TB',
        't_exp': 100.0,
        'adsorbate': 'TA',

        'date': '26/06/92',
        't_act': 100.0,
        'lab': 'TL',
        'comment': 'test comment',

        'user': 'TU',
        'project': 'TP',
        'machine': 'TM',
        'is_real': True,
        'exp_type': 'calorimetry',

        # Units/bases
        'adsorbent_basis': 'mass',
        'adsorbent_unit': 'g',
        'loading_basis': 'molar',
        'loading_unit': 'mmol',
        'pressure_mode': 'absolute',
        'pressure_unit': 'bar',

        # other properties

        'DOI': 'dx.doi/10.0000',
        'origin': 'test',
        'test_parameter': 'parameter',

    }

    return parameters


@pytest.fixture(scope='function')
def isotherm_data():
    """
    Creates a dataframe with all data for an model isotherm
    """
    isotherm_data = pandas.DataFrame({
        PRESSURE_KEY: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
        LOADING_KEY: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
        OTHER_KEY: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
    })

    return isotherm_data


@pytest.fixture(scope='function')
def basic_isotherm(isotherm_parameters):
    """
    Creates an basic isotherm from model data
    """
    isotherm = pygaps.classes.isotherm.Isotherm(**isotherm_parameters)

    return isotherm


@pytest.fixture(scope='function')
def basic_pointisotherm(isotherm_data, basic_isotherm):
    """
    Creates an isotherm from model data
    """
    other_keys = [OTHER_KEY]

    isotherm = pygaps.PointIsotherm.from_isotherm(
        basic_isotherm,
        isotherm_data,
        loading_key=LOADING_KEY,
        pressure_key=PRESSURE_KEY,
        other_keys=other_keys)

    return isotherm


@pytest.fixture()
def basic_modelisotherm(isotherm_data, basic_isotherm):
    """
    Creates an isotherm from model data
    """
    model = "Henry"

    isotherm = pygaps.ModelIsotherm.from_isotherm(
        basic_isotherm,
        isotherm_data,
        loading_key=LOADING_KEY,
        pressure_key=PRESSURE_KEY,
        model=model,
    )

    return isotherm


@pytest.fixture(scope='function')
def sample_data():
    """
    Creates an dict with all data for an model sample
    """
    sample_data = {
        'name': 'TEST',
        'batch': 'TB',
        'contact': 'TU',
        'source': 'TL',
        'project': 'TP',
        'struct': 'MOF-1',
        'type': 'MOF',
        'form': 'powder',
        'comment': 'test comment',

        'density': 10,  # g/cm3
        'poresize': 14,
        'molar_mass': 10,  # g/mol
    }

    return sample_data


@pytest.fixture(scope='function')
def basic_sample(sample_data):
    """
    Creates an sample from model data
    """
    sample = pygaps.Sample(**sample_data)

    return sample


@pytest.fixture(scope='session')
def adsorbate_data():
    """
    Creates an dict with all data for an model adsorbate
    """
    adsorbate_data = {
        'nick': 'TA',
        'formula': 'TA21',

        'common_name': 'nitrogen',
        'molar_mass': 28.01348,
        'cross_sectional_area': 0.162,
        'molecular_diameter': 0.3,
        'polarizability': 1.76E-30,
        'magnetic_susceptibility': 3.6E-35,
        'dipole_moment': 0.0,
        'quadrupole_moment': 1.52,
        'criticalp_temperature': 77.355,
        'criticalp_pressure': 34.0,
        'criticalp_density': 11.2,
        'triplep_temperature': 63.1,
        # properties for 1atm/ 77k
        'liquid_density': 0.806,
        'surface_density': 6.71e18,
        'surface_tension': 8.8796,
        'saturation_pressure': 101325,
        'enthalpy_liquefaction': 5.5796,
    }

    return adsorbate_data


@pytest.fixture(scope='function')
def basic_adsorbate(adsorbate_data):
    """
    Creates an sample from model data
    """
    adsorbate = pygaps.Adsorbate(**adsorbate_data)

    return adsorbate


@pytest.fixture()
def use_adsorbate(basic_adsorbate):
    """
    Uploads adsorbate to list
    """

    adsorbate = next(
        (x for x in pygaps.ADSORBATE_LIST if basic_adsorbate.name == x.name), None)
    if not adsorbate:
        pygaps.ADSORBATE_LIST.append(basic_adsorbate)

    return


@pytest.fixture()
def use_sample(basic_sample):
    """
    Uploads sample to list
    """

    sample = next(
        (x for x in pygaps.SAMPLE_LIST if basic_sample.name == x.name and basic_sample.batch == x.batch), None)
    if not sample:
        pygaps.SAMPLE_LIST.append(basic_sample)

    return
