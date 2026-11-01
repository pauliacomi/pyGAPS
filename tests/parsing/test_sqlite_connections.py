"""Independent regression tests for SQLite connection routing."""

import shutil
import sqlite3

import pytest

import pygaps
from pygaps.parsing import sqlite as pgsql


@pytest.fixture
def database_copies(tmp_path, monkeypatch):
    default = tmp_path / 'default.db'
    external = tmp_path / 'external.db'
    for path in (default, external):
        shutil.copyfile(pygaps.DATABASE, path)
    monkeypatch.setattr(pgsql, 'DATABASE', default)
    return default, external


@pytest.mark.parsing
@pytest.mark.parametrize('positional', [True, False])
def test_database_path_routes_all_operations(database_copies, positional):
    default, external = database_copies
    material = pygaps.Material('connection-routing-test')
    args, kwargs = ((external,), {}) if positional else ((), {'db_path': external})

    pgsql.material_to_db(material, *args, **kwargs)
    assert material in pgsql.materials_from_db(*args, **kwargs)
    assert material not in pgsql.materials_from_db(db_path=default)
    pgsql.material_delete_db(material, *args, **kwargs)
    assert material not in pgsql.materials_from_db(*args, **kwargs)


@pytest.mark.parsing
def test_supplied_cursor_does_not_open_another_connection(database_copies, monkeypatch):
    _, external = database_copies
    with sqlite3.connect(external) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        def unexpected_connection(*args, **kwargs):
            pytest.fail('A supplied cursor must be reused.')

        monkeypatch.setattr(pgsql.sqlite3, 'connect', unexpected_connection)
        material = pygaps.Material('cursor-routing-test')
        pgsql.material_to_db(material, external, cursor=cursor)
        assert material in pgsql.materials_from_db(external, cursor=cursor)
