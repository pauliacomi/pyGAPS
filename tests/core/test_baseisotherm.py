"""Tests relating to the Isotherm class."""

from copy import deepcopy

import numpy
import pytest

import pygaps
import pygaps.utilities.exceptions as pgEx
from pygaps.core.baseisotherm import BaseIsotherm


@pytest.mark.core
class TestBaseIsotherm:
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

    @pytest.mark.parametrize('kind', ['point', 'model'])
    @pytest.mark.parametrize('mode', ['absolute', 'relative'])
    def test_evaluation_input_defaults(self, monkeypatch, fractional_conversion_parameters, kind, mode):
        parameters = {**fractional_conversion_parameters, 'pressure_mode': mode}
        monkeypatch.setattr(parameters['adsorbate'], 'saturation_pressure', lambda temp, unit, pseudo=False: 1)
        cls = pygaps.PointIsotherm if kind == 'point' else pygaps.ModelIsotherm
        options = {} if kind == 'point' else {'model': 'Henry'}
        iso = cls(pressure=[1, 2, 3], loading=[2, 4, 6], branch='ads', **options, **parameters)

        assert iso.loading_at(2, pressure_mode=mode) == pytest.approx(4)
        assert iso.pressure_at(4, loading_basis='molar', material_basis='mass') == pytest.approx(2)
        assert iso.pressure_at(0.04, loading_basis='fraction') == pytest.approx(2)
        assert iso.pressure_at(4, loading_basis='percent') == pytest.approx(2)
        if kind == 'model':
            assert iso.spreading_pressure_at(2, pressure_mode=mode) == pytest.approx(4)
        if mode == 'relative':
            with pytest.raises(pgEx.ParameterError, match='pressure unit'):
                iso.loading_at(2, pressure_mode='absolute')
            assert iso.loading_at(2, pressure_mode='absolute', pressure_unit='bar') == pytest.approx(4)
            if kind == 'model':
                with pytest.raises(pgEx.ParameterError, match='pressure unit'):
                    iso.spreading_pressure_at(2, pressure_mode='absolute')

        for kwargs in [{'loading_basis': 'mass'}, {'material_basis': 'volume'}]:
            with pytest.raises(pgEx.ParameterError, match='unit'):
                iso.pressure_at(4, **kwargs)

    @pytest.mark.parametrize('kind', ['point', 'model'])
    def test_dimensionless_input_arrays(self, fractional_conversion_parameters, kind):
        cls = pygaps.PointIsotherm if kind == 'point' else pygaps.ModelIsotherm
        options = {} if kind == 'point' else {'model': 'Henry'}
        iso = cls(
            pressure=[1, 2, 3], loading=[2, 4, 6], branch='ads',
            **options, **fractional_conversion_parameters,
        )
        numpy.testing.assert_allclose(
            iso.pressure_at([0.08, 0.16], loading_basis='fraction', material_basis='volume', material_unit='cm3'),
            [1, 2],
        )
        numpy.testing.assert_allclose(
            iso.pressure_at([2, 4], loading_basis='percent', material_basis='mass'),
            [1, 2],
        )

    @pytest.mark.parametrize('kind', ['point', 'model'])
    @pytest.mark.parametrize('indexed', [False, True])
    @pytest.mark.parametrize('limits, expected', [
        ((None, 0), [0]), ((0, 0), [0]), ((0, 2), [0, 1, 2]),
        ((1, 2), [1, 2]), ((1, None), [1, 2]), ((None, None), [0, 1, 2]),
    ])
    def test_inclusive_data_limits(self, isotherm_parameters, kind, indexed, limits, expected):
        if kind == 'point':
            iso = pygaps.PointIsotherm(
                pressure=[0, 1, 2], loading=[0, 1, 2], branch='ads', **isotherm_parameters
            )
        else:
            iso = pygaps.ModelIsotherm(
                model=pygaps.modelling.model_from_dict({
                    'name': 'Henry', 'parameters': {'K': 1},
                    'pressure_range': (0, 2), 'loading_range': (0, 2),
                }),
                branch='ads', **isotherm_parameters,
            )
        for method in [iso.pressure, iso.loading]:
            kwargs = {'points': 3} if kind == 'model' else {}
            numpy.testing.assert_allclose(method(limits=limits, indexed=indexed, **kwargs), expected, atol=1e-12)
        if kind == 'point':
            iso.data_raw['other'] = [0, 1, 2]
            numpy.testing.assert_array_equal(iso.other_data('other', limits=limits, indexed=indexed), expected)

    def test_pressure_model_inclusive_limits(self, isotherm_parameters):
        iso = pygaps.ModelIsotherm(
            model=pygaps.modelling.model_from_dict({
                'name': 'Virial', 'parameters': {'K': 1, 'A': 0, 'B': 0, 'C': 0},
                'pressure_range': (1, 3), 'loading_range': (1, 3),
            }),
            branch='ads', **isotherm_parameters,
        )
        numpy.testing.assert_array_equal(iso.loading(points=3, limits=(1, 3)), [1, 2, 3])
        numpy.testing.assert_array_equal(iso.pressure(points=3, limits=(1, 3)), [1, 2, 3])

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

    @pytest.mark.parametrize('registered', [False, True])
    def test_isotherm_material_dictionary_snapshot(self, monkeypatch, registered):
        material = pygaps.Material(
            'local-material', density=2, molar_mass=10,
            provenance={'tags': ['registered']},
        )
        registry = [material] if registered else []
        monkeypatch.setattr('pygaps.core.material.MATERIAL_LIST', registry)
        supplied = {'name': material.name, 'density': 9, 'notes': {'tags': ['local']}}
        original = deepcopy(supplied)

        iso = BaseIsotherm(material=supplied, adsorbate='nitrogen', temperature=77)

        assert supplied == original
        assert iso.material is not material
        assert iso.material.density == 9
        assert material.density == 2
        assert len(registry) == int(registered)
        if registered:
            assert iso.material.molar_mass == 10
            iso.material.properties['provenance']['tags'].append('changed')
            assert material.properties['provenance'] == {'tags': ['registered']}
            material.molar_mass = 20
            assert iso.material.molar_mass == 10

        iso.material.properties['notes']['tags'].append('changed')
        assert supplied == original
        supplied['notes']['tags'].append('caller-edit')
        assert iso.material.properties['notes'] == {'tags': ['local', 'changed']}

    def test_isotherm_material_dictionary_does_not_register(self, monkeypatch):
        registry = []
        monkeypatch.setattr('pygaps.core.material.MATERIAL_LIST', registry)
        iso = BaseIsotherm(
            material={'name': 'local-material', 'store': True},
            adsorbate='nitrogen', temperature=77,
        )

        assert registry == []
        assert iso.material.properties['store'] is True

    @pytest.mark.parametrize('by_name', [False, True])
    def test_isotherm_material_explicit_sharing(self, monkeypatch, by_name):
        material = pygaps.Material('shared-material', density=2)
        monkeypatch.setattr('pygaps.core.material.MATERIAL_LIST', [material])
        iso = BaseIsotherm(
            material=material.name if by_name else material,
            adsorbate='nitrogen', temperature=77,
        )

        assert iso.material is material
        material.density = 9
        assert iso.material.density == 9

    @pytest.mark.parametrize('kind', ['point', 'model'])
    def test_isotherm_material_local_conversion(self, monkeypatch, fractional_conversion_parameters, kind):
        parameters = fractional_conversion_parameters
        material = parameters['material']
        monkeypatch.setattr('pygaps.core.material.MATERIAL_LIST', [material])
        cls = pygaps.PointIsotherm if kind == 'point' else pygaps.ModelIsotherm
        options = {} if kind == 'point' else {'model': 'Henry'}
        first = cls(pressure=[1., 2., 3.], loading=[2., 4., 6.], **options, **parameters)
        first_id = first.iso_id
        supplied = {'name': material.name, 'density': 9}
        second = cls(
            pressure=[1., 2., 3.], loading=[2., 4., 6.], **options,
            **{**parameters, 'material': supplied},
        )

        assert supplied == {'name': material.name, 'density': 9}
        assert first.iso_id == first_id
        assert first.material is material
        assert second.material is not material
        assert second.material.molar_mass == 10
        assert first.loading_at(1, material_basis='volume', material_unit='cm3') == pytest.approx(4)
        assert second.loading_at(1, material_basis='volume', material_unit='cm3') == pytest.approx(18)
        second.material.density = 5
        assert first.iso_id == first_id
        assert material.density == 2

    def test_isotherm_temperature(self):
        """Test various temperature functions."""
        isotherm = BaseIsotherm(m='carbon', a='nitrogen', t=303.15)
        isotherm.convert_temperature("°C")
        assert isotherm._temperature == 30.0
        assert isotherm.temperature == 303.15

    @pytest.mark.parametrize(
        'update',
        [
            ({'pressure_unit': 'Pa'}),
            ({'pressure_mode': 'absolute', 'pressure_unit': 'Pa'}),
            ({'pressure_mode': 'relative', 'pressure_unit': None}),
            ({'loading_basis': 'molar', 'loading_unit': 'mol'}),
            ({'loading_basis': 'mass', 'loading_unit': 'g'}),
            ({'material_basis': 'mass', 'material_unit': 'kg'}),
            ({'material_basis': 'volume', 'material_unit': 'cm3'}),
            (
                {
                    'temperature_unit': '°C',
                }
            ),
        ],
    )
    def test_isotherm_mode_and_units(self, isotherm_parameters, update):
        """Test unit specification."""
        isotherm_parameters.update(update)
        BaseIsotherm(**isotherm_parameters)

    @pytest.mark.parametrize(
        'prop, set_to',
        [
            ('pressure_unit', 'something'),
            ('pressure_mode', 'something'),
            ('loading_unit', 'something'),
            ('loading_basis', 'something'),
            ('material_unit', 'something'),
            ('material_basis', 'something'),
            ('temperature_unit', 'something'),
        ],
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
