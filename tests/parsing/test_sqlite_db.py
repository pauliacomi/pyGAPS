"""""Tests sqlite database utilities."""

import pytest

import pygaps
from pygaps.parsing import sqlite as pgsqlite
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
            db_execute_general("SELECT", "/")
        return db_file

    def test_adsorbate_type(self, db_file, adsorbate_data):
        """Test functions related to adsorbate type table then inserts required data."""
        test_dict = {
            "type": "prop",
            "unit": "test unit",
            "description": "Test"
        }

        # Upload test
        pgsqlite.adsorbate_property_type_to_db(test_dict, db_path=db_file)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.adsorbate_property_type_to_db(test_dict, db_path=db_file)

        # Get test
        assert test_dict in pgsqlite.adsorbate_property_types_from_db(
            db_path=db_file
        )

        # Delete test
        pgsqlite.adsorbate_property_type_delete_db(
            test_dict["type"], db_path=db_file
        )

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.adsorbate_property_type_delete_db(
                test_dict["type"], db_path=db_file
            )

    def test_adsorbates(self, db_file, adsorbate_data, basic_adsorbate):
        """Test functions related to adsorbate table, then inserts a test adsorbate."""

        # Upload test
        pgsqlite.adsorbate_to_db(basic_adsorbate, db_path=db_file)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.adsorbate_to_db(basic_adsorbate, db_path=db_file)

        # Get test
        assert basic_adsorbate in pgsqlite.adsorbates_from_db(db_path=db_file)

        # Overwrite upload
        basic_adsorbate.properties['backend_name'] = "newname"
        pgsqlite.adsorbate_to_db(
            basic_adsorbate, db_path=db_file, overwrite=True
        )
        got_adsorbate = next(
            ads for ads in pgsqlite.adsorbates_from_db(db_path=db_file)
            if ads.name == basic_adsorbate.name
        )
        assert got_adsorbate.backend_name() == basic_adsorbate.backend_name()

        # Delete test
        pgsqlite.adsorbate_delete_db(basic_adsorbate, db_path=db_file)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.adsorbate_delete_db(basic_adsorbate, db_path=db_file)

        # Final upload
        pgsqlite.adsorbate_to_db(basic_adsorbate, db_path=db_file)

    def test_material_type(self, db_file, material_data):
        """Test functions related to material type table then inserts required data."""

        test_dict = {
            "type": "prop",
            "unit": "test unit",
            "description": "Test"
        }

        # Upload test
        pgsqlite.material_property_type_to_db(test_dict, db_path=db_file)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.material_property_type_to_db(test_dict, db_path=db_file)

        # Get test
        assert test_dict in pgsqlite.material_property_types_from_db(
            db_path=db_file
        )

        # Delete test
        pgsqlite.material_property_type_delete_db(
            test_dict['type'], db_path=db_file
        )

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.material_property_type_delete_db(
                test_dict["type"], db_path=db_file
            )

        # Property type upload
        for prop in material_data:
            pgsqlite.material_property_type_to_db({
                'type': prop,
                'unit': "test unit"
            },
                                                  db_path=db_file)

    def test_material(self, db_file, material_data, basic_material):
        """Test functions related to materials table, then inserts a test material."""

        # Upload test
        pgsqlite.material_to_db(basic_material, db_path=db_file)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.material_to_db(basic_material, db_path=db_file)

        # Get test
        assert basic_material in pgsqlite.materials_from_db(db_path=db_file)

        # Overwrite upload
        basic_material.properties['comment'] = 'New comment'
        pgsqlite.material_to_db(
            basic_material, overwrite=True, db_path=db_file
        )
        got_material = next(
            mat for mat in pgsqlite.materials_from_db(db_path=db_file)
            if mat.name == basic_material.name
        )
        assert got_material.properties['comment'] == basic_material.properties[
            'comment']

        # Delete test
        pgsqlite.material_delete_db(basic_material, db_path=db_file)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.material_delete_db(basic_material, db_path=db_file)

        # Final upload
        pgsqlite.material_to_db(basic_material, db_path=db_file)

    def test_isotherm_type(self, db_file, basic_pointisotherm):
        """Test functions related to isotherm type table then inserts required data."""

        test_dict = {"type": "test", "description": "Test"}

        # Upload test
        pgsqlite.isotherm_type_to_db(test_dict, db_path=db_file)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.isotherm_type_to_db(test_dict, db_path=db_file)

        # Get test
        assert test_dict in pgsqlite.isotherm_types_from_db(db_path=db_file)

        # Delete test
        pgsqlite.isotherm_type_delete_db(test_dict["type"], db_path=db_file)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pgsqlite.isotherm_type_delete_db(
                test_dict["type"], db_path=db_file
            )

    def test_isotherm(self, db_file, isotherm_parameters, basic_pointisotherm):
        """Test functions related to isotherms table, then inserts a test isotherm."""

        # Upload test
        pygaps.isotherm_to_db(basic_pointisotherm, db_path=db_file)

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.isotherm_to_db(basic_pointisotherm, db_path=db_file)

        # Get test
        assert basic_pointisotherm in pygaps.isotherms_from_db(db_path=db_file)

        # Delete test
        pygaps.isotherm_delete_db(basic_pointisotherm, db_path=db_file)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.isotherm_delete_db(basic_pointisotherm, db_path=db_file)
