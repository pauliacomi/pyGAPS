"""Tests ISODB interaction."""

import pytest

import pygaps


@pytest.mark.parsing
class TestISODB():
    def test_get_isotherm(self):
        """Test the parsing of an isotherm to json."""
        pygaps.isotherm_from_isodb('10.1002adfm.201200084.Isotherm3')
