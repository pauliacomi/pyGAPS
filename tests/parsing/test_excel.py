"""Tests excel parsing."""

import pytest

import pygaps

from .conftest import DATA_BEL_XL
from .conftest import DATA_JSON
from .conftest import DATA_MIC_XL
from .conftest import DATA_XL


@pytest.mark.parsing
class TestExcel():
    """All testing of Excel interface"""
    def test_read_create_excel(self, basic_pointisotherm, tmpdir_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('regular.xls').strpath

        pygaps.isotherm_to_xl(basic_pointisotherm, path=path)

        isotherm = pygaps.isotherm_from_xl(path)
        assert isotherm == basic_pointisotherm

    def test_read_create_excel_model(
        self, basic_modelisotherm, tmpdir_factory
    ):
        """Test creation/read of model isotherm excel file."""
        path = tmpdir_factory.mktemp('excel').join('regular.xls').strpath

        pygaps.isotherm_to_xl(basic_modelisotherm, path=path)

        isotherm = pygaps.isotherm_from_xl(path)
        assert isotherm == basic_modelisotherm

    def test_read_excel(self):
        """Test read excel files file."""
        for index, path in enumerate(DATA_XL):
            isotherm = pygaps.isotherm_from_xl(path=path)
            with open(DATA_JSON[index], 'r') as file:
                isotherm2 = pygaps.isotherm_from_json(file.read())
                assert isotherm.to_dict() == isotherm2.to_dict()

    def test_read_excel_mic(self):
        """Test reading of micromeritics report files."""
        for path in DATA_MIC_XL:
            isotherm = pygaps.isotherm_from_xl(path=path, fmt='mic')
            json_path = str(path).replace('.xls', '.json')
            assert isotherm == pygaps.isotherm_from_json(json_path)

    def test_read_excel_bel(self):
        """Test reading of bel report files."""
        for path in DATA_BEL_XL:
            isotherm = pygaps.isotherm_from_xl(path=path, fmt='bel')
            json_path = str(path).replace('.xls', '.json')
            assert isotherm == pygaps.isotherm_from_json(json_path)
