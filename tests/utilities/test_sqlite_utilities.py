"""Test sqlite utilities."""
import pytest

import pygaps.utilities.sqlite_utilities as squ

tb = 'table'
s1 = ['a', 'b']
s2 = ['x', 'y']


@pytest.mark.utilities
def test_update():
    update = r'UPDATE "table" SET a = :a, b = :b WHERE x = :x AND y = :y'
    assert update == squ.build_update(tb, s1, s2)

    update = r'UPDATE "table" SET a = :a, b = :b WHERE x = :m_x AND y = :m_y'
    assert update == squ.build_update(tb, s1, s2, prefix='m_')


@pytest.mark.utilities
def test_insert():
    insert = r'INSERT INTO "table" (a, b) VALUES (:a, :b)'
    assert insert == squ.build_insert(tb, s1)


@pytest.mark.utilities
def test_select():
    select = r'SELECT a, b FROM "table"'
    assert select == squ.build_select(tb, s1, [])

    select = r'SELECT a, b FROM "table" WHERE x = :x AND y = :y'
    assert select == squ.build_select(tb, s1, s2)


@pytest.mark.utilities
def test_select_unnamed():
    select = r'SELECT a, b FROM "table" WHERE x = ? AND y = ?'
    assert select == squ.build_select_unnamed(tb, s1, s2)

    select = r'SELECT a, b FROM "table" WHERE x = ? OR y = ?'
    assert select == squ.build_select_unnamed(tb, s1, s2, join='OR')


@pytest.mark.utilities
def test_delete():
    delete = r'DELETE FROM "table" WHERE a = :a AND b = :b'
    assert delete == squ.build_delete(tb, s1)
