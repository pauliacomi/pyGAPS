"""Tests excel parsing."""

import pytest

import pygaps.parsing.excel as pgpe
import pygaps.parsing.json as pgpj

from .conftest import DATA_JSON
from .conftest import DATA_XL


@pytest.mark.parsing
class TestExcel():
    """All testing of Excel interface"""
    def test_excel_isotherm(self, basic_isotherm, tmpdir_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('baseisotherm.xls').strpath
        pgpe.isotherm_to_xl(basic_isotherm, path=path)
        isotherm = pgpe.isotherm_from_xl(path)
        assert isotherm == basic_isotherm

    def test_excel_isotherm_material(self, basic_isotherm, basic_material, tmpdir_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('isotherm_mat.xls').strpath
        basic_isotherm.material = basic_material
        pgpe.isotherm_to_xl(basic_isotherm, path=path)
        isotherm = pgpe.isotherm_from_xl(path)
        assert isotherm == basic_isotherm

    def test_excel_pointisotherm(self, basic_pointisotherm, tmpdir_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('pointisotherm.xls').strpath
        pgpe.isotherm_to_xl(basic_pointisotherm, path=path)
        isotherm = pgpe.isotherm_from_xl(path)
        assert isotherm == basic_pointisotherm

    def test_excel_modelisotherm(self, basic_modelisotherm, tmpdir_factory):
        """Test creation/read of model isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('modelisotherm.xls').strpath
        pgpe.isotherm_to_xl(basic_modelisotherm, path=path)
        isotherm = pgpe.isotherm_from_xl(path)
        assert isotherm == basic_modelisotherm

    def test_read_excel(self):
        """Test read excel files file."""
        for path in DATA_XL:
            isotherm = pgpe.isotherm_from_xl(path=path)
            isotherm2 = pgpj.isotherm_from_json(next(DATA_JSON))
            assert isotherm.to_dict() == isotherm2.to_dict()
