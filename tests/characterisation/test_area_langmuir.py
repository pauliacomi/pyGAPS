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

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
@pytest.mark.filterwarnings('ignore:The correlation is not linear.')
class TestAreaLangmuir():
    """Tests Langmuir surface area calculations."""

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_area_langmuir(self, sample):
        """Test calculation with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('langmuir_area', None):

            filepath = os.path.join(DATA_N77_PATH, sample['file'])
            isotherm = pygaps.isotherm_from_jsonf(filepath)

            bet_area = pygaps.area_langmuir(isotherm).get("area")

            err_relative = 0.1  # 10 percent
            err_absolute = 0.1  # 0.1 m2

            assert isclose(bet_area, sample['langmuir_area'],
                           err_relative, err_absolute)

    def test_area_langmuir_choice(self):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = os.path.join(DATA_N77_PATH, sample['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)

        langmuir_area = pygaps.area_langmuir(
            isotherm, limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(langmuir_area, sample['s_langmuir_area'],
                       err_relative, err_absolute)

    @cleanup
    def test_area_langmuir_output(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = os.path.join(DATA_N77_PATH, sample['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)
        pygaps.area_langmuir(isotherm, verbose=True)
