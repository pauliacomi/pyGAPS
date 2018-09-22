"""
Tests csv interaction
"""

import pytest

import pygaps


@pytest.mark.parsing
class TestCSV(object):

    def test_csv(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the regular csv file"""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        pygaps.isotherm_to_csv(basic_pointisotherm, path)

        isotherm = pygaps.isotherm_from_csv(path)

        assert isotherm == basic_pointisotherm
