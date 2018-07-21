"""
Tests excel interaction
"""

import pygaps

from ..conftest import parsing
from .conftest import DATA_EXCEL_BEL
from .conftest import DATA_EXCEL_MIC
from .conftest import DATA_EXCEL_STD


@parsing
class TestExcel(object):

    def test_read_create_excel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the regular excel file"""

        path = tmpdir_factory.mktemp('excel').join('regular.xls').strpath

        pygaps.isotherm_to_xl(basic_pointisotherm, path=path)

        isotherm = pygaps.isotherm_from_xl(path)
        assert isotherm == basic_pointisotherm

    def test_read_create_excel_madirel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the MADIREL file"""

        path = DATA_EXCEL_STD[0]
        path = tmpdir_factory.mktemp('excel').join('MADIREL.xlsx').strpath
        pygaps.isotherm_to_xl(basic_pointisotherm,
                              path=path, fmt='MADIREL')

        isotherm = pygaps.isotherm_from_xl(path, fmt='MADIREL')
        assert isotherm == basic_pointisotherm

    def test_read_excel_mic(self):
        """Tests reading of micromeritics report files"""

        for path in DATA_EXCEL_MIC:
            isotherm = pygaps.isotherm_from_xl(path=path, fmt='mic')

            json_path = path.replace('.xls', '.json')

            with open(json_path, 'r') as file:
                assert isotherm == pygaps.isotherm_from_json(file.read())

    def test_read_excel_bel(self):
        """Tests reading of bel report files"""

        for path in DATA_EXCEL_BEL:
            isotherm = pygaps.isotherm_from_xl(path=path, fmt='bel')

            json_path = path.replace('.xls', '.json')

            with open(json_path, 'r') as file:
                assert isotherm == pygaps.isotherm_from_json(file.read())
