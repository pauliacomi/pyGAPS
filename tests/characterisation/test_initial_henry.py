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
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestInitialHenry():
    """Test all initial henry methods."""
    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_ihenry_slope(self, sample):
        """Test initial slope method with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('Khi_slope', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            ihenry_slope = pygaps.initial_henry_slope(
                isotherm, max_adjrms=0.01
            )

            err_relative = 0.1  # 10 percent
            err_absolute = 10  #

            assert isclose(
                ihenry_slope, sample['Khi_slope'], err_relative, err_absolute
            )

    def test_ihenry_slope_limits(self):
        """Test introducing limits in the initial slope method."""
        sample = DATA['SiO2']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.initial_henry_slope(
            isotherm, max_adjrms=0.01, p_limits=[0, 0.2]
        )
        pygaps.initial_henry_slope(
            isotherm, max_adjrms=0.01, p_limits=[0.2, None]
        )
        pygaps.initial_henry_slope(
            isotherm, max_adjrms=0.01, l_limits=[5, None]
        )

        with pytest.raises(pgEx.ParameterError):
            pygaps.initial_henry_slope(
                isotherm, max_adjrms=0.01, l_limits=[25, None]
            )

    @cleanup
    def test_ihenry_slope_verbose(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.initial_henry_slope(isotherm, verbose=True)

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_ihenry_virial(self, sample):
        """Test virial method with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('Khi_slope', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            ihenry_virial = pygaps.initial_henry_virial(isotherm)

            err_relative = 0.1  # 10 percent
            err_absolute = 10  #

            assert isclose(
                ihenry_virial, sample['Khi_virial'], err_relative, err_absolute
            )

    @cleanup
    def test_ihenry_virial_verbose(self):
        """Test verbosity."""
        sample = DATA['SiO2']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.initial_henry_virial(isotherm, verbose=True)
