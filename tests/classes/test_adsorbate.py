"""
This test module has tests relating to the adsorbate class
"""

import pytest

import pygaps


class TestAdsorbate(object):
    """
    Tests the adsorbate class
    """

    def test_adsorbate_created(self, adsorbate_data, basic_adsorbate):
        "Checks adsorbate can be created from test data"

        assert adsorbate_data == basic_adsorbate.to_dict()

        with pytest.raises(Exception):
            pygaps.Adsorbate({})

    def test_adsorbate_retreived_list(self, adsorbate_data, basic_adsorbate):
        "Checks adsorbate can be retrieved from master list"
        pygaps.data.GAS_LIST.append(basic_adsorbate)
        uploaded_adsorbate = pygaps.Adsorbate.from_list(
            adsorbate_data.get('nick'))

        assert adsorbate_data == uploaded_adsorbate.to_dict()

        with pytest.raises(Exception):
            pygaps.Adsorbate.from_list('noname')

    def test_adsorbate_get_properties(self, adsorbate_data, basic_adsorbate):
        "Checks if properties of a adsorbate can be located"

        assert basic_adsorbate.get_prop(
            'common_name') == adsorbate_data['properties'].get('common_name')
        assert basic_adsorbate.common_name(
        ) == adsorbate_data['properties'].get('common_name')

        name = basic_adsorbate.properties.pop('common_name')
        with pytest.raises(Exception):
            basic_adsorbate.common_name()
        basic_adsorbate.properties['common_name'] = name

    @pytest.mark.parametrize('calculated', [True, False])
    def test_adsorbate_named_props(self, adsorbate_data, basic_adsorbate, calculated):
        temp = 77.355
        assert basic_adsorbate.molar_mass(calculated) == pytest.approx(
            adsorbate_data['properties'].get('molar_mass'), 0.001)
        assert basic_adsorbate.saturation_pressure(temp, calculate=calculated) == pytest.approx(
            adsorbate_data['properties'].get('saturation_pressure'), 0.001)
        assert basic_adsorbate.surface_tension(temp, calculate=calculated) == pytest.approx(
            adsorbate_data['properties'].get('surface_tension'), 0.001)
        assert basic_adsorbate.liquid_density(temp, calculate=calculated) == pytest.approx(
            adsorbate_data['properties'].get('liquid_density'), 0.001)

    def test_adsorbate_print(self, basic_adsorbate):
        """Checks the printing is done"""

        print(basic_adsorbate)
