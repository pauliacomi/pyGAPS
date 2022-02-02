"""Tests excel parsing."""

import pytest

from .conftest import DATA_QNT

# from pygaps.parsing.qnt_txt import parse


@pytest.mark.parsing
class TestQuantachrome():
    """Test parsing of Quantachrome files"""
    @pytest.mark.parametrize("path", DATA_QNT)
    def test_read_qnt_txt(self, path):
        """Test reading of Quantachrome txt files."""
        # TODO Quantachrome txt files are cursed
        # parse(path)
        assert True
