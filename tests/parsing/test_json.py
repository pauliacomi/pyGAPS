"""Tests JSON parsing."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_JSON
from .conftest import DATA_JSON_NIST


@pytest.mark.parsing
class TestJson():
    """All testing of JSON interface"""
    def test_json_isotherm(self, basic_isotherm):
        """Test the parsing of an isotherm to json."""
        test_isotherm_json = pgp.isotherm_to_json(basic_isotherm)
        new_isotherm = pgp.isotherm_from_json(test_isotherm_json)
        assert basic_isotherm == new_isotherm

    def test_json_iso_material(self, basic_isotherm, basic_material):
        """Test the parsing of an isotherm that has a special material to json."""
        basic_isotherm.material = basic_material
        test_isotherm_json = pgp.isotherm_to_json(basic_isotherm)
        new_isotherm = pgp.isotherm_from_json(test_isotherm_json)
        assert basic_isotherm == new_isotherm

    def test_json_pointisotherm(self, basic_pointisotherm):
        """Test the parsing of a PointIsotherm to json."""
        test_isotherm_json = pgp.isotherm_to_json(basic_pointisotherm)
        new_isotherm = pgp.isotherm_from_json(test_isotherm_json)
        assert basic_pointisotherm == new_isotherm

    def test_json_modelisotherm(self, basic_modelisotherm):
        """Test the parsing of an ModelIsotherm to json."""
        test_isotherm_json = pgp.isotherm_to_json(basic_modelisotherm)
        new_isotherm = pgp.isotherm_from_json(test_isotherm_json)
        assert basic_modelisotherm.to_dict() == new_isotherm.to_dict()

    def test_json_isotherm_file(self, basic_pointisotherm, tmp_path_factory):
        """Test the parsing of an isotherm to a json file."""
        path = tmp_path_factory.mktemp('json') / 'pointisotherm.json'
        pgp.isotherm_to_json(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_json(path)
        assert isotherm == basic_pointisotherm

    def test_json_isotherm_self(self, basic_isotherm):
        """Test the parsing of an isotherm 'to_json' class function."""
        isotherm_json_std = pgp.isotherm_to_json(basic_isotherm)
        new_isotherm_cls = basic_isotherm.to_json()
        assert isotherm_json_std == new_isotherm_cls

    @pytest.mark.parametrize("path", DATA_JSON)
    def test_json_read(self, path):
        """Test read json files."""
        isotherm = pgp.isotherm_from_json(path)
        assert isotherm

    @pytest.mark.parametrize("path", DATA_JSON_NIST)
    def test_json_nistisotherm(self, path):
        """Test the parsing of an isotherm from a NIST json."""
        pgp.isotherm_from_json(path, fmt='NIST')
