"""Tests relating to initial henry constant.

All functions in /calculations/initial_henry.py are tested here.
The purposes are:

    - testing the user-facing API functions (initial_henry_x)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import pytest
from numpy import isclose

import pygaps.characterisation.initial_henry as ih
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestInitialHenry():
    """Test all initial henry methods."""

    @pytest.mark.parametrize('sample', DATA.values())
    def test_ihenry_slope(self, sample, data_char_path):
        """Test initial slope method with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'Khi_slope' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        ihenry_slope = ih.initial_henry_slope(isotherm, max_adjrms=0.01)

        err_relative = 0.1  # 10 percent
        err_absolute = 10  #

        assert isclose(ihenry_slope, sample['Khi_slope'], err_relative, err_absolute)

    def test_ihenry_slope_limits(self, data_char_path):
        """Test introducing limits in the initial slope method."""
        sample = DATA['SiO2']
        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        ih.initial_henry_slope(isotherm, max_adjrms=0.01, p_limits=[0, 0.2])
        ih.initial_henry_slope(isotherm, max_adjrms=0.01, p_limits=[0.2, None])
        ih.initial_henry_slope(isotherm, max_adjrms=0.01, l_limits=[5, None])

        with pytest.raises(pgEx.ParameterError):
            ih.initial_henry_slope(isotherm, max_adjrms=0.01, l_limits=[25, None])

    @mpl_cleanup
    def test_ihenry_slope_verbose(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        ih.initial_henry_slope(isotherm, verbose=True)

    @pytest.mark.parametrize('sample', DATA.values())
    def test_ihenry_virial(self, sample, data_char_path):
        """Test virial method with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'Khi_slope' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        ihenry_virial = ih.initial_henry_virial(isotherm)

        err_relative = 0.1  # 10 percent
        err_absolute = 10  #

        assert isclose(ihenry_virial, sample['Khi_virial'], err_relative, err_absolute)

    @mpl_cleanup
    def test_ihenry_virial_verbose(self, data_char_path):
        """Test verbosity."""
        sample = DATA['SiO2']
        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        ih.initial_henry_virial(isotherm, verbose=True)
