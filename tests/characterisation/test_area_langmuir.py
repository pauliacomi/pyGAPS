"""
This test module has tests relating to Langmuir area calculations.

All functions in /calculations/area_langmuir.py are tested here.
The purposes are:

    - testing the user-facing API function (area_langmuir)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import pytest
from numpy import isclose
from numpy import linspace

import pygaps.characterisation.area_lang as al
import pygaps.parsing.json as pgpj
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestAreaLangmuir():
    """Tests Langmuir surface area calculations."""

    def test_basic_functions(self):
        """Test basic functionality."""
        P = linspace(0, 1)
        L = linspace(0.3, 10)

        # arrays should be equal
        with pytest.raises(pgEx.ParameterError):
            al.area_langmuir_raw(P[1:], L, 1)

        # should not take less than 3 points
        with pytest.raises(pgEx.CalculationError):
            al.area_langmuir_raw(P[:2], L[:2], 1, p_limits=[-1, 10])

        # 3 will work
        al.area_langmuir_raw(P[:3], L[:3], 1, p_limits=[-1, 10])

        # test using autolimits
        al.area_langmuir_raw(P, L, 1)

    @pytest.mark.parametrize('sample', DATA.values())
    def test_area_langmuir(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'langmuir_area' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = al.area_langmuir(isotherm).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['langmuir_area'], err_relative, err_absolute)

    def test_area_langmuir_choice(self, data_char_path):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = al.area_langmuir(isotherm, p_limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['langmuir_area_s'], err_relative, err_absolute)

    def test_area_langmuir_branch(self, data_char_path):
        """Test branch to use."""

        sample = DATA['Takeda 5A']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = al.area_langmuir(isotherm, branch="des").get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2
        assert isclose(area, sample['langmuir_area'], err_relative, err_absolute)

    @mpl_cleanup
    def test_area_langmuir_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        al.area_langmuir(isotherm, verbose=True)
