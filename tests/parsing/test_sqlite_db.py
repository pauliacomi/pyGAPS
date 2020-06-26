"""""Tests sqlite database utilities."""

import pytest

import pygaps
from pygaps.utilities.sqlite_db_creator import db_create
from pygaps.utilities.sqlite_db_creator import db_execute_general


@pytest.fixture(scope='session')
def db_file(tmpdir_factory):
    """Generate the database in a temporary folder."""

    pth = tmpdir_factory.mktemp('database').join('test.db')
    db_create(str(pth))

    return str(pth)


@pytest.mark.parsing
class TestDatabase():
    def test_db_create(self, db_file):
        """Test the database creation."""
        with pytest.raises(pygaps.ParsingError):
            db_execute_general("/", "SELECT")
        return db_file

    def test_adsorbate_type(self, db_file, adsorbate_data):
        """Test functions related to adsorbate type table then inserts required data."""
        test_dict = {
            "type": "prop",
            "unit": "test unit",
            "description": "Test"
        }

        # Upload test
        pygaps.db_upload_adsorbate_property_type(db_file, test_dict)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_adsorbate_property_type(db_file, test_dict)

        # Get test
        assert test_dict in pygaps.db_get_adsorbate_property_types(db_file)

        # Delete test
        pygaps.db_delete_adsorbate_property_type(db_file, test_dict["type"])

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_adsorbate_property_type(
                db_file, test_dict["type"]
            )

    def test_adsorbates(self, db_file, adsorbate_data, basic_adsorbate):
        """Test functions related to adsorbate table, then inserts a test adsorbate."""

        # Upload test
        pygaps.db_upload_adsorbate(db_file, basic_adsorbate)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_adsorbate(db_file, basic_adsorbate)

        # Get test
        assert basic_adsorbate in pygaps.db_get_adsorbates(db_file)

        # Overwrite upload
        basic_adsorbate.properties['backend_name'] = "newname"
        pygaps.db_upload_adsorbate(db_file, basic_adsorbate, overwrite=True)
        got_adsorbate = next(
            ads for ads in pygaps.db_get_adsorbates(db_file)
            if ads.name == basic_adsorbate.name
        )
        assert got_adsorbate.backend_name() == basic_adsorbate.backend_name()

        # Delete test
        pygaps.db_delete_adsorbate(db_file, basic_adsorbate)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_adsorbate(db_file, basic_adsorbate)

        # Final upload
        pygaps.db_upload_adsorbate(db_file, basic_adsorbate)

    def test_material_type(self, db_file, material_data):
        """Test functions related to material type table then inserts required data."""

        test_dict = {
            "type": "prop",
            "unit": "test unit",
            "description": "Test"
        }

        # Upload test
        pygaps.db_upload_material_property_type(db_file, test_dict)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_material_property_type(db_file, test_dict)

        # Get test
        assert test_dict in pygaps.db_get_material_property_types(db_file)

        # Delete test
        pygaps.db_delete_material_property_type(db_file, test_dict['type'])

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_material_property_type(db_file, test_dict["type"])

        # Property type upload
        for prop in material_data:
            pygaps.db_upload_material_property_type(
                db_file, {
                    'type': prop,
                    'unit': "test unit"
                }
            )

    def test_material(self, db_file, material_data, basic_material):
        """Test functions related to materials table, then inserts a test material."""

        # Upload test
        pygaps.db_upload_material(db_file, basic_material)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_material(db_file, basic_material)

        # Get test
        assert basic_material in pygaps.db_get_materials(db_file)

        # Overwrite upload
        basic_material.properties['comment'] = 'New comment'
        pygaps.db_upload_material(db_file, basic_material, overwrite=True)
        got_material = next(
            mat for mat in pygaps.db_get_materials(db_file)
            if mat.name == basic_material.name
        )
        assert got_material.properties['comment'] == basic_material.properties[
            'comment']

        # Delete test
        pygaps.db_delete_material(db_file, basic_material)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_material(db_file, basic_material)

        # Final upload
        pygaps.db_upload_material(db_file, basic_material)

    def test_isotherm_type(self, db_file, basic_pointisotherm):
        """Test functions related to isotherm type table then inserts required data."""

        test_dict = {"type": "test", "description": "Test"}

        # Upload test
        pygaps.db_upload_isotherm_type(db_file, test_dict)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_isotherm_type(db_file, test_dict)

        # Get test
        assert test_dict in pygaps.db_get_isotherm_types(db_file)

        # Delete test
        pygaps.db_delete_isotherm_type(db_file, test_dict["type"])

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_isotherm_type(db_file, test_dict["type"])

    def test_isotherm(self, db_file, isotherm_parameters, basic_pointisotherm):
        """Test functions related to isotherms table, then inserts a test isotherm."""

        # Upload test
        pygaps.db_upload_isotherm(db_file, basic_pointisotherm)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_isotherm(db_file, basic_pointisotherm)

        # Get test
        assert basic_pointisotherm in pygaps.db_get_isotherms(db_file)

        # Delete test
        pygaps.db_delete_isotherm(db_file, basic_pointisotherm)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_isotherm(db_file, basic_pointisotherm)
