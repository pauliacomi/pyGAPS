"""
This test module has tests relating to the isotherm class
"""

import pytest

import pygaps


@pytest.mark.core
class TestIsotherm():
    """Test the basic isotherm object."""

    def test_isotherm_create(self):
        """Check isotherm can be created from test data."""

        pygaps.classes.isotherm.Isotherm(
            material_name='carbon',
            material_batch='X1',
            adsorbate='nitrogen',
            t_iso=77,
        )

    def test_isotherm_id(self, basic_isotherm):
        """Check isotherm id works as intended."""

        iso_id = basic_isotherm.iso_id

        basic_isotherm.new_param = 'changed'
        assert iso_id != basic_isotherm.iso_id
        basic_isotherm.t_iso = 0
        assert iso_id != basic_isotherm.iso_id

    @pytest.mark.parametrize('missing_param',
                             pygaps.classes.isotherm.Isotherm._required_params)
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        """Test exception throw for missing required attributes."""

        data = isotherm_parameters
        del data[missing_param]

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(**isotherm_parameters)

    @pytest.mark.parametrize('update', [
        ({'pressure_unit': 'Pa'}),
        ({'pressure_mode': 'absolute', 'pressure_unit': 'Pa'}),
        ({'pressure_mode': 'relative', 'pressure_unit': None}),
        ({'loading_basis': 'molar', 'loading_unit': 'mol'}),
        ({'loading_basis': 'mass', 'loading_unit': 'g'}),
        ({'adsorbent_basis': 'mass', 'adsorbent_unit': 'kg'}),
        ({'adsorbent_basis': 'volume', 'adsorbent_unit': 'cm3'}),
    ])
    def test_isotherm_mode_and_units(self, isotherm_parameters, update):
        """Test exception throw for missing or wrong unit."""

        isotherm_parameters.update(update)
        pygaps.classes.isotherm.Isotherm(**isotherm_parameters)

    @pytest.mark.parametrize('prop, set_to', [
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
        ('adsorbent_basis', 'something')
    ])
    def test_isotherm_mode_and_units_bad(self, isotherm_parameters, prop, set_to):
        """Test exception throw for missing or wrong unit."""

        isotherm_parameters[prop] = set_to

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.isotherm.Isotherm(**isotherm_parameters)

    def test_isotherm_get_parameters(self, isotherm_parameters, basic_isotherm):
        """Check isotherm returns the same dict as was used to create it."""

        iso_dict = basic_isotherm.to_dict()
        assert isotherm_parameters == iso_dict

    def test_isotherm_print_parameters(self, basic_isotherm):
        """Check isotherm can print its own info."""
        repr(basic_isotherm)
        print(basic_isotherm)
