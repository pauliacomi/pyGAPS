"""
This test module has tests relating to sqlite database utilities
"""

import copy
import sqlite3

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


@pytest.mark.incremental
class TestDatabase(object):
    def test_db_create(self, db_file):
        "Tests the database creation"
        with pytest.raises(sqlite3.OperationalError):
            db_execute_general("/", "SELECT")
        return db_file

    def test_machine(self, db_file):
        "Tests functions related to machine table, then inserts a test machine"
        machine_dict = {
            'nick': 'TM',
            'name': 'Test Machine',
            'type': 'TestType',
        }
        pygaps.db_upload_machine_type(db_file, machine_dict["type"])
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_machine_type(db_file, machine_dict["type"])

        pygaps.db_upload_machine(db_file, machine_dict)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_machine(db_file, machine_dict)

        pygaps.db_upload_machine(db_file, machine_dict, overwrite=True)

        pygaps.db_delete_machine(db_file, machine_dict["nick"])
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_delete_machine(db_file, machine_dict["nick"])

        pygaps.db_upload_machine(db_file, machine_dict)

        return

    def test_labs(self, db_file):
        "Tests functions related to labs table, then inserts a test lab"
        lab_dict = {
            'nick': 'TL',
            'name': 'Test Lab',
            'email': 'test@email.com',
            'address': 'Test Address',
        }
        pygaps.db_upload_lab(db_file, lab_dict)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_lab(db_file, lab_dict)

        pygaps.db_upload_lab(db_file, lab_dict, overwrite=True)

        pygaps.db_delete_lab(db_file, lab_dict["nick"])
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_delete_lab(db_file, lab_dict["nick"])
        pygaps.db_upload_lab(db_file, lab_dict)

        return

    def test_contacts(self, db_file):
        "Tests functions related to contacts table, then inserts a test contact"
        contact_dict = {
            'nick': 'TU',
            'name': 'Test User',
            'email': 'test@email.com',
            'phone': '0800',
            'labID': 'TL',
            'type': 'Test Address',
            'permanent': True,
        }
        pygaps.db_upload_contact(db_file, contact_dict)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_contact(db_file, contact_dict)

        pygaps.db_upload_contact(db_file, contact_dict, overwrite=True)

        pygaps.db_delete_contact(db_file, contact_dict["nick"])
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_delete_contact(db_file, contact_dict["nick"])

        pygaps.db_upload_contact(db_file, contact_dict)

        return

    def test_gasses(self, db_file, adsorbate_data):
        "Tests functions related to gasses table, then inserts a test gas"

        test_duplicate = True
        for prop in adsorbate_data["properties"]:
            pygaps.db_upload_gas_property_type(db_file, prop, "test unit")
            if test_duplicate:
                test_duplicate = False
                with pytest.raises(sqlite3.IntegrityError):
                    pygaps.db_upload_gas_property_type(
                        db_file, prop, "test unit")

        # Start testing samples table
        basic_adsorbate = pygaps.Adsorbate(adsorbate_data)
        assert len(pygaps.db_get_gasses(db_file)) == 0

        pygaps.db_upload_gas(db_file, basic_adsorbate)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_gas(db_file, basic_adsorbate)

        basic_adsorbate.formula = "New Formula"
        pygaps.db_upload_gas(db_file, basic_adsorbate, overwrite=True)
        assert pygaps.db_get_gasses(
            db_file)[0].formula == basic_adsorbate.formula

        pygaps.db_delete_gas(db_file, basic_adsorbate)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_delete_gas(db_file, basic_adsorbate)
        pygaps.db_upload_gas(db_file, basic_adsorbate)

        return

    def test_sample(self, db_file, sample_data):
        "Tests functions related to samples table, then inserts a test sample"

        # Test sample_form table
        pygaps.db_upload_sample_form(db_file, {'nick': sample_data['form'],
                                               'name': 'test name'})
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_sample_form(db_file, {'nick': sample_data['form'],
                                                   'name': 'test name'})

        # Test sample_type table
        pygaps.db_upload_sample_type(db_file, {'nick': sample_data['type'],
                                               'name': 'test name'})
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_sample_type(db_file, {'nick': sample_data['type'],
                                                   'name': 'test name'})

        # Test sample_property_type table
        test_error = True
        for prop in sample_data["properties"]:
            pygaps.db_upload_sample_property_type(db_file, prop, "test unit")
            if test_error:
                with pytest.raises(sqlite3.IntegrityError):
                    test_error = False
                    pygaps.db_upload_sample_property_type(
                        db_file, prop, "test unit")

        # Start testing samples table
        basic_sample = pygaps.Sample(sample_data)
        assert len(pygaps.db_get_samples(db_file)) == 0

        pygaps.db_upload_sample(db_file, basic_sample)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_sample(db_file, basic_sample)

        basic_sample.comment = 'New comment'
        pygaps.db_upload_sample(db_file, basic_sample, overwrite=True)
        assert pygaps.db_get_samples(
            db_file)[0].comment == basic_sample.comment

        pygaps.db_delete_sample(db_file, basic_sample)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_delete_sample(db_file, basic_sample)
        pygaps.db_upload_sample(db_file, basic_sample)

        return

    def test_experiment(self, db_file, basic_pointisotherm):
        "Tests functions related to experiments table, then inserts a test experiment"

        isotherm = basic_pointisotherm

        # Test experiment_type table
        pygaps.db_upload_experiment_type(db_file, {'nick': isotherm.exp_type,
                                                   'name': 'test type'})
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_experiment_type(db_file, {'nick': isotherm.exp_type,
                                                       'name': 'test type'})

        # Test experiment_data_type table
        pygaps.db_upload_experiment_data_type(
            db_file, isotherm.loading_key, "test unit")
        pygaps.db_upload_experiment_data_type(
            db_file, isotherm.pressure_key, "test unit")
        for key in isotherm.other_keys:
            pygaps.db_upload_experiment_data_type(
                db_file, key, "test unit")

        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_experiment_data_type(
                db_file, isotherm.loading_key, "test unit")

        # Start testing experiments table
        assert len(pygaps.db_get_experiments(db_file, {})) == 0

        pygaps.db_upload_experiment(db_file, isotherm)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_upload_experiment(db_file, isotherm)
        replace_isotherm = copy.deepcopy(isotherm)
        replace_isotherm.comment = 'New comment'
        pygaps.db_upload_experiment(
            db_file, replace_isotherm, overwrite=isotherm)
        assert pygaps.db_get_experiments(
            db_file, {'id': replace_isotherm.id})[0].comment == replace_isotherm.comment

        pygaps.db_delete_experiment(db_file, replace_isotherm)
        with pytest.raises(sqlite3.IntegrityError):
            pygaps.db_delete_experiment(db_file, isotherm)

        pygaps.db_upload_experiment(db_file, isotherm)

        return
