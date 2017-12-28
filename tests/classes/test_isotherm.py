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

        iso_id = isotherm.id
        isotherm.nothing = 'changed'
        assert iso_id == isotherm.id
        isotherm.t_act = 123
        assert iso_id != isotherm.id

        return

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
                            ('pressure_unit', None),
                            ('pressure_unit', 'something'),
                            ('pressure_mode', None),
                            ('pressure_mode', 'something'),
                            ('loading_unit', None),
                            ('loading_unit', 'something'),
                            ('loading_basis', None),
                            ('loading_basis', 'something'),
                            ('adsorbent_unit', None),
                            ('adsorbent_unit', 'something'),
                            ('adsorbent_basis', None),
                            ('adsorbent_basis', 'something')])
    def test_isotherm_mode_and_units(self, isotherm_parameters, prop, set_to):
        "Tests exception throw for missing or wrong unit"

        isotherm_parameters[prop] = set_to

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(
                **isotherm_parameters)

        return

    def test_isotherm_get_parameters(self, isotherm_parameters, basic_isotherm):
        "Checks isotherm returns the same dict as was used to create it"

        iso_dict = basic_isotherm.to_dict()
        del iso_dict['id']
        assert isotherm_parameters == iso_dict

    def test_isotherm_print_parameters(self, basic_isotherm):
        "Checks isotherm can print its own info"

        print(basic_isotherm)
