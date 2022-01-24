"""Tests AIF interaction."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_AIF


@pytest.mark.parsing
class TestAIF():
    def test_aif_pointisotherm(self, basic_pointisotherm, tmpdir_factory):
        """Test creation of the PointIsotherm AIF."""

        path = tmpdir_factory.mktemp('aif').join('isotherm.aif').strpath
        pgp.isotherm_to_aif(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)

        assert isotherm.to_dict() == basic_pointisotherm.to_dict()
        assert isotherm == basic_pointisotherm

    @pytest.mark.parametrize("path", DATA_AIF)
    def test_aif_read(self, path):
        """Test reading of some AIFs."""
        isotherm = pgp.isotherm_from_aif(path)
        json_path = path.with_suffix('.json')
        pgp.isotherm_to_json(isotherm, json_path, indent=4)
        # assert isotherm == pgp.isotherm_from_json(json_path)
