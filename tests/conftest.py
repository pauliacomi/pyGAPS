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
    """Create a dictionary with all parameters for an isotherm."""

    return {

        'material_name': 'TEST',
        'material_batch': 'TB',
        't_iso': 100.0,
        'adsorbate': 'TA',

        'date': '26/06/92',
        't_act': 100.0,
        'lab': 'TL',
        'comment': 'test comment',

        'user': 'TU',
        'project': 'TP',
        'machine': 'TM',
        'is_real': True,
        'iso_type': 'calorimetry',

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

        # No warnings
        'warn_off': True
    }


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
    """Create a basic isotherm from basic data."""
    return pygaps.classes.isotherm.Isotherm(no_warn=True, **isotherm_parameters)


@pytest.fixture(scope='function')
def basic_pointisotherm(isotherm_data, isotherm_parameters):
    """Create a point isotherm from basic data."""
    other_keys = [OTHER_KEY]

    isotherm = pygaps.PointIsotherm(
        isotherm_data=isotherm_data,
        loading_key=LOADING_KEY,
        pressure_key=PRESSURE_KEY,
        other_keys=other_keys,
        no_warn=True,
        **isotherm_parameters
    )

    return isotherm


@pytest.fixture()
def basic_modelisotherm(isotherm_data, isotherm_parameters):
    """Creates a model isotherm from basic data."""
    model = "Henry"

    isotherm = pygaps.ModelIsotherm(
        isotherm_data=isotherm_data,
        loading_key=LOADING_KEY,
        pressure_key=PRESSURE_KEY,
        model=model,
        no_warn=True,
        **isotherm_parameters
    )

    return isotherm


@pytest.fixture(scope='function')
def material_data():
    """
    Creates an dict with all data for an model material
    """
    m_data = {
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

    return m_data


@pytest.fixture(scope='function')
def basic_material(material_data):
    """
    Creates an material from model data
    """
    material = pygaps.Material(**material_data)

    return material


@pytest.fixture(scope='session')
def adsorbate_data():
    """
    Creates an dict with all data for an model adsorbate
    """
    adsorbate_data = {
        'name': 'TA',
        'formula': 'TA21',

        'backend_name': 'nitrogen',
        'molar_mass': 28.01348,
        'cross_sectional_area': 0.162,
        'molecular_diameter': 0.3,
        'polarizability': 1.76E-3,
        'magnetic_susceptibility': 3.6E-8,
        'dipole_moment': 0.0,
        'quadrupole_moment': 1.52,
        't_critical': 77.355,
        'p_critical': 34.0,
        'rhomolar_critical': 11.2,
        't_triple': 63.1,
        # properties for 1atm/ 77k
        'gas_density': 0.00461214,
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
    Creates an material from model data
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
def use_material(basic_material):
    """
    Uploads material to list
    """

    material = next(
        (x for x in pygaps.MATERIAL_LIST if basic_material.name == x.name and basic_material.batch == x.batch), None)
    if not material:
        pygaps.MATERIAL_LIST.append(basic_material)

    return
