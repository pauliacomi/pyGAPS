"""
This test module has tests relating to the isotherm class
"""

import pytest

import pygaps


class TestIsotherm(object):
    """
    Tests the parent isotherm object
    """

    def test_isotherm_created(self):
        "Checks isotherm can be created from test data"

        isotherm_param = {
            'is_real': False,
            'sample_name': 'carbon',
            'sample_batch': 'X1',
            'adsorbate': 'nitrogen',
            't_exp': 77,
        }

        isotherm = pygaps.classes.isotherm.Isotherm(**isotherm_param)

        return isotherm

    @pytest.mark.parametrize('missing_param',
                             ['sample_name', 'sample_batch', 't_exp', 'adsorbate'])
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        "Tests exception throw for missing required attributes"

        data = isotherm_parameters
        del data[missing_param]

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(
                **data)

        return

    @pytest.mark.parametrize('prop, set_to', [
                            ('basis_adsorbent', None),
                            ('basis_adsorbent', 'something'),
                            ('mode_pressure', None),
                            ('mode_pressure', 'something'),
                            ('unit_loading', None),
                            ('unit_loading', 'something'),
                            ('unit_pressure', None),
                            ('unit_pressure', 'something')])
    def test_isotherm_mode_and_units(self, isotherm_parameters, prop, set_to):
        "Tests exception throw for missing or wrong unit"

        props = dict(
            basis_adsorbent='mass',
            mode_pressure='absolute',
            unit_loading='mmol',
            unit_pressure='bar',
        )

        props[prop] = set_to

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(
                basis_adsorbent=props.get('basis_adsorbent'),
                mode_pressure=props.get('mode_pressure'),
                unit_loading=props.get('unit_loading'),
                unit_pressure=props.get('unit_pressure'),
                **isotherm_parameters)

        return

    def test_isotherm_get_parameters(self, isotherm_parameters, basic_isotherm):
        "Checks isotherm returns the same dict as was used to create it"

        assert isotherm_parameters == basic_isotherm.to_dict()

    def test_isotherm_print_parameters(self, basic_isotherm, noplot):
        "Checks isotherm can print its own info"

        print(basic_isotherm)
