"""Tests bel file read."""

import pytest

import pygaps.parsing.json as pgpj
import pygaps.parsing.bel_dat as pgpbel

from .conftest import DATA_BEL


@pytest.mark.parsing
class TestBEL():
    def test_read_bel(self):
        """Tests reading of a bel data file"""

        for path in DATA_BEL:

            isotherm = pgpbel.isotherm_from_bel(path=path)
            json_path = str(path).replace('.DAT', '.json')
            assert isotherm == pgpj.isotherm_from_json(json_path)
