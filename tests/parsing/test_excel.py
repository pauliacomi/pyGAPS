"""
Tests excel interaction
"""

import pytest

import pygaps

from ..conftest import parsing
from .conftest import DATA_EXCEL_BEL
from .conftest import DATA_EXCEL_MIC
from .conftest import DATA_EXCEL_STD


@parsing
@pytest.mark.slowtest
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
        new_props = basic_pointisotherm.other_properties.copy()
        new_props.update({
            'henry_constant': '',
            'langmuir_n1': '', 'langmuir_b1': '',
            'langmuir_n2': '', 'langmuir_b2': '',
            'langmuir_n3': '', 'langmuir_b3': '',
            'langmuir_r2': '',
            'c1': '', 'c2': '', 'c3': '',
            'c4': '', 'c5': '', 'c6': '',
            'c_m': '',
            'enth_0': '', 'enth_a': '',
            'enth_b': '', 'enth_c': '',
            'enth_d': '', 'enth_e': '',
            'enth_f': '', 'enth_r2': '',
        })
        basic_pointisotherm.other_properties = new_props.copy()
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
