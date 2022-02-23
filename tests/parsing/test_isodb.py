"""Tests NIST ISODB interaction."""

import pytest

import pygaps.parsing.isodb as isodb


@pytest.mark.parsing
class TestISODB():
    def test_get_isotherm(self):
        """Test the parsing of an isotherm to json."""
        isodb.isotherm_from_isodb('10.1002adfm.201200084.Isotherm3')
