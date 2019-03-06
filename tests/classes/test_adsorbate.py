"""
This test module has tests relating to the adsorbate class
"""

import warnings

import pytest

import pygaps


@pytest.mark.core
class TestAdsorbate():
    """
    Tests the adsorbate class
    """

    def test_adsorbate_create(self, adsorbate_data, basic_adsorbate):
        "Checks adsorbate can be created from test data"

        assert adsorbate_data == basic_adsorbate.to_dict()

    def test_adsorbate_retrieved_list(self, adsorbate_data, basic_adsorbate):
        "Checks adsorbate can be retrieved from master list"
        pygaps.data.ADSORBATE_LIST.append(basic_adsorbate)
        uploaded_adsorbate = pygaps.Adsorbate.find(
            adsorbate_data.get('name'))

        assert adsorbate_data == uploaded_adsorbate.to_dict()

        with pytest.raises(pygaps.ParameterError):
            pygaps.Adsorbate.find('noname')

    def test_adsorbate_get_properties(self, adsorbate_data, basic_adsorbate):
        "Checks if properties of a adsorbate can be located"

        assert basic_adsorbate.get_prop('backend_name') == adsorbate_data.get('backend_name')
        assert basic_adsorbate.backend_name() == adsorbate_data.get('backend_name')

        name = basic_adsorbate.properties.pop('backend_name')
        with pytest.raises(pygaps.ParameterError):
            basic_adsorbate.backend_name()
        basic_adsorbate.properties['backend_name'] = name

    @pytest.mark.parametrize('calculated', [True, False])
    def test_adsorbate_named_props(self, adsorbate_data, basic_adsorbate, calculated):
        temp = 77.355
        assert basic_adsorbate.molar_mass(calculated) == pytest.approx(
            adsorbate_data.get('molar_mass'), 0.001)
        assert basic_adsorbate.saturation_pressure(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('saturation_pressure'), 0.001)
        assert basic_adsorbate.surface_tension(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('surface_tension'), 0.001)
        assert basic_adsorbate.liquid_density(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('liquid_density'), 0.001)
        assert basic_adsorbate.gas_density(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('gas_density'), 0.001)
        assert basic_adsorbate.enthalpy_liquefaction(temp, calculate=calculated) == pytest.approx(
            adsorbate_data.get('enthalpy_liquefaction'), 0.001)

    @pytest.mark.parametrize('calculated, error',
                             [(True, pygaps.CalculationError),
                              (False, pygaps.ParameterError)])
    def test_adsorbate_miss_named_props(self, calculated, error):
        temp = 77.355
        ads = pygaps.Adsorbate(name='n', formula='C2')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(error):
                ads.molar_mass(calculated)
            with pytest.raises(error):
                ads.saturation_pressure(temp, calculate=calculated)
            with pytest.raises(error):
                ads.surface_tension(temp, calculate=calculated)
            with pytest.raises(error):
                ads.liquid_density(temp, calculate=calculated)
            with pytest.raises(error):
                ads.gas_density(temp, calculate=calculated)
            with pytest.raises(error):
                ads.enthalpy_liquefaction(temp, calculate=calculated)

    def test_adsorbate_print(self, basic_adsorbate):
        """Checks the printing is done"""

        print(basic_adsorbate)
