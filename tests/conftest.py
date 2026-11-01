"""
Configuration file for pytest and commonly used fixtures
"""

import os
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'

import matplotlib

matplotlib.use('Agg')

import pandas
import pytest

import pygaps

from .test_utils import isolated_pygaps_state
from .test_utils import plotting_context
from .test_utils import registered_object

DATA_PATH = Path(__file__).parent / 'test_data'


def pytest_configure(config):
    """Set global variables for pytest."""
    config.DATA_PATH = DATA_PATH


def pytest_addoption(parser):
    parser.addoption(
        '--reverse-independent',
        action='store_true',
        help='Reverse independent test order; exclude tests/parsing/test_sqlite_db.py and run it separately.',
    )


@pytest.fixture(autouse=True)
def isolate_plotting_state():
    """Protect nondecorated tests without imposing a different plotting style."""
    with plotting_context({}):
        yield


@pytest.fixture(autouse=True)
def isolate_global_state():
    with isolated_pygaps_state():
        yield


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    yield
    reverse = config.getoption('reverse_independent')
    if reverse:
        items.reverse()
    scenario = [item for item in items if item.path == DATA_PATH.parent / 'parsing' / 'test_sqlite_db.py']
    if not scenario:
        return
    if reverse:
        raise pytest.UsageError('Exclude the shared SQLite scenario when using --reverse-independent; run it separately.')
    if config.getoption('numprocesses', default=0) or hasattr(config, 'workerinput'):
        raise pytest.UsageError('The shared SQLite scenario must run serially, without distributed scheduling.')
    declaration_order = [name for name in vars(scenario[0].cls) if name.startswith('test_')]
    selected_order = [item.originalname for item in scenario]
    if selected_order != [name for name in declaration_order if name in selected_order]:
        raise pytest.UsageError('The shared SQLite scenario must retain its declared step order; reorder independent tests separately.')


# Global fixtures
@pytest.fixture(scope='function')
def isotherm_parameters():
    """Create a dictionary with all parameters for an isotherm."""
    return {
        'material': 'TEST',
        'temperature': 100.0,
        'adsorbate': 'TA',
        'date': '26/06/92',
        'activation_temperature': 100.0,
        'lab': 'TL',
        'comment': 'test comment',
        'user': 'TU',
        'project': 'TP',
        'machine': 'TM',
        'iso_type': 'calorimetry',
        # Units/bases
        'material_basis': 'mass',
        'material_unit': 'g',
        'loading_basis': 'molar',
        'loading_unit': 'mmol',
        'pressure_mode': 'absolute',
        'pressure_unit': 'bar',
        'temperature_unit': 'K',
        # other properties
        'DOI': 'dx.doi/10.0000',
        'origin': 'test',
        'test_parameter': 'parameter',
    }


@pytest.fixture(scope='function')
def isotherm_data():
    """Create a dataframe with all data for an model isotherm."""
    return pandas.DataFrame(
        {
            "pressure": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            "loading": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            "enthalpy": [5.2, 5.1, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
            "text_data": ["a", "b", "c", "d", "e", "f", "g", "h"],
        }
    )


@pytest.fixture(scope='function')
def basic_isotherm(isotherm_parameters):
    """Create a basic isotherm from basic data."""
    return pygaps.core.baseisotherm.BaseIsotherm(**isotherm_parameters)


@pytest.fixture(scope='function')
def basic_pointisotherm(isotherm_data, isotherm_parameters):
    """Create a point isotherm from basic data."""
    return pygaps.PointIsotherm(isotherm_data=isotherm_data, loading_key="loading", pressure_key="pressure", **isotherm_parameters)


@pytest.fixture()
def basic_modelisotherm(isotherm_data, isotherm_parameters):
    """Creates a model isotherm from basic data."""
    return pygaps.ModelIsotherm(
        isotherm_data=isotherm_data, loading_key="loading", pressure_key="pressure", model="Henry", **isotherm_parameters
    )


@pytest.fixture(scope='function')
def material_data():
    """Create an dict with all data for an model material."""
    return {
        'name': 'TEST',
        'batch': 'TB',
        'contact': 'TU',
        'source': 'TL',
        'project': 'TP',
        'struct': 'MOF-1',
        'type': 'MOF',
        'form': 'powder',
        'comment': 'test comment',
        'density': 2.0,  # g/cm3
        'poresize': 14.0,
        'molar_mass': 10.0,  # g/mol
    }


@pytest.fixture(scope='function')
def basic_material(material_data):
    """Create a material from model data."""
    return pygaps.Material(**material_data)


@pytest.fixture(scope='function')
def use_material(basic_material):
    """Upload basic material to global list."""
    with registered_object(pygaps.MATERIAL_LIST, basic_material):
        yield


@pytest.fixture(scope='function')
def adsorbate_data():
    """Create a dict with all data for an model adsorbate."""
    return {
        'name': 'TA',
        'alias': ['ta1', 'ta2', 'ta'],
        'formula': 'TA21',
        'backend_name': 'NITROGEN',
        'molar_mass': 28.01348,
        'cross_sectional_area': 0.162,
        'molecular_diameter': 0.3,
        'polarizability': 1.76e-3,
        'magnetic_susceptibility': 3.6e-8,
        'dipole_moment': 0.0,
        'quadrupole_moment': 1.52,
        't_critical': 126.2,
        'p_critical': 33.95,
        't_triple': 63.1,
        'p_triple': 0.1252,
        'rhomolar_critical': 11.2,
        # properties for 1atm/ 77k
        'gas_density': 0.00461214,
        'liquid_density': 0.806,
        'surface_density': 6.71e18,
        'surface_tension': 8.8796,
        'saturation_pressure': 101325,
        'enthalpy_liquefaction': 5.5796,
    }


@pytest.fixture(scope='function')
def basic_adsorbate(adsorbate_data):
    """Create a basic adsorbate from model data."""
    return pygaps.Adsorbate(**adsorbate_data)


@pytest.fixture(scope='function')
def use_adsorbate(basic_adsorbate):
    """Upload basic adsorbate to global list."""
    with registered_object(pygaps.ADSORBATE_LIST, basic_adsorbate):
        yield
