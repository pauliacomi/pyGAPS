"""
This test module has tests relating to BET area calculations
"""

import os

import pytest
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import HERE


class TestBET(object):
    """
    Tests everything related to BET surface area calculation
    """

    def test_BET_checks(self, basic_pointisotherm, basic_adsorbate, basic_sample):
        """Test checks"""

        isotherm = basic_pointisotherm
        adsorbate = basic_adsorbate

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.area_BET(isotherm)

        pygaps.data.GAS_LIST.append(adsorbate)
        isotherm.convert_mode_pressure("relative")

        pygaps.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_mode_adsorbent("volume")

        # Will raise a "isotherm loading not in volume mode exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.area_BET(isotherm)

        isotherm.convert_mode_adsorbent("mass")

        return

    @pytest.mark.parametrize('file, expected_bet',
                             [(data['file'], data['bet_area']) for data in list(DATA.values())])
    def test_BET(self, file, expected_bet, basic_adsorbate):
        """Test calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        bet_area = pygaps.area_BET(isotherm).get("bet_area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(bet_area, expected_bet, err_relative, err_absolute)

    def test_BET_choice(self, basic_adsorbate):
        """Test choice of points"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        data = DATA['MCM-41']

        filepath = os.path.join(HERE, 'data', 'isotherms_json', data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        bet_area = pygaps.area_BET(
            isotherm, limits=[0.05, 0.30]).get("bet_area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(bet_area, data['s_bet_area'],
                       err_relative, err_absolute)

    def test_BET_output(self, basic_adsorbate, noplot):
        """Test verbosity"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        data = DATA['MCM-41']

        filepath = os.path.join(HERE, 'data', 'isotherms_json', data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        pygaps.area_BET(isotherm, verbose=True)
