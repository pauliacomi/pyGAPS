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
import logging

import pytest
from numpy import isclose
from numpy import linspace

import pygaps.characterisation.area_bet as ab
import pygaps.parsing.json as pgpj
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestAreaBET():
    """Tests BET surface area calculations."""

    def test_basic_functions(self):
        """Test basic functionality."""
        P = linspace(0, 1)
        L = linspace(0.3, 10)

        # arrays should be equal
        with pytest.raises(pgEx.ParameterError):
            ab.area_BET_raw(P[1:], L, 1)

        # should not take less than 3 points
        with pytest.raises(pgEx.CalculationError):
            ab.area_BET_raw(P[:2], L[:2], 1, p_limits=[-1, 10])

        # 3 will work
        ab.area_BET_raw(P[:3], L[:3], 1, p_limits=[-1, 10])

        # Basic automatic limit test (using rouquerol)
        ab.area_BET_raw(P, L, 1)

    def test_limit_selection(self):
        """Test the automatic selection of limits."""

        P = [0.001, 0.004, 0.009, 0.042, 0.093, 0.124, 0.156, 0.186]
        L = [118, 135, 146, 172, 189, 195, 200, 203]

        # Enough points here
        ab.area_BET_raw(P, L, 1)

        # Not enough points here
        with pytest.raises(pgEx.CalculationError):
            ab.area_BET_raw(P[4:], L[4:], 1)

    @pytest.mark.parametrize('sample', DATA.values())
    def test_area_bet(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'bet_area' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = ab.area_BET(isotherm).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['bet_area'], err_relative, err_absolute)

    def test_area_BET_choice(self, data_char_path):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = ab.area_BET(isotherm, p_limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['bet_area_s'], err_relative, err_absolute)

    def test_area_BET_branch(self, data_char_path, caplog):
        """Test branch to use."""

        sample = DATA['SiO2']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        with caplog.at_level(logging.WARNING):  # warns about the monolayer value
            area = ab.area_BET(isotherm, branch="des").get("area")
        assert caplog.records

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2
        assert isclose(area, sample['bet_area_des'], err_relative, err_absolute)

    @mpl_cleanup
    def test_area_BET_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        ab.area_BET(isotherm, verbose=True)
