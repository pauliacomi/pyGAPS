"""
This test module has tests relating to initial henry constant
"""

import os

import pytest
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestInitialHenry(object):
    """
    Tests all initial henry methods
    """

    @pytest.mark.parametrize('file, expected',
                             [(data['file'], data['Khslope']) for data in list(DATA.values())])
    def test_ihenry_slope(self, file, expected):
        "The initial slope method"

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(text_file.read())

        ihenry_slope = pygaps.initial_henry_slope(
            isotherm, max_adjrms=0.01, verbose=False)

        err_relative = 0.1  # 10 percent
        err_absolute = 10   #

        assert isclose(ihenry_slope, expected, err_relative, err_absolute)

    @pytest.mark.parametrize('file, expected',
                             [(data['file'], data['Khvirial']) for data in list(DATA.values())])
    def test_ihenry_virial(self, file, expected):
        "The virial method"

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(text_file.read())

        ihenry_virial = pygaps.initial_henry_virial(isotherm, verbose=False)

        err_relative = 0.1  # 10 percent
        err_absolute = 10   #

        assert isclose(ihenry_virial, expected, err_relative, err_absolute)
