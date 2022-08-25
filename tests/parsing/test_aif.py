"""Tests AIF interaction."""

import pytest

import pygaps.parsing as pgp

from .conftest import DATA_AIF
from .conftest import DATA_JSON


@pytest.mark.parsing
class TestAIF():
    """Test AIF-related functionality."""
    def test_aif_baseisotherm(self, basic_isotherm, tmp_path_factory):
        """Test creation/read of BaseIsotherm AIF"""
        path = tmp_path_factory.mktemp('aif') / 'baseisotherm.aif'
        pgp.isotherm_to_aif(basic_isotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert isotherm.to_dict() == basic_isotherm.to_dict()
        assert isotherm == basic_isotherm

    def test_aif_pointisotherm(self, basic_pointisotherm, tmp_path_factory):
        """Test creation of the PointIsotherm AIF."""
        path = tmp_path_factory.mktemp('aif') / 'pointisotherm.aif'
        pgp.isotherm_to_aif(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert isotherm.to_dict() == basic_pointisotherm.to_dict()
        assert isotherm == basic_pointisotherm

    def test_aif_modelisotherm(self, basic_modelisotherm, tmp_path_factory):
        """Test creation/read of ModelIsotherm AIF."""
        path = tmp_path_factory.mktemp('aif') / 'modelisotherm.aif'
        pgp.isotherm_to_aif(basic_modelisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert isotherm.to_dict() == basic_modelisotherm.to_dict()
        assert isotherm == basic_modelisotherm

    def test_aif_isotherm_mat(self, basic_pointisotherm, basic_material, tmp_path_factory):
        """Test serialisation of material properties into AIF."""
        path = tmp_path_factory.mktemp('aif') / 'isotherm_mat.aif'
        basic_pointisotherm.material = basic_material
        pgp.isotherm_to_aif(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert isotherm.to_dict() == basic_pointisotherm.to_dict()
        assert isotherm == basic_pointisotherm

    @pytest.mark.parametrize("path", DATA_AIF)
    def test_aif_read(self, path):
        """Test reading of some AIFs."""
        isotherm = pgp.isotherm_from_aif(path)
        assert isotherm

    @pytest.mark.parametrize("use_pygaps_units", [True, False])
    @pytest.mark.parametrize("path_json", DATA_JSON)
    def test_aif_write_read(self, use_pygaps_units, path_json, tmp_path_factory):
        """Test various parsings in AIF files."""
        isotherm = pgp.isotherm_from_json(path_json)

        # round the iso dataframe to the parser precision
        isotherm.data_raw = isotherm.data_raw.round(pgp._PARSER_PRECISION)

        path = tmp_path_factory.mktemp('aif') / path_json.with_suffix(".aif").name
        pgp.isotherm_to_aif(isotherm, path)
        if use_pygaps_units:
            isotherm2 = pgp.isotherm_from_aif(path)
        else:
            if isotherm.loading_basis == 'volume_liquid':
                # TODO expected to fail at the moment
                return
            isotherm2 = pgp.isotherm_from_aif(path, _parse_units=True)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2
