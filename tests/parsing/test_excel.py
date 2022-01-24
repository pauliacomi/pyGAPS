"""Tests excel parsing."""

import pytest

import pygaps.parsing.excel as pgpe
import pygaps.parsing.json as pgpj

from .conftest import DATA_JSON
from .conftest import DATA_XL


@pytest.mark.parsing
class TestExcel():
    """All testing of Excel interface"""
    def test_read_create_excel(self, basic_pointisotherm, tmpdir_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('regular.xls').strpath
        pgpe.isotherm_to_xl(basic_pointisotherm, path=path)
        isotherm = pgpe.isotherm_from_xl(path)
        assert isotherm == basic_pointisotherm

    def test_read_create_excel_model(self, basic_modelisotherm, tmpdir_factory):
        """Test creation/read of model isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('regular.xls').strpath
        pgpe.isotherm_to_xl(basic_modelisotherm, path=path)
        isotherm = pgpe.isotherm_from_xl(path)
        assert isotherm == basic_modelisotherm

    def test_read_excel(self):
        """Test read excel files file."""
        for path in DATA_XL:
            isotherm = pgpe.isotherm_from_xl(path=path)
            isotherm2 = pgpj.isotherm_from_json(next(DATA_JSON))
            assert isotherm.to_dict() == isotherm2.to_dict()
