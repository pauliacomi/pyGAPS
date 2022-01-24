"""Tests excel parsing."""

import pytest

import pygaps.parsing as pgp
from .conftest import DATA_3P_XL


@pytest.mark.parsing
class Test3P():
    """Test parsing of 3p files"""
    @pytest.mark.parametrize("path", DATA_3P_XL)
    def test_read_excel_3p(self, path):
        """Test reading of 3P report files."""
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='3p', fmt='xl')
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        assert isotherm == pgp.isotherm_from_json(json_path)
