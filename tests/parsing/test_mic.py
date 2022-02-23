"""Tests excel parsing."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_MIC_XL


@pytest.mark.parsing
class TestMicromeritics():
    """Test parsing of Micromeritics files"""
    @pytest.mark.parametrize("path", DATA_MIC_XL)
    def test_read_excel_mic(self, path):
        """Test reading of micromeritics report files."""
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='mic', fmt='xl')
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        assert isotherm == pgp.isotherm_from_json(json_path)
