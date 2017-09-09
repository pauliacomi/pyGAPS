"""
Tests excel interaction
"""

import pygaps
import pytest

from ..conftest import windows


@windows
@pytest.mark.slowtest
class TestExcel(object):

    def test_create_excel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the regular excel file"""

        path = tmpdir_factory.mktemp('excel').join('regular.xlsx').strpath
        pygaps.isotherm_to_xl(basic_pointisotherm,
                              path=path)

        isotherm = pygaps.isotherm_from_xl(path)

        assert isotherm == basic_pointisotherm

    def test_create_excel_madirel(self, basic_pointisotherm, tmpdir_factory):
        """Tests creation of the MADIREL file"""

        path = tmpdir_factory.mktemp('excel').join('MADIREL.xlsx').strpath
        pygaps.isotherm_to_xl(basic_pointisotherm,
                              path=path, fmt='MADIREL')

        isotherm = pygaps.isotherm_from_xl(path, fmt='MADIREL')

        assert isotherm == basic_pointisotherm
