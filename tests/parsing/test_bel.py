"""
Tests bel file read
"""

import pygaps

from ..conftest import parsing

from .conftest import DATA_EXCEL_BEL


@parsing
class TestCSV(object):

    def test_bel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the regular csv file"""

        for path in DATA_EXCEL_BEL:
            dat_path = path.replace('.xls', '.dat')

            isotherm = pygaps.isotherm_from_bel(path=dat_path)

            json_path = path.replace('.dat', '.json')

            with open(json_path, 'r') as file:
                assert isotherm == pygaps.isotherm_from_json(file.read())
