"""Tests sqlite database utilities."""

import pytest

import pygaps
from pygaps.parsing import sqlite as pgsql
from pygaps.utilities.exceptions import ParsingError
from pygaps.utilities.sqlite_db_creator import db_create
from pygaps.utilities.sqlite_db_creator import db_execute_general


@pytest.fixture(scope='session')
def db_file(tmp_path_factory):
    """Generate the database in a temporary folder."""
    pth = tmp_path_factory.mktemp('database') / 'test.db'
    db_create(pth)
    return pth


@pytest.mark.parsing
class TestDatabase():
    """All testing of Database interface"""
    def test_db_create(self, db_file):
        """Test the database creation."""
        with pytest.raises(ParsingError):
            db_execute_general("SELECT", "/")
        return db_file

    def test_adsorbate_type(self, db_file, adsorbate_data):
        """Test functions related to adsorbate type table then inserts required data."""
        test_dict = {"type": "prop", "unit": "test unit", "description": "Test"}

        # Upload test
        pgsql.adsorbate_property_type_to_db(test_dict, db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.adsorbate_property_type_to_db(test_dict, db_path=db_file)

        # Get test
        assert test_dict in pgsql.adsorbate_property_types_from_db(db_path=db_file)

        # Delete test
        pgsql.adsorbate_property_type_delete_db(test_dict["type"], db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.adsorbate_property_type_delete_db(test_dict["type"], db_path=db_file)

    def test_adsorbates(self, db_file, adsorbate_data, basic_adsorbate):
        """Test functions related to adsorbate table, then inserts a test adsorbate."""

        # Upload test
        pgsql.adsorbate_to_db(basic_adsorbate, db_path=db_file)

        # Upload blank test
        pgsql.adsorbate_to_db(pygaps.Adsorbate('blank'), db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.adsorbate_to_db(basic_adsorbate, db_path=db_file)

        # Get test
        assert basic_adsorbate in pgsql.adsorbates_from_db(db_path=db_file)

        # Overwrite upload
        basic_adsorbate.properties['formula'] = "newform"
        pgsql.adsorbate_to_db(basic_adsorbate, db_path=db_file, overwrite=True)
        got_adsorbate = next(
            ads for ads in pgsql.adsorbates_from_db(db_path=db_file)
            if ads.name == basic_adsorbate.name
        )
        assert got_adsorbate.formula == basic_adsorbate.formula

        # Delete test
        pgsql.adsorbate_delete_db(basic_adsorbate, db_path=db_file)

        # Delete string test
        pgsql.adsorbate_delete_db('blank', db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.adsorbate_delete_db(basic_adsorbate, db_path=db_file)

        # Final upload
        pgsql.adsorbate_to_db(basic_adsorbate, db_path=db_file)

    def test_material_type(self, db_file, material_data):
        """Test functions related to material type table then inserts required data."""

        test_dict = {"type": "prop", "unit": "test unit", "description": "Test"}

        # Upload test
        pgsql.material_property_type_to_db(test_dict, db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.material_property_type_to_db(test_dict, db_path=db_file)

        # Get test
        assert test_dict in pgsql.material_property_types_from_db(db_path=db_file)

        # Delete test
        pgsql.material_property_type_delete_db(test_dict['type'], db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.material_property_type_delete_db(test_dict["type"], db_path=db_file)

        # Property type upload
        for prop in material_data:
            pgsql.material_property_type_to_db({'type': prop, 'unit': "test unit"}, db_path=db_file)

    def test_material(self, db_file, material_data, basic_material):
        """Test functions related to materials table, then inserts a test material."""

        # Upload test
        pgsql.material_to_db(basic_material, db_path=db_file)

        # Upload blank test
        pgsql.material_to_db(pygaps.Material('blank'), db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.material_to_db(basic_material, db_path=db_file)

        # Get test
        assert basic_material in pgsql.materials_from_db(db_path=db_file)

        # Overwrite upload
        basic_material.properties['comment'] = 'New comment'
        pgsql.material_to_db(basic_material, overwrite=True, db_path=db_file)
        got_material = next(
            mat for mat in pgsql.materials_from_db(db_path=db_file)
            if mat.name == basic_material.name
        )
        assert got_material.properties['comment'] == basic_material.properties['comment']

        # Delete test
        pgsql.material_delete_db(basic_material, db_path=db_file)

        # Delete string test
        pgsql.material_delete_db('blank', db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.material_delete_db(basic_material, db_path=db_file)

        # Final upload
        pgsql.material_to_db(basic_material, db_path=db_file)

    def test_isotherm_type(self, db_file, basic_pointisotherm):
        """Test functions related to isotherm type table then inserts required data."""

        test_dict = {"type": "test", "description": "Test"}

        # Upload test
        pgsql.isotherm_type_to_db(test_dict, db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.isotherm_type_to_db(test_dict, db_path=db_file)

        # Get test
        assert test_dict in pgsql.isotherm_types_from_db(db_path=db_file)

        # Delete test
        pgsql.isotherm_type_delete_db(test_dict["type"], db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.isotherm_type_delete_db(test_dict["type"], db_path=db_file)

    def test_isotherm(self, db_file, isotherm_parameters, basic_isotherm):
        """Test functions related to isotherms table, then inserts a test isotherm."""

        # Upload test
        pgsql.isotherm_to_db(basic_isotherm, db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.isotherm_to_db(basic_isotherm, db_path=db_file)

        # Get test
        assert basic_isotherm in pgsql.isotherms_from_db(db_path=db_file)

        # Delete test
        pgsql.isotherm_delete_db(basic_isotherm, db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.isotherm_delete_db(basic_isotherm, db_path=db_file)

    def test_isotherm_autoinsert(self, db_file, basic_isotherm, basic_adsorbate, basic_material):
        """Test the autoupload functionality."""

        pgsql.material_delete_db(basic_material, db_path=db_file)
        pgsql.adsorbate_delete_db(basic_adsorbate, db_path=db_file)
        if basic_adsorbate in pygaps.ADSORBATE_LIST:
            pygaps.ADSORBATE_LIST.remove(basic_adsorbate)
        if basic_material in pygaps.MATERIAL_LIST:
            pygaps.MATERIAL_LIST.remove(basic_material)
        basic_isotherm.to_db(db_path=db_file, autoinsert_material=True, autoinsert_adsorbate=True)
        pgsql.isotherm_delete_db(basic_isotherm, db_path=db_file)
        pgsql.material_delete_db(basic_material, db_path=db_file)
        pgsql.adsorbate_delete_db(basic_adsorbate, db_path=db_file)
        pgsql.material_to_db(basic_material, db_path=db_file)
        pgsql.adsorbate_to_db(basic_adsorbate, db_path=db_file)

    def test_pointisotherm(self, db_file, isotherm_parameters, basic_pointisotherm):
        """Test functions related to isotherms table, then inserts a test isotherm."""

        # Upload test
        pgsql.isotherm_to_db(basic_pointisotherm, db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.isotherm_to_db(basic_pointisotherm, db_path=db_file)

        # Get test
        assert basic_pointisotherm in pgsql.isotherms_from_db(db_path=db_file)

        # Delete test
        pgsql.isotherm_delete_db(basic_pointisotherm, db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.isotherm_delete_db(basic_pointisotherm, db_path=db_file)

        # Convenience function test
        basic_pointisotherm.to_db(db_file)

    def test_modelisotherm(self, db_file, isotherm_parameters, basic_modelisotherm):
        """Test functions related to isotherms table, then inserts a test isotherm."""

        # Upload test
        pgsql.isotherm_to_db(basic_modelisotherm, db_path=db_file)

        # Unique test
        with pytest.raises(ParsingError):
            pgsql.isotherm_to_db(basic_modelisotherm, db_path=db_file)

        # Get test
        assert basic_modelisotherm in pgsql.isotherms_from_db(db_path=db_file)

        # Delete test
        pgsql.isotherm_delete_db(basic_modelisotherm, db_path=db_file)

        # Delete fail test
        with pytest.raises(ParsingError):
            pgsql.isotherm_delete_db(basic_modelisotherm, db_path=db_file)

        # Convenience function test
        basic_modelisotherm.to_db(db_file)
