"""Tests relating to the Adsorbate class."""

import warnings
from unittest.mock import Mock
from unittest.mock import call

import pytest

import pygaps
import pygaps.utilities.coolprop_utilities as coolprop
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


@pytest.mark.core
class TestAdsorbate:
    """Test the adsorbate class."""

    def test_adsorbate_basic(self):
        """Basic creation tests."""
        with pytest.raises(ParameterError):
            ads = pygaps.Adsorbate(None)
        ads = pygaps.Adsorbate('Test')
        assert ads == 'Test'
        assert ads == 'test'
        assert repr(ads) == "<pygaps.Adsorbate 'Test'>"
        assert str(ads) == 'Test'
        assert ads + '2' == 'Test2'
        assert 'i' + ads == 'iTest'
        assert hash(ads) == hash('Test')

    def test_adsorbate_alias(self):
        """Aliasing tests."""
        ads = pygaps.Adsorbate(name='Test', alias=['Test2'])
        assert ads == 'TEST'
        assert ads == 'test2'
        assert ads == 'Test2'
        assert all([alias in ads.alias for alias in ['test', 'test2']])
        ads = pygaps.Adsorbate(name='Test', alias='Test2')
        assert ads == 'TEST'
        assert ads == 'test2'
        assert ads == 'Test2'

    def test_adsorbate_create(self, adsorbate_data, basic_adsorbate):
        """Check adsorbate can be created from test data."""
        assert adsorbate_data == basic_adsorbate.to_dict()

    def test_adsorbate_retrieved_list(self, adsorbate_data, basic_adsorbate):
        """Check adsorbate can be retrieved from master list."""

        found_adsorbate = pygaps.Adsorbate.find(basic_adsorbate)
        assert basic_adsorbate == found_adsorbate

        pygaps.ADSORBATE_LIST.append(basic_adsorbate)
        uploaded_adsorbate = pygaps.Adsorbate.find(adsorbate_data.get('name'))

        assert adsorbate_data == uploaded_adsorbate.to_dict()

        with pytest.raises(ParameterError):
            pygaps.Adsorbate.find('noname')

        with pytest.raises(ParameterError):
            pygaps.Adsorbate.find(2)
        pygaps.ADSORBATE_LIST.remove(basic_adsorbate)

        uploaded = pygaps.Adsorbate("uploaded", store=True)
        assert uploaded == pygaps.Adsorbate.find('uploaded')

        pygaps.Adsorbate("not_uploaded", store=False)
        with pytest.raises(ParameterError):
            pygaps.Adsorbate.find('not_uploaded')

    def test_adsorbate_find_equals(self):
        """Check standard adsorbates can be found."""
        ads = pygaps.Adsorbate.find('N2')
        assert ads == 'N2'
        assert ads == 'nitrogen'
        assert ads == 'Nitrogen'

    def test_adsorbate_formula(self):
        """Check that formula is correctly latexed."""
        ads = pygaps.Adsorbate.find('N2')
        assert ads.formula == 'N_{2}'
        ads = pygaps.Adsorbate.find('D4')
        assert ads.formula == 'octamethylcyclotetrasiloxane'

    def test_adsorbate_get_properties(self, adsorbate_data, basic_adsorbate):
        """Check if properties of a adsorbate can be located."""

        assert basic_adsorbate.get_prop('backend_name') == adsorbate_data.get('backend_name')
        assert basic_adsorbate.backend_name == adsorbate_data.get('backend_name')

        name = basic_adsorbate.properties.pop('backend_name')
        with pytest.raises(ParameterError):
            name = basic_adsorbate.backend_name
        basic_adsorbate.properties['backend_name'] = name

    def test_adsorbate_fallback(self):
        """Check if fallback to properties dictionary works."""
        ads = pygaps.Adsorbate("test")
        ads.properties["molar_mass"] = 142
        assert ads.molar_mass() == 142

    def test_backend_cache_tracks_fluid_and_mode(self, monkeypatch):
        factory = Mock(side_effect=[Mock(), Mock(), Mock()])
        monkeypatch.setattr(coolprop.CP, 'AbstractState', factory)
        monkeypatch.setattr(coolprop, 'COOLPROP_BACKEND', 'HEOS')
        ads = pygaps.Adsorbate('custom', backend_name='Nitrogen')
        first = ads.backend
        assert ads.backend is first
        ads.properties['backend_name'] = 'Oxygen'
        second = ads.backend
        assert second is not first
        monkeypatch.setattr(coolprop, 'COOLPROP_BACKEND', 'REFPROP')
        assert ads.backend is not second
        assert factory.call_args_list == [
            call('HEOS', 'Nitrogen'), call('HEOS', 'Oxygen'), call('REFPROP', 'Oxygen'),
        ]
        assert '_backend_name' not in ads.to_dict()

    @pytest.mark.parametrize('change', ['fluid', 'mode'])
    def test_backend_failed_replacement_retries(self, monkeypatch, caplog, change):
        old_state = Mock()
        old_state.molar_mass.return_value = 0.028
        new_state = Mock()
        new_state.molar_mass.return_value = 0.032
        factory = Mock(side_effect=[old_state, ValueError('backend unavailable'), ValueError('backend unavailable'), new_state])
        monkeypatch.setattr(coolprop.CP, 'AbstractState', factory)
        monkeypatch.setattr(coolprop, 'COOLPROP_BACKEND', 'HEOS')
        ads = pygaps.Adsorbate('custom', backend_name='Nitrogen', molar_mass=30)
        assert ads.molar_mass() == pytest.approx(28)
        if change == 'fluid':
            ads.properties['backend_name'] = 'Oxygen'
        else:
            monkeypatch.setattr(coolprop, 'COOLPROP_BACKEND', 'REFPROP')

        assert ads.molar_mass() == 30
        assert ads.molar_mass() == 30
        assert ads._state is old_state
        assert (ads._backend_mode, ads._backend_name) == ('HEOS', 'Nitrogen')
        assert 'backend unavailable' in caplog.text
        assert ads.molar_mass() == pytest.approx(32)
        assert ads.backend is new_state
        assert factory.call_count == 4

    @pytest.mark.parametrize('mode', ['HEOS', 'REFPROP'])
    def test_direct_thermodynamic_calls_use_selected_backend(self, monkeypatch, mode):
        monkeypatch.setattr(coolprop, 'COOLPROP_BACKEND', mode)
        props = Mock(return_value=1)
        monkeypatch.setattr(coolprop.CP.CoolProp, 'PropsSI', props)
        ads = pygaps.Adsorbate('custom', backend_name='Nitrogen')

        assert ads.p_triple() == 1
        props.assert_called_with('PTRIPLE', f'{mode}::Nitrogen')
        assert ads.compressibility(100, 100000) == 1
        props.assert_called_with('Z', 'T', 100, 'P', 100000, f'{mode}::Nitrogen')

    @pytest.mark.parametrize('calculated', [True, False])
    def test_adsorbate_named_props(self, adsorbate_data, basic_adsorbate, calculated):
        """Test all named properties, both calculated and not."""
        temp = 77.355
        assert basic_adsorbate.molar_mass(calculated) == pytest.approx(adsorbate_data.get('molar_mass'), 0.001)
        assert basic_adsorbate.t_triple(calculated) == pytest.approx(adsorbate_data.get('t_triple'), 0.001)
        assert basic_adsorbate.p_triple(calculated) == pytest.approx(adsorbate_data.get('p_triple') * 1e5, 0.001)
        assert basic_adsorbate.t_critical(calculated) == pytest.approx(adsorbate_data.get('t_critical'), 0.001)
        assert basic_adsorbate.p_critical(calculated) == pytest.approx(adsorbate_data.get('p_critical') * 1e5, 0.001)
        assert basic_adsorbate.saturation_pressure(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('saturation_pressure'), 0.001
        )
        assert basic_adsorbate.surface_tension(temp, calculate=calculated) == pytest.approx(adsorbate_data.get('surface_tension'), 0.001)
        assert basic_adsorbate.liquid_density(temp, calculate=calculated) == pytest.approx(adsorbate_data.get('liquid_density'), 0.001)
        assert basic_adsorbate.gas_density(temp, calculate=calculated) == pytest.approx(adsorbate_data.get('gas_density'), 0.001)
        assert basic_adsorbate.enthalpy_liquefaction(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('enthalpy_liquefaction'), 0.001
        )

    def test_adsorbate_miss_named_props(self):
        """Test warning/error if properties cannot be calculated + are missing."""
        temp = 77.355
        ads = pygaps.Adsorbate(name='temp')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(CalculationError):
                ads.molar_mass()
            with pytest.raises(CalculationError):
                ads.saturation_pressure(temp)
            with pytest.raises(CalculationError):
                ads.surface_tension(temp)
            with pytest.raises(CalculationError):
                ads.liquid_density(temp)
            with pytest.raises(CalculationError):
                ads.gas_density(temp)
            with pytest.raises(CalculationError):
                ads.enthalpy_liquefaction(temp)

    @pytest.mark.parametrize('source, unit, expected', [
        ('calculated', None, 101325), ('calculated', 'Pa', 101325),
        ('calculated', 'bar', 1.01325), ('calculated', 'kPa', 101.325),
        ('stored', 'bar', 1.01325), ('fallback', 'bar', 1.01325),
    ])
    def test_saturation_pressure_units(self, monkeypatch, caplog, source, unit, expected):
        ads = pygaps.Adsorbate('custom', saturation_pressure=101325)
        state = Mock()
        state.p.return_value = 101325
        if source == 'fallback':
            state.update.side_effect = ValueError('backend unavailable')
        monkeypatch.setattr(pygaps.Adsorbate, 'backend', property(lambda self: state))

        assert ads.saturation_pressure(77, unit=unit, calculate=source != 'stored') == pytest.approx(expected)
        assert ads.pressure_saturation(77, unit=unit, calculate=source != 'stored') == pytest.approx(expected)
        if source == 'stored':
            state.update.assert_not_called()
        if source == 'fallback':
            assert 'backend unavailable' in caplog.text

    @pytest.mark.parametrize('calculate', [False, True])
    def test_saturation_pressure_invalid_unit(self, monkeypatch, calculate):
        ads = pygaps.Adsorbate('custom', saturation_pressure=101325)
        state = Mock()
        state.p.return_value = 101325
        monkeypatch.setattr(pygaps.Adsorbate, 'backend', property(lambda self: state))

        with pytest.raises(ParameterError, match='Unit selected'):
            ads.saturation_pressure(77, unit='invalid', calculate=calculate)

    @pytest.mark.parametrize('temp, unit, scale', [
        (200, None, 1), (200, 'Pa', 1), (200, 'bar', 1e5), (200, 'kPa', 1e3),
        (77, 'bar', 1e5), (100, 'bar', 1e5),
    ])
    def test_saturation_pressure_pseudo_units(self, monkeypatch, temp, unit, scale):
        ads = pygaps.Adsorbate('custom')
        monkeypatch.setattr(ads, 't_critical', lambda: 100)
        monkeypatch.setattr(ads, 'p_critical', lambda: 101325)
        state = Mock()
        state.p.return_value = 101325
        monkeypatch.setattr(pygaps.Adsorbate, 'backend', property(lambda self: state))
        expected = 101325 * ((temp / 100) ** 2 if temp >= 100 else 1) / scale

        assert ads.saturation_pressure_pseudo_dubinin(temp, unit=unit) == pytest.approx(expected)
        if temp > 100:
            assert ads.saturation_pressure(temp, unit=unit, pseudo='Dubinin') == pytest.approx(expected)

    @pytest.mark.parametrize('pseudo', [False, True, 'Dubinin'])
    @pytest.mark.parametrize('temp', [77, 200])
    def test_saturation_pressure_pseudo_boolean(self, monkeypatch, temp, pseudo):
        ads = pygaps.Adsorbate('custom')
        monkeypatch.setattr(ads, 't_critical', lambda: 100)
        monkeypatch.setattr(ads, 'p_critical', lambda: 100000)
        state = Mock()
        state.p.return_value = 50000
        monkeypatch.setattr(pygaps.Adsorbate, 'backend', property(lambda self: state))
        expected = 4 if pseudo and temp > 100 else 0.5

        assert ads.saturation_pressure(temp, unit='bar', pseudo=pseudo) == pytest.approx(expected)

    @pytest.mark.parametrize('temp', [77, 200])
    def test_saturation_pressure_unknown_pseudo(self, temp):
        with pytest.raises(ParameterError, match='pseudo'):
            pygaps.Adsorbate('custom').saturation_pressure(temp, pseudo='unknown')

    def test_adsorbate_print(self, basic_adsorbate):
        """Check printing is possible."""
        print(basic_adsorbate)
        basic_adsorbate.print_info()
