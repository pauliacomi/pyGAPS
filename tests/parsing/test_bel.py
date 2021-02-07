"""Tests bel file read."""

import pytest

import pygaps

from .conftest import DATA_BEL


@pytest.mark.parsing
class TestBEL():
    def test_read_bel(self):
        """Tests reading of a bel data file"""

        for path in DATA_BEL:

            isotherm = pygaps.isotherm_from_bel(path=path)
            json_path = str(path).replace('.DAT', '.json')
            assert isotherm == pygaps.isotherm_from_json(json_path)
