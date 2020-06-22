"""Tests csv interaction."""

import pytest

import pygaps


@pytest.mark.parsing
class TestCSV():
    def test_csv_isotherm(self, basic_isotherm, tmpdir_factory):
        """Test creation of the Isotherm CSV."""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        pygaps.isotherm_to_csv(basic_isotherm, path)

        isotherm = pygaps.isotherm_from_csv(path)

        assert isotherm == basic_isotherm

    def test_csv_pointisotherm(self, basic_pointisotherm, tmpdir_factory):
        """Test creation of the PointIsotherm CSV."""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        pygaps.isotherm_to_csv(basic_pointisotherm, path)

        isotherm = pygaps.isotherm_from_csv(path)

        assert isotherm == basic_pointisotherm

    def test_csv_modelisotherm(self, basic_modelisotherm, tmpdir_factory):
        """Test creation of the ModelIsotherm CSV."""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        pygaps.isotherm_to_csv(basic_modelisotherm, path)

        isotherm = pygaps.isotherm_from_csv(path)

        assert isotherm.to_dict() == basic_modelisotherm.to_dict()

    def test_csv_isotherm_self(self, basic_isotherm, tmpdir_factory):
        """Test creation of class CSV function."""

        isotherm_json_std = pygaps.isotherm_to_csv(basic_isotherm)
        new_isotherm_cls = basic_isotherm.to_csv()
        assert isotherm_json_std == new_isotherm_cls
