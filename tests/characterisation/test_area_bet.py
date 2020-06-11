"""
This test module has tests relating to BET area calculation.

All functions in /calculations/area_bet.py are tested here.
The purposes are:

    - testing the user-facing API function (area_BET)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose
from numpy import linspace

import pygaps
import pygaps.characterisation.area_bet as ab

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestAreaBET():
    """Tests BET surface area calculations."""
    def test_basic_functions(self):
        """Test basic functionality."""
        P = linspace(0, 1)
        L = linspace(0.3, 10)

        # arrays should be equal
        with pytest.raises(pygaps.ParameterError):
            ab.area_BET_raw(P[1:], L, 1)

        # should not take less than 2 points
        with pytest.raises(pygaps.CalculationError):
            ab.area_BET_raw(P[:2], L[:2], 1, limits=[-1, 10])

        # 3 will work
        ab.area_BET_raw(P[:3], L[:3], 1, limits=[-1, 10])

        # test using rouquerol
        ab.area_BET_raw(P, L, 1)

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_area_bet(self, sample):
        """Test calculation with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('bet_area', None):

            filepath = os.path.join(DATA_N77_PATH, sample['file'])
            isotherm = pygaps.isotherm_from_jsonf(filepath)

            bet_area = ab.area_BET(isotherm).get("area")

            err_relative = 0.1  # 10 percent
            err_absolute = 0.1  # 0.1 m2

            assert isclose(
                bet_area, sample['bet_area'], err_relative, err_absolute
            )

    def test_area_BET_choice(self):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = os.path.join(DATA_N77_PATH, sample['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)

        bet_area = ab.area_BET(isotherm, limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(
            bet_area, sample['s_bet_area'], err_relative, err_absolute
        )

    @cleanup
    def test_area_BET_output(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = os.path.join(DATA_N77_PATH, sample['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)
        ab.area_BET(isotherm, verbose=True)
