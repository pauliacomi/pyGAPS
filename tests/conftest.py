"""
Configuration file for pytest and commonly used fixtures
"""
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
    return pandas.DataFrame({
        "pressure": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
        "loading": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
        "enthalpy": [5.2, 5.1, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
        "text_data": ["a", "b", "c", "d", "e", "f", "g", "h"],
    })


@pytest.fixture(scope='function')
def basic_isotherm(isotherm_parameters):
    """Create a basic isotherm from basic data."""
    return pygaps.core.baseisotherm.BaseIsotherm(**isotherm_parameters)


@pytest.fixture(scope='function')
def basic_pointisotherm(isotherm_data, isotherm_parameters):
    """Create a point isotherm from basic data."""
    return pygaps.PointIsotherm(
        isotherm_data=isotherm_data,
        loading_key="loading",
        pressure_key="pressure",
        **isotherm_parameters
    )


@pytest.fixture()
def basic_modelisotherm(isotherm_data, isotherm_parameters):
    """Creates a model isotherm from basic data."""
    return pygaps.ModelIsotherm(
        isotherm_data=isotherm_data,
        loading_key="loading",
        pressure_key="pressure",
        model="Henry",
        **isotherm_parameters
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
    pygaps.MATERIAL_LIST.append(basic_material)
    yield
    pygaps.MATERIAL_LIST.pop()


@pytest.fixture(scope='session')
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


@pytest.fixture(scope='function')
def basic_adsorbate(adsorbate_data):
    """Create a basic adsorbate from model data."""
    return pygaps.Adsorbate(**adsorbate_data)


@pytest.fixture(scope='function')
def use_adsorbate(basic_adsorbate):
    """Upload basic adsorbate to global list."""
    pygaps.ADSORBATE_LIST.append(basic_adsorbate)
    yield
    pygaps.ADSORBATE_LIST.pop()
