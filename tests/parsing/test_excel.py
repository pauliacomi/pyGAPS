"""Tests excel parsing."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_JSON
from .conftest import DATA_XL


@pytest.mark.parsing
class TestExcel():
    """All testing of Excel interface"""
    def test_excel_isotherm(self, basic_isotherm, tmp_path_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'baseisotherm.xls'
        pgp.isotherm_to_xl(basic_isotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert isotherm == basic_isotherm

    def test_excel_isotherm_material(self, basic_isotherm, basic_material, tmp_path_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'isotherm_mat.xls'
        basic_isotherm.material = basic_material
        pgp.isotherm_to_xl(basic_isotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert isotherm == basic_isotherm

    def test_excel_pointisotherm(self, basic_pointisotherm, tmp_path_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'pointisotherm.xls'
        pgp.isotherm_to_xl(basic_pointisotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert isotherm == basic_pointisotherm

    def test_excel_modelisotherm(self, basic_modelisotherm, tmp_path_factory):
        """Test creation/read of model isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'modelisotherm.xls'
        pgp.isotherm_to_xl(basic_modelisotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert isotherm == basic_modelisotherm

    @pytest.mark.parametrize("path", DATA_XL)
    def test_excel_read(self, path):
        """Test read excel files."""
        isotherm = pgp.isotherm_from_xl(path=path)
        assert isotherm

    @pytest.mark.parametrize("path_json", DATA_JSON)
    def test_excel_write_read(self, path_json, tmp_path_factory):
        """Test various parsings in excel files."""
        isotherm = pgp.isotherm_from_json(path_json)
        path = tmp_path_factory.mktemp('excel') / path_json.with_suffix(".xls").name
        pgp.isotherm_to_xl(isotherm, path)
        isotherm2 = pgp.isotherm_from_xl(path)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2
