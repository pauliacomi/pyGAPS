"""Tests excel parsing."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_QNT


@pytest.mark.parsing
class TestQuantachrome():
    """Test parsing of Quantachrome files"""
    @pytest.mark.parametrize("path", DATA_QNT)
    def test_read_qnt_txt(self, path):
        """Test reading of Quantachrome txt files."""
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='qnt', fmt='txt-raw')
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        assert isotherm == pgp.isotherm_from_json(json_path)
