"""Tests relating to initial henry constant.

All functions in /calculations/initial_henry.py are tested here.
The purposes are:

    - testing the user-facing API functions (initial_henry_x)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterization can be found in the
/.conftest file together with the other isotherm parameters.
"""

import os

import pytest
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestInitialHenry():
    """Test all initial henry methods."""

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_ihenry_slope(self, sample):
        """Test initial slope method."""

        sample = DATA[sample]
        filepath = os.path.join(DATA_N77_PATH, sample['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)

        ihenry_slope = pygaps.initial_henry_slope(
            isotherm, max_adjrms=0.01, verbose=False)

        err_relative = 0.1  # 10 percent
        err_absolute = 10   #

        assert isclose(ihenry_slope, sample['Khi_slope'],
                       err_relative, err_absolute)

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_ihenry_virial(self, sample):
        """Test virial method."""

        sample = DATA[sample]
        filepath = os.path.join(DATA_N77_PATH, sample['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)

        ihenry_virial = pygaps.initial_henry_virial(isotherm, verbose=False)

        err_relative = 0.1  # 10 percent
        err_absolute = 10   #

        assert isclose(ihenry_virial, sample['Khi_virial'],
                       err_relative, err_absolute)
