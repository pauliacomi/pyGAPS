"""Tests relating to the material class."""

import pytest

import pygaps


@pytest.mark.core
class TestMaterial():
    """Test the material class."""

    def test_material_basic(self):
        """Basic creation tests."""
        mat = pygaps.Material('material', 'batch')
        assert mat == 'material batch'
        assert mat != 'Material Batch'
        mat2 = pygaps.Material('material', 'batch')
        assert mat == mat2

    def test_material_create(self, material_data, basic_material):
        """Check material can be created from test data."""
        assert material_data == basic_material.to_dict()

    def test_material_retrieved_list(self, material_data, basic_material):
        """Check material can be retrieved from master list."""
        pygaps.data.MATERIAL_LIST.append(basic_material)
        uploaded_material = pygaps.Material.find(
            material_data.get('name'),
            material_data.get('batch'))

        assert material_data == uploaded_material.to_dict()

        with pytest.raises(pygaps.ParameterError):
            pygaps.Material.find('noname', 'nobatch')

    def test_material_get_properties(self, material_data, basic_material):
        """Checks if properties of a material can be located."""

        assert basic_material.get_prop(
            'density') == material_data.get('density')

        density = basic_material.properties.pop('density')
        with pytest.raises(pygaps.ParameterError):
            basic_material.get_prop('density')
        basic_material.properties['density'] = density

    def test_material_print(self, basic_material):
        """Checks the printing can be done."""
        print(basic_material)
