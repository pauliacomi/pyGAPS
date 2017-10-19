"""
This test module has tests relating to sqlite database utilities
"""

import copy

import pytest

import pygaps
import pygaps.parsing as ps
from pygaps.utilities.sqlite_db_creator import db_create
from pygaps.utilities.sqlite_db_creator import db_execute_general


@pytest.fixture(scope='session')
def db_file(tmpdir_factory):
    "Generates the database in a temporary folder"

    pth = tmpdir_factory.mktemp('database').join('test.db')
    db_create(str(pth))

    return str(pth)


@pytest.mark.incremental
class TestDatabase(object):
    def test_db_create(self, db_file):
        "Tests the database creation"
        with pytest.raises(pygaps.ParsingError):
            db_execute_general("/", "SELECT")
        return db_file

    def test_machine(self, db_file):
        "Tests functions related to machine table, then inserts a test machine"
        machine_dict = {
            'nick': 'TM',
            'name': 'Test Machine',
            'type': 'TestType',
        }

        # First upload
        ps.db_upload_machine(db_file, machine_dict)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_machine(db_file, machine_dict)

        # Overwrite upload
        ps.db_upload_machine(db_file, machine_dict, overwrite=True)

        # Delete test
        ps.db_delete_machine(db_file, machine_dict["nick"])

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            ps.db_delete_machine(db_file, machine_dict["nick"])

        # Final upload
        ps.db_upload_machine(db_file, machine_dict)

        return

    def test_sources(self, db_file):
        "Tests functions related to sources table, then inserts a test source"
        source_dict = {
            'nick': 'TL',
            'name': 'Test Lab'
        }

        # First upload
        ps.db_upload_source(db_file, source_dict)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_source(db_file, source_dict)

        # Overwrite upload
        ps.db_upload_source(db_file, source_dict, overwrite=True)

        # Delete test
        ps.db_delete_source(db_file, source_dict["nick"])

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            ps.db_delete_source(db_file, source_dict["nick"])

        # Final upload
        ps.db_upload_source(db_file, source_dict)

        return

    def test_contacts(self, db_file):
        "Tests functions related to contacts table, then inserts a test contact"
        contact_dict = {
            'nick': 'TU',
            'name': 'Test User',
            'email': 'test@email.com',
            'phone': '0800',
        }

        # First upload
        ps.db_upload_contact(db_file, contact_dict)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_contact(db_file, contact_dict)

        # Overwrite upload
        ps.db_upload_contact(db_file, contact_dict, overwrite=True)

        # Delete test
        ps.db_delete_contact(db_file, contact_dict["nick"])

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            ps.db_delete_contact(db_file, contact_dict["nick"])

        # Final upload
        ps.db_upload_contact(db_file, contact_dict)

        return

    def test_gasses(self, db_file, adsorbate_data):
        "Tests functions related to gasses table, then inserts a test gas"

        # Property type testing
        test_duplicate = True
        for prop in adsorbate_data["properties"]:
            ps.db_upload_adsorbate_property_type(db_file, prop, "test unit")
            if test_duplicate:
                test_duplicate = False
                with pytest.raises(pygaps.ParsingError):
                    ps.db_upload_adsorbate_property_type(
                        db_file, prop, "test unit")

        # Start testing samples table
        basic_adsorbate = pygaps.Adsorbate(adsorbate_data)

        # Assert empty
        assert len(pygaps.db_get_adsorbates(db_file)) == 0

        # First upload
        ps.db_upload_adsorbate(db_file, basic_adsorbate)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_adsorbate(db_file, basic_adsorbate)

        # Overwrite upload
        basic_adsorbate.formula = "New Formula"
        ps.db_upload_adsorbate(db_file, basic_adsorbate, overwrite=True)
        assert pygaps.db_get_adsorbates(
            db_file)[0].formula == basic_adsorbate.formula

        # Delete test
        ps.db_delete_adsorbate(db_file, basic_adsorbate)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            ps.db_delete_adsorbate(db_file, basic_adsorbate)

        # Final upload
        ps.db_upload_adsorbate(db_file, basic_adsorbate)

        return

    def test_sample(self, db_file, sample_data):
        "Tests functions related to samples table, then inserts a test sample"

        # Test sample_type table
        ps.db_upload_sample_type(db_file, {'nick': sample_data['type'],
                                           'name': 'test name'})
        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_sample_type(db_file, {'nick': sample_data['type'],
                                               'name': 'test name'})

        # Property type testing
        test_error = True
        for prop in sample_data["properties"]:
            ps.db_upload_sample_property_type(db_file, prop, "test unit")
            if test_error:
                with pytest.raises(pygaps.ParsingError):
                    test_error = False
                    ps.db_upload_sample_property_type(
                        db_file, prop, "test unit")

        # Start testing samples table
        basic_sample = pygaps.Sample(sample_data)

        # Assert empty
        assert len(pygaps.db_get_samples(db_file)) == 0

        # First upload
        pygaps.db_upload_sample(db_file, basic_sample)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_sample(db_file, basic_sample)

        # Overwrite upload
        basic_sample.comment = 'New comment'
        pygaps.db_upload_sample(db_file, basic_sample, overwrite=True)
        assert pygaps.db_get_samples(
            db_file)[0].comment == basic_sample.comment

        # Delete test
        ps.db_delete_sample(db_file, basic_sample)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            ps.db_delete_sample(db_file, basic_sample)

        # Final upload
        pygaps.db_upload_sample(db_file, basic_sample)

        return

    def test_experiment(self, db_file, basic_pointisotherm):
        "Tests functions related to experiments table, then inserts a test experiment"

        isotherm = basic_pointisotherm

        # Test experiment_type table
        ps.db_upload_experiment_type(db_file, {'nick': isotherm.exp_type,
                                               'name': 'test type'})
        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_experiment_type(db_file, {'nick': isotherm.exp_type,
                                                   'name': 'test type'})

        # Test experiment_data_type table
        ps.db_upload_experiment_data_type(
            db_file, isotherm.loading_key, "test unit")
        ps.db_upload_experiment_data_type(
            db_file, isotherm.pressure_key, "test unit")
        for key in isotherm.other_keys:
            ps.db_upload_experiment_data_type(
                db_file, key, "test unit")

        with pytest.raises(pygaps.ParsingError):
            ps.db_upload_experiment_data_type(
                db_file, isotherm.loading_key, "test unit")

        # Start testing experiments table
        assert len(pygaps.db_get_experiments(db_file, {})) == 0

        # First upload
        pygaps.db_upload_experiment(db_file, isotherm)

        # Error test uniqueness
        with pytest.raises(pygaps.ParsingError):
            pygaps.db_upload_experiment(db_file, isotherm)

        replace_isotherm = copy.deepcopy(isotherm)
        replace_isotherm.comment = 'New comment'
        pygaps.db_upload_experiment(
            db_file, replace_isotherm, overwrite=isotherm)
        assert pygaps.db_get_experiments(
            db_file, {'id': replace_isotherm.id})[0].comment == replace_isotherm.comment

        # Delete test
        ps.db_delete_experiment(db_file, replace_isotherm)

        # Delete fail test
        with pytest.raises(pygaps.ParsingError):
            ps.db_delete_experiment(db_file, isotherm)

        # Final upload
        pygaps.db_upload_experiment(db_file, isotherm)

        return
