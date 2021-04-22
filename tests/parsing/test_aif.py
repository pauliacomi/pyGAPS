"""Tests AIF interaction."""

import pytest

from pygaps.parsing.aif import isotherm_from_aif
from pygaps.parsing.aif import isotherm_to_aif

from .conftest import DATA_AIF


@pytest.mark.parsing
class TestAIF():
    def test_aif_pointisotherm(self, basic_pointisotherm, tmpdir_factory):
        """Test creation of the PointIsotherm AIF."""

        path = tmpdir_factory.mktemp('aif').join('isotherm.aif').strpath
        isotherm_to_aif(basic_pointisotherm, path)
        isotherm = isotherm_from_aif(path)

        assert isotherm.to_dict() == basic_pointisotherm.to_dict()
        assert isotherm == basic_pointisotherm

    def test_aif_read(self):
        """Test reading of some AIFs."""
        for path in DATA_AIF:
            isotherm_from_aif(path)
