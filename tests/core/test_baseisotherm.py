"""Tests relating to the Isotherm class."""

import pytest

import pygaps
import pygaps.utilities.exceptions as pgEx
from pygaps.core.baseisotherm import BaseIsotherm


@pytest.mark.core
class TestBaseIsotherm():
    """Test the basic isotherm object."""
    def test_isotherm_create(self):
        """Check isotherm can be created from test data."""
        BaseIsotherm(
            material='carbon',
            adsorbate='nitrogen',
            temperature=77,
        )

    def test_isotherm_create_short(self):
        """Check isotherm can be created from shorthands."""
        BaseIsotherm(m='carbon', a='nitrogen', t=77)

    def test_isotherm_id(self, basic_isotherm):
        """Check isotherm id works as intended."""
        iso_id = basic_isotherm.iso_id
        basic_isotherm.new_param = 'changed'
        assert iso_id != basic_isotherm.iso_id
        basic_isotherm.temperature = 0
        assert iso_id != basic_isotherm.iso_id

    @pytest.mark.parametrize('missing_param', BaseIsotherm._required_params)
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        """Test exception throw for missing required attributes."""
        data = isotherm_parameters
        del data[missing_param]
        with pytest.raises(pgEx.ParameterError):
            BaseIsotherm(**isotherm_parameters)

    def test_isotherm_adsorbate(self):
        """Test various adsorbate functions."""
        isotherm = BaseIsotherm(m='carbon', a='nitrogen', t=77)
        assert isotherm._adsorbate == isotherm.adsorbate
        assert isinstance(isotherm.adsorbate, pygaps.Adsorbate)
        isotherm.adsorbate = "oxygen"
        assert isinstance(isotherm.adsorbate, pygaps.Adsorbate)

    def test_isotherm_material(self, basic_material, use_material):
        """Test various material functions."""
        isotherm = BaseIsotherm(m='carbon', a='nitrogen', t=77)
        assert isotherm._material == isotherm.material
        assert isinstance(isotherm.material, pygaps.Material)
        isotherm.material = "zeolite"
        assert isinstance(isotherm.material, pygaps.Material)
        isotherm.material = {'name': "testing"}
        assert isotherm.material == "testing"
        isotherm.material = {'name': "TEST"}
        assert isotherm.material == basic_material

    def test_isotherm_temperature(self):
        """Test various temperature functions."""
        isotherm = BaseIsotherm(m='carbon', a='nitrogen', t=303.15)
        isotherm.convert_temperature("°C")
        assert isotherm._temperature == 30.0
        assert isotherm.temperature == 303.15

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
            ({
                'temperature_unit': '°C',
            }),
        ]
    )
    def test_isotherm_mode_and_units(self, isotherm_parameters, update):
        """Test unit specification."""
        isotherm_parameters.update(update)
        BaseIsotherm(**isotherm_parameters)

    @pytest.mark.parametrize(
        'prop, set_to', [
            ('pressure_unit', 'something'),
            ('pressure_mode', 'something'),
            ('loading_unit', 'something'),
            ('loading_basis', 'something'),
            ('material_unit', 'something'),
            ('material_basis', 'something'),
            ('temperature_unit', 'something'),
        ]
    )
    def test_isotherm_mode_and_units_bad(self, isotherm_parameters, prop, set_to):
        """Test exception throw for missing or wrong unit."""
        isotherm_parameters[prop] = set_to
        with pytest.raises(pgEx.ParameterError):
            BaseIsotherm(**isotherm_parameters)

    def test_isotherm_unit_dict(self, basic_isotherm):
        """Test combined unit dict ouput."""
        units = basic_isotherm.units
        assert all(unit in units for unit in BaseIsotherm._unit_params)

    def test_isotherm_convert_temperature(self, basic_isotherm):
        """Test if temperatures can be converted."""
        temp = basic_isotherm.temperature
        assert temp == basic_isotherm._temperature

        basic_isotherm.convert_temperature(unit_to="°C", verbose=True)
        basic_isotherm.convert_temperature(unit_to="K", verbose=True)

        assert temp == basic_isotherm.temperature

    def test_isotherm_get_parameters(self, isotherm_parameters, basic_isotherm):
        """Check isotherm returns the same dict as was used to create it."""

        iso_dict = basic_isotherm.to_dict()
        assert isotherm_parameters == iso_dict

    def test_isotherm_print_parameters(self, basic_isotherm):
        """Check isotherm can print its own info."""
        repr(basic_isotherm)
        print(basic_isotherm)
