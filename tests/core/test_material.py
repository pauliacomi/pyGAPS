"""Tests relating to the Material class."""

import pytest

import pygaps
import pygaps.utilities.exceptions as pgEx


@pytest.mark.core
class TestMaterial():
    """Test the material class."""
    def test_material_basic(self):
        """Basic creation tests."""
        mat = pygaps.Material('material1')
        assert mat == 'material1'
        assert mat != 'Material1'
        mat2 = pygaps.Material('material1')
        assert mat == mat2

    def test_material_create(self, material_data, basic_material):
        """Check material can be created from test data."""
        assert material_data == basic_material.to_dict()

    def test_material_retrieved_list(self, material_data, basic_material):
        """Check material can be retrieved from master list."""

        uploaded_material = pygaps.Material.find(material_data.get('name'))
        assert basic_material == uploaded_material

        with pytest.raises(pgEx.ParameterError):
            pygaps.Material.find('noname')

        uploaded = pygaps.Material("uploaded", store=True)
        assert uploaded == pygaps.Material.find('uploaded')

        not_uploaded = pygaps.Material("not_uploaded", store=False)
        with pytest.raises(pgEx.ParameterError):
            pygaps.Material.find('not_uploaded')

    def test_material_get_properties(self, material_data, basic_material):
        """Check if properties of a material can be located."""

        assert basic_material.get_prop('density'
                                       ) == material_data.get('density')

        density = basic_material.properties.pop('density')
        assert basic_material.get_prop('density') == None
        basic_material.properties['density'] = density
        with pytest.raises(pgEx.ParameterError):
            basic_material.get_prop('something')

    def test_adsorbate_named_props(self, material_data, basic_material):
        assert basic_material.density == material_data['density']
        assert basic_material.molar_mass == material_data['molar_mass']
        basic_material.density = 100
        assert basic_material.properties['density'] == 100
        basic_material.molar_mass = 100
        assert basic_material.properties['molar_mass'] == 100

    def test_material_print(self, basic_material):
        """Checks the printing can be done."""
        print(basic_material)
