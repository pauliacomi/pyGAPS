"""Tests various BEL file read."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_BEL
from .conftest import DATA_BEL_CSV
from .conftest import DATA_BEL_XL


@pytest.mark.parsing
class TestBEL():
    """Test parsing of BEL files"""
    @pytest.mark.parametrize("path", DATA_BEL)
    def test_read_bel_dat(self, path):
        """Test reading of a BEL data file."""
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='bel', fmt='dat')
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        isotherm2 = pgp.isotherm_from_json(json_path)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2

    @pytest.mark.parametrize("path", DATA_BEL_CSV)
    def test_read_bel_csv(self, path):
        """Test reading of BEL CSV files."""
        lang = "ENG"
        if path.stem.endswith("_jis"):
            lang = "JPN"
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='bel', fmt='csv', lang=lang)
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        isotherm2 = pgp.isotherm_from_json(json_path)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2

    @pytest.mark.parametrize("path", DATA_BEL_XL)
    def test_read_bel_excel(self, path):
        """Test reading of BEL report files."""
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='bel', fmt='xl')
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        isotherm2 = pgp.isotherm_from_json(json_path)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2
