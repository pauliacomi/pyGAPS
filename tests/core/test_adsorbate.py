"""Tests relating to the Adsorbate class."""

import warnings

import pytest

import pygaps
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


@pytest.mark.core
class TestAdsorbate():
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
        ads = pygaps.Adsorbate("test")
        ads.properties["molar_mass"] = 142
        assert ads.molar_mass() == 142

    @pytest.mark.parametrize('calculated', [True, False])
    def test_adsorbate_named_props(self, adsorbate_data, basic_adsorbate, calculated):
        temp = 77.355
        assert basic_adsorbate.molar_mass(calculated) == pytest.approx(
            adsorbate_data.get('molar_mass'), 0.001
        )
        assert basic_adsorbate.saturation_pressure(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('saturation_pressure'), 0.001
        )
        assert basic_adsorbate.surface_tension(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('surface_tension'), 0.001
        )
        assert basic_adsorbate.liquid_density(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('liquid_density'), 0.001
        )
        assert basic_adsorbate.gas_density(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('gas_density'), 0.001
        )
        assert basic_adsorbate.enthalpy_liquefaction(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('enthalpy_liquefaction'), 0.001
        )

    def test_adsorbate_miss_named_props(self):
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

    def test_adsorbate_print(self, basic_adsorbate):
        """Check printing is possible."""
        print(basic_adsorbate)
        basic_adsorbate.print_info()
