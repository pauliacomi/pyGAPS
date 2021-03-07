"""Tests relating to the Isotherm class."""

import pytest

import pygaps
import pygaps.utilities.exceptions as pgEx


@pytest.mark.core
class TestBaseIsotherm():
    """Test the basic isotherm object."""
    def test_isotherm_create(self):
        """Check isotherm can be created from test data."""

        pygaps.core.baseisotherm.BaseIsotherm(
            material='carbon',
            adsorbate='nitrogen',
            temperature=77,
        )

    def test_isotherm_id(self, basic_isotherm):
        """Check isotherm id works as intended."""

        iso_id = basic_isotherm.iso_id

        basic_isotherm.new_param = 'changed'
        assert iso_id != basic_isotherm.iso_id
        basic_isotherm.temperature = 0
        assert iso_id != basic_isotherm.iso_id

    @pytest.mark.parametrize(
        'missing_param', pygaps.core.baseisotherm.BaseIsotherm._required_params
    )
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        """Test exception throw for missing required attributes."""

        data = isotherm_parameters
        del data[missing_param]

        with pytest.raises(pgEx.ParameterError):
            pygaps.core.baseisotherm.BaseIsotherm(**isotherm_parameters)

    @pytest.mark.parametrize(
        'update', [
            ({
                'pressure_unit': 'Pa'
            }),
            ({
                'pressure_mode': 'absolute',
                'pressure_unit': 'Pa'
            }),
            ({
                'pressure_mode': 'relative',
                'pressure_unit': None
            }),
            ({
                'loading_basis': 'molar',
                'loading_unit': 'mol'
            }),
            ({
                'loading_basis': 'mass',
                'loading_unit': 'g'
            }),
            ({
                'material_basis': 'mass',
                'material_unit': 'kg'
            }),
            ({
                'material_basis': 'volume',
                'material_unit': 'cm3'
            }),
        ]
    )
    def test_isotherm_mode_and_units(self, isotherm_parameters, update):
        """Test exception throw for missing or wrong unit."""

        isotherm_parameters.update(update)
        pygaps.core.baseisotherm.BaseIsotherm(**isotherm_parameters)

    @pytest.mark.parametrize(
        'prop, set_to', [('pressure_unit', 'something'),
                         ('pressure_mode', 'something'),
                         ('loading_unit', 'something'),
                         ('loading_basis', 'something'),
                         ('material_unit', 'something'),
                         ('material_basis', 'something')]
    )
    def test_isotherm_mode_and_units_bad(
        self, isotherm_parameters, prop, set_to
    ):
        """Test exception throw for missing or wrong unit."""

        isotherm_parameters[prop] = set_to

        with pytest.raises(pgEx.ParameterError):
            pygaps.core.baseisotherm.BaseIsotherm(**isotherm_parameters)

    def test_isotherm_get_parameters(
        self, isotherm_parameters, basic_isotherm
    ):
        """Check isotherm returns the same dict as was used to create it."""

        iso_dict = basic_isotherm.to_dict()
        assert isotherm_parameters == iso_dict

    def test_isotherm_print_parameters(self, basic_isotherm):
        """Check isotherm can print its own info."""
        repr(basic_isotherm)
        print(basic_isotherm)
