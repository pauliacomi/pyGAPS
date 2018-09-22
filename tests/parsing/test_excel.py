"""
Tests excel interaction
"""
import pytest

import pygaps

from .conftest import DATA_EXCEL_BEL
from .conftest import DATA_EXCEL_MIC
from .conftest import DATA_EXCEL_STD


@pytest.mark.parsing
class TestExcel(object):

    def test_read_create_excel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the regular excel file"""

        path = tmpdir_factory.mktemp('excel').join('regular.xls').strpath

        pygaps.isotherm_to_xl(basic_pointisotherm, path=path)

        isotherm = pygaps.isotherm_from_xl(path)
        assert isotherm == basic_pointisotherm

    def test_read_create_excel_madirel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the MADIREL file"""

        iso_dict = basic_pointisotherm.to_dict()
        for key in pygaps.parsing.excelinterface._FIELDS_MADIREL:
            if not iso_dict.get(key):
                iso_dict[key] = ''

        for key in pygaps.parsing.excelinterface._FIELDS_MADIREL_ENTH:
            if not iso_dict.get(key):
                iso_dict[key] = ''

        iso_data = basic_pointisotherm._data

        isotherm = pygaps.PointIsotherm(iso_data,
                                        loading_key=basic_pointisotherm.loading_key,
                                        pressure_key=basic_pointisotherm.pressure_key,
                                        other_keys=basic_pointisotherm.other_keys,
                                        **iso_dict)

        path = DATA_EXCEL_STD[0]
        path = tmpdir_factory.mktemp('excel').join('MADIREL.xlx').strpath
        pygaps.isotherm_to_xl(isotherm,
                              path=path, fmt='MADIREL')

        from_iso = pygaps.isotherm_from_xl(path, fmt='MADIREL')
        assert from_iso == isotherm

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
