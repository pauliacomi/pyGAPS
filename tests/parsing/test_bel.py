"""
Tests bel file read
"""

import pytest

import pygaps

from .conftest import DATA_BEL


@pytest.mark.parsing
class TestBEL(object):

    def test_read_bel(self):
        """Tests reading of a bel data file"""

        for path in DATA_BEL:

            isotherm = pygaps.isotherm_from_bel(path=path)

            json_path = path.replace('.DAT', '.json')

            with open(json_path, 'r') as file:
                assert isotherm == pygaps.isotherm_from_json(file.read())
