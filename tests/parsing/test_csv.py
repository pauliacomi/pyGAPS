"""Tests csv interaction."""

import pytest

import pygaps.parsing as pgp
from pygaps.utilities.exceptions import ParsingError

from .conftest import DATA_CSV
from .conftest import DATA_JSON


@pytest.mark.parsing
class TestCSV():
    """All testing of CSV interface"""
    def test_csv_isotherm_checks(self):
        """Sanity checks for the CSV parser."""

        # basic from string
        text = "material,test\nadsorbate,test\ntemperature,303\n"
        assert pgp.isotherm_from_csv(text)

        # empty value
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,"
        assert pgp.isotherm_from_csv(text).properties['new'] is None

        # multiple value errors
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,1,2"
        with pytest.raises(ParsingError):
            pgp.isotherm_from_csv(text)

        # bool in csv
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,True"
        assert pgp.isotherm_from_csv(text).properties['new'] is True

        # list in csv
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,[1 2 3]"
        assert pgp.isotherm_from_csv(text).properties['new'] == [1, 2, 3]

    def test_csv_isotherm(self, basic_isotherm, tmp_path_factory):
        """Test creation of the Isotherm CSV."""
        path = tmp_path_factory.mktemp('csv') / 'baseisotherm.csv'
        pgp.isotherm_to_csv(basic_isotherm, path)
        isotherm = pgp.isotherm_from_csv(path)
        assert isotherm == basic_isotherm

    def test_csv_iso_material(self, basic_isotherm, basic_material, tmp_path_factory):
        """Test the parsing of an isotherm that has a special material to json."""
        path = tmp_path_factory.mktemp('csv') / 'isotherm_mat.csv'
        basic_isotherm.material = basic_material
        pgp.isotherm_to_csv(basic_isotherm, path)
        isotherm = pgp.isotherm_from_csv(path)
        assert isotherm == basic_isotherm

    def test_csv_pointisotherm(self, basic_pointisotherm, tmp_path_factory):
        """Test creation of the PointIsotherm CSV."""
        path = tmp_path_factory.mktemp('csv') / 'pointisotherm.csv'
        pgp.isotherm_to_csv(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_csv(path)
        assert isotherm == basic_pointisotherm

    def test_csv_modelisotherm(self, basic_modelisotherm, tmp_path_factory):
        """Test creation of the ModelIsotherm CSV."""
        path = tmp_path_factory.mktemp('csv') / 'modelisotherm.csv'
        pgp.isotherm_to_csv(basic_modelisotherm, path)
        isotherm = pgp.isotherm_from_csv(path)
        assert isotherm.to_dict() == basic_modelisotherm.to_dict()

    def test_csv_isotherm_self(self, basic_isotherm):
        """Test creation of class 'to_csv' function."""
        isotherm_json_std = pgp.isotherm_to_csv(basic_isotherm)
        new_isotherm_cls = basic_isotherm.to_csv()
        assert isotherm_json_std == new_isotherm_cls

    @pytest.mark.parametrize("path", DATA_CSV)
    def test_csv_read(self, path):
        """Test reading of some CSVs."""
        isotherm = pgp.isotherm_from_csv(path)
        assert isotherm

    @pytest.mark.parametrize("path_json", DATA_JSON)
    def test_csv_write_read(self, path_json, tmp_path_factory):
        """Test various parsings in CSV files."""
        isotherm = pgp.isotherm_from_json(path_json)

        # round the iso dataframe to the parser precision
        isotherm.data_raw = isotherm.data_raw.round(pgp._PARSER_PRECISION)

        path = tmp_path_factory.mktemp('csv') / path_json.with_suffix(".csv").name
        pgp.isotherm_to_csv(isotherm, path)
        isotherm2 = pgp.isotherm_from_csv(path)
        assert isotherm.to_dict() == isotherm2.to_dict()
        assert isotherm == isotherm2
