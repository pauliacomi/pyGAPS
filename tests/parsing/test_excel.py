"""
Tests excel interaction
"""

import pytest

import pygaps

from .conftest import DATA_EXCEL_MIC
from .conftest import DATA_EXCEL_BEL
from ..conftest import parsing
from ..conftest import windows


@windows
@parsing
@pytest.mark.slowtest
class TestExcel(object):

    def test_create_excel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the regular excel file"""

        path = tmpdir_factory.mktemp('excel').join('regular.xlsx').strpath
        try:
            pygaps.isotherm_to_xl(basic_pointisotherm,
                                  path=path)
        except SystemError:
            # Excel is not installed
            return

        isotherm = pygaps.isotherm_from_xl(path)

        assert isotherm == basic_pointisotherm

    def test_create_excel_madirel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the MADIREL file"""

        path = tmpdir_factory.mktemp('excel').join('MADIREL.xlsx').strpath
        try:
            pygaps.isotherm_to_xl(basic_pointisotherm,
                                  path=path, fmt='MADIREL')
        except SystemError as e_info:
            # Excel is not installed
            return

        isotherm = pygaps.isotherm_from_xl(path, fmt='MADIREL')

        assert isotherm == basic_pointisotherm

    def test_read_excel_mic(self):
        """Tests reading of micromeritics report files"""

        for path in DATA_EXCEL_MIC:
            isotherm = pygaps.isotherm_from_xl(path=path,
                                               fmt='mic')

            json_path = path.replace('.xls', '.json')

            with open(json_path, 'r') as file:
                assert pygaps.isotherm_to_json(isotherm) == file.read()

    def test_read_excel_bel(self):
        """Tests reading of bel report files"""

        for path in DATA_EXCEL_BEL:
            isotherm = pygaps.isotherm_from_xl(path=path,
                                               fmt='bel')

            json_path = path.replace('.xls', '.json')

            with open(json_path, 'r') as file:
                assert pygaps.isotherm_to_json(isotherm) == file.read()
