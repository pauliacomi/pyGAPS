"""Tests SMS DVS excel file parsing."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_SMSDVS_XL


@pytest.mark.parsing
class TestSMS_DVS():
    """Test parsing of SMS DVS files"""
    @pytest.mark.parametrize("path", DATA_SMSDVS_XL)
    def test_read_excel_smsdvs(self, path):
        """Test reading of SMS DVS excel processed files."""
        isotherm = pgp.isotherm_from_commercial(path=path, manufacturer='smsdvs', fmt='xlsx')
        json_path = path.with_suffix('.json')
        # pgp.isotherm_to_json(isotherm, json_path, indent=4)
        isotherm2 = pgp.isotherm_from_json(json_path)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2
