"""Tests csv interaction."""

import pytest

from pygaps.parsing.csv import isotherm_from_csv
from pygaps.parsing.csv import isotherm_to_csv
from pygaps.utilities.exceptions import ParsingError


@pytest.mark.parsing
class TestCSV():
    """All testing of CSV interface"""
    def test_csv_isotherm_checks(self):
        """Sanity checks for the CSV parser."""

        # basic from string
        text = "material,test\nadsorbate,test\ntemperature,303\n"
        assert isotherm_from_csv(text)

        # empty value
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,"
        assert isotherm_from_csv(text).new is None

        # multiple value errors
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,1,2"
        with pytest.raises(ParsingError):
            isotherm_from_csv(text)

        # bool in csv
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,True"
        assert isotherm_from_csv(text).new is True

        # list in csv
        text = "material,test\nadsorbate,test\ntemperature,303\nnew,[1 2 3]"
        assert isotherm_from_csv(text).new == [1, 2, 3]

    def test_csv_isotherm(self, basic_isotherm, tmpdir_factory):
        """Test creation of the Isotherm CSV."""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        isotherm_to_csv(basic_isotherm, path)

        isotherm = isotherm_from_csv(path)

        assert isotherm == basic_isotherm

    def test_csv_pointisotherm(self, basic_pointisotherm, tmpdir_factory):
        """Test creation of the PointIsotherm CSV."""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        isotherm_to_csv(basic_pointisotherm, path)

        isotherm = isotherm_from_csv(path)

        assert isotherm == basic_pointisotherm

    def test_csv_modelisotherm(self, basic_modelisotherm, tmpdir_factory):
        """Test creation of the ModelIsotherm CSV."""

        path = tmpdir_factory.mktemp('csv').join('isotherm.csv').strpath

        isotherm_to_csv(basic_modelisotherm, path)

        isotherm = isotherm_from_csv(path)

        assert isotherm.to_dict() == basic_modelisotherm.to_dict()

    def test_csv_isotherm_self(self, basic_isotherm, tmpdir_factory):
        """Test creation of class CSV function."""

        isotherm_json_std = isotherm_to_csv(basic_isotherm)
        new_isotherm_cls = basic_isotherm.to_csv()
        assert isotherm_json_std == new_isotherm_cls
