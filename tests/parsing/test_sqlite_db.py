"""Tests sqlite database utilities."""

import pytest

import pygaps
from pygaps.utilities.sqlite_db_creator import db_create
from pygaps.utilities.sqlite_db_creator import db_execute_general


@pytest.fixture(scope='session')
def db_file(tmpdir_factory):
    "Generates the database in a temporary folder"

    pth = tmpdir_factory.mktemp('database').join('test.db')
    db_create(str(pth))

    return str(pth)


@pytest.mark.parsing
@pytest.mark.incremental
class TestDatabase():
    def test_db_create(self, db_file):
        "Tests the database creation"
        with pytest.raises(pygaps.ParsingError):
            db_execute_general("/", "SELECT")
        return db_file

    def test_adsorbate_type(self, db_file, adsorbate_data):
        "Tests functions related to adsorbate type table then inserts required data"

        # Upload test
        pygaps.db_upload_adsorbate_property_type(db_file, {
            'type': 'prop',
            'unit': "test unit"
        })

        # Get test
        assert len(pygaps.db_get_adsorbate_property_types(db_file)) == 1

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_adsorbate_property_type(db_file, {
                'type': 'prop',
                'unit': "test unit"
            })

        # Delete test
        pygaps.db_delete_adsorbate_property_type(db_file, 'prop')

        # Property type upload
        for prop in adsorbate_data:
            pygaps.db_upload_adsorbate_property_type(db_file, {
                'type': prop,
                'unit': "test unit"
            })

    def test_adsorbates(self, db_file, adsorbate_data, basic_adsorbate):
        "Tests functions related to adsorbate table, then inserts a test adsorbate"

        # Assert empty
        assert not pygaps.db_get_adsorbates(db_file)

        # First upload
        pygaps.db_upload_adsorbate(db_file, basic_adsorbate)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_adsorbate(db_file, basic_adsorbate)

        # Overwrite upload
        basic_adsorbate.properties['backend_name'] = "newname"
        pygaps.db_upload_adsorbate(db_file, basic_adsorbate, overwrite=True)
        got_adsorbate = pygaps.db_get_adsorbates(db_file)[0]
        assert got_adsorbate.properties['backend_name'] == basic_adsorbate.properties['backend_name']

        # Delete test
        pygaps.db_delete_adsorbate(db_file, basic_adsorbate)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_adsorbate(db_file, basic_adsorbate)

        # Final upload
        pygaps.db_upload_adsorbate(db_file, basic_adsorbate)

    def test_material_type(self, db_file, material_data):
        "Tests functions related to material type table then inserts required data"

        # Upload test
        pygaps.db_upload_material_property_type(db_file, {
            'type': 'prop',
            'unit': "test unit"
        })

        # Get test
        assert len(pygaps.db_get_material_property_types(db_file)) == 1

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_material_property_type(db_file, {
                'type': 'prop',
                'unit': "test unit"
            })

        # Delete test
        pygaps.db_delete_material_property_type(db_file, 'prop')

        # Property type upload
        for prop in material_data:
            pygaps.db_upload_material_property_type(db_file, {
                'type': prop,
                'unit': "test unit"
            })

    def test_material(self, db_file, material_data, basic_material):
        "Tests functions related to materials table, then inserts a test material"

        # Assert empty
        assert not pygaps.db_get_materials(db_file)

        # First upload
        pygaps.db_upload_material(db_file, basic_material)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_material(db_file, basic_material)

        # Overwrite upload
        basic_material.properties['comment'] = 'New comment'
        pygaps.db_upload_material(db_file, basic_material, overwrite=True)
        got_material = pygaps.db_get_materials(db_file)[0]
        assert got_material.properties['comment'] == basic_material.properties['comment']

        # Delete test
        pygaps.db_delete_material(db_file, basic_material)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_material(db_file, basic_material)

        # Final upload
        pygaps.db_upload_material(db_file, basic_material)

    def test_isotherm_type(self, db_file, basic_pointisotherm):
        "Tests functions related to isotherm type table then inserts required data"

        # Upload test
        pygaps.db_upload_isotherm_type(db_file, {'type': basic_pointisotherm.iso_type,
                                                 'description': 'test type'})

        # Get test
        assert len(pygaps.db_get_isotherm_types(db_file)) == 1

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_isotherm_type(db_file, {'type': basic_pointisotherm.iso_type,
                                                     'description': 'test type'})

        # Delete test
        pygaps.db_delete_isotherm_type(db_file, basic_pointisotherm.iso_type)

        # Upload data
        pygaps.db_upload_isotherm_type(db_file, {'type': basic_pointisotherm.iso_type,
                                                 'description': 'test type'})

    def test_isotherm_prop_type(self, db_file, isotherm_parameters):
        "Tests functions related to isotherm prop type table then inserts required data"

        # Upload test
        pygaps.db_upload_isotherm_property_type(db_file, {
            'type': 'prop',
            'unit': "test unit"
        })

        # Get test
        assert any(a['type'] == 'prop' for a in pygaps.db_get_isotherm_property_types(db_file))

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_isotherm_property_type(db_file, {
                'type': 'prop',
                'unit': "test unit"
            })

        # Delete test
        pygaps.db_delete_isotherm_property_type(db_file, 'prop')

        # Property type upload
        for prop in isotherm_parameters:
            if prop not in pygaps.classes.isotherm.Isotherm._db_columns and prop not in pygaps.classes.isotherm.Isotherm._unit_params:
                pygaps.db_upload_isotherm_property_type(db_file, {
                    'type': prop,
                    'unit': "test unit"
                })

    def test_isotherm_data_type(self, db_file, basic_pointisotherm):
        "Tests functions related to isotherm prop type table then inserts required data"

        # Upload test
        pygaps.db_upload_isotherm_data_type(db_file, {
            'type': 'test',
            'unit': "test unit"
        })

        # Get test
        assert len(pygaps.db_get_isotherm_data_types(db_file)) == 1

        # Unique test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_isotherm_data_type(db_file, {
                'type': 'test',
                'unit': "test unit"
            })

        # Delete test
        pygaps.db_delete_isotherm_data_type(db_file, 'test')

        # Upload
        pygaps.db_upload_isotherm_data_type(db_file, {
            'type': basic_pointisotherm.loading_key,
            'unit': "test unit"
        })
        pygaps.db_upload_isotherm_data_type(db_file, {
            'type': basic_pointisotherm.pressure_key,
            'unit': "test unit"
        })
        for key in basic_pointisotherm.other_keys:
            pygaps.db_upload_isotherm_data_type(db_file, {
                'type': key,
                'unit': "test unit"
            })

    def test_isotherm(self, db_file, isotherm_parameters, basic_pointisotherm):
        "Tests functions related to isotherms table, then inserts a test isotherm"

        # Start testing isotherms table
        assert not pygaps.db_get_isotherms(db_file, {})

        # First upload
        pygaps.db_upload_isotherm(db_file, basic_pointisotherm)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_isotherm(db_file, basic_pointisotherm)

        # Delete test
        pygaps.db_delete_isotherm(db_file, basic_pointisotherm)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_delete_isotherm(db_file, basic_pointisotherm)

        # Final upload
        pygaps.db_upload_isotherm(db_file, basic_pointisotherm)

        return
