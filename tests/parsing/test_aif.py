"""Tests AIF interaction."""

import pytest

from pygaps.utilities.exceptions import ParsingError
from pygaps.parsing.aif import isotherm_to_aif
from pygaps.parsing.aif import isotherm_from_aif


@pytest.mark.parsing
class TestAIF():
    def test_aif_pointisotherm(self, basic_pointisotherm, tmpdir_factory):
        """Test creation of the PointIsotherm AIF."""

        path = tmpdir_factory.mktemp('aif').join('isotherm.aif').strpath

        isotherm_to_aif(basic_pointisotherm, path)
        isotherm_to_aif(basic_pointisotherm, 'test')

        isotherm = isotherm_from_aif(path)
        isotherm_to_aif(isotherm, 'test2s')

        assert isotherm.to_dict() == basic_pointisotherm.to_dict()
        assert isotherm == basic_pointisotherm
