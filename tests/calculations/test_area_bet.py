"""
This test module has tests relating to BET area calculations
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestAreaBET(object):
    """
    Tests everything related to BET surface area calculation
    """

    @pytest.mark.parametrize('file, expected_bet',
                             [(data['file'], data['bet_area']) for data in list(DATA.values())])
    def test_area_BET(self, file, expected_bet):
        """Test calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        bet_area = pygaps.area_BET(isotherm).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(bet_area, expected_bet, err_relative, err_absolute)

    def test_area_BET_choice(self):
        """Test choice of points"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        bet_area = pygaps.area_BET(
            isotherm, limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(bet_area, data['s_bet_area'],
                       err_relative, err_absolute)

    @cleanup
    def test_area_BET_output(self, noplot):
        """Test verbosity"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        pygaps.area_BET(isotherm, verbose=True)
