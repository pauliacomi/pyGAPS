"""
This test module has tests relating to the isotherm class
"""

import pytest

import pygaps

from ..conftest import basic


@basic
class TestIsotherm(object):
    """
    Tests the parent isotherm object
    """

    def test_isotherm_create(self):
        "Checks isotherm can be created from test data"

        isotherm_param = {
            'is_real': False,
            'sample_name': 'carbon',
            'sample_batch': 'X1',
            'adsorbate': 'nitrogen',
            't_exp': 77,
        }

        isotherm = pygaps.classes.isotherm.Isotherm(
            loading_key='loading',
            pressure_key='pressure',
            ** isotherm_param)

        return isotherm

    @pytest.mark.parametrize('missing_key',
                             ['loading_key', 'pressure_key'])
    def test_isotherm_miss_key(self, isotherm_parameters, missing_key):
        "Tests exception throw for missing data primary key (loading/pressure)"

        keys = dict(
            pressure_key="pressure",
            loading_key="loading",
        )

        del keys[missing_key]

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(
                loading_key=keys.get('loading_key'),
                pressure_key=keys.get('pressure_key'),
                **isotherm_parameters)

        return

    @pytest.mark.parametrize('missing_param',
                             ['sample_name', 'sample_batch', 't_exp', 'adsorbate'])
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        "Tests exception throw for missing required attributes"

        data = isotherm_parameters
        del data[missing_param]

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(
                **isotherm_parameters)

        return

    @pytest.mark.parametrize('prop, set_to', [
                            ('unit_pressure', None),
                            ('unit_pressure', 'something'),
                            ('mode_pressure', None),
                            ('mode_pressure', 'something'),
                            ('unit_loading', None),
                            ('unit_loading', 'something'),
                            ('basis_loading', None),
                            ('basis_loading', 'something'),
                            ('unit_adsorbent', None),
                            ('unit_adsorbent', 'something'),
                            ('basis_adsorbent', None),
                            ('basis_adsorbent', 'something')])
    def test_isotherm_mode_and_units(self, isotherm_parameters, prop, set_to):
        "Tests exception throw for missing or wrong unit"

        props = dict(
            unit_adsorbent='g',
            basis_adsorbent='mass',
            basis_loading='molar',
            unit_loading='mmol',
            mode_pressure='absolute',
            unit_pressure='bar',
        )

        props[prop] = set_to

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(
                unit_adsorbent=props.get('unit_adsorbent'),
                basis_adsorbent=props.get('basis_adsorbent'),
                basis_loading=props.get('basis_loading'),
                unit_loading=props.get('unit_loading'),
                mode_pressure=props.get('mode_pressure'),
                unit_pressure=props.get('unit_pressure'),
                **isotherm_parameters)

        return

    def test_isotherm_get_parameters(self, isotherm_parameters, basic_isotherm):
        "Checks isotherm returns the same dict as was used to create it"

        assert isotherm_parameters == basic_isotherm.to_dict()

    def test_isotherm_print_parameters(self, basic_isotherm):
        "Checks isotherm can print its own info"

        print(basic_isotherm)
