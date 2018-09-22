"""
This test module has tests relating to Langmuir area calculations
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestAreaLangmuir(object):
    """
    Tests everything related to Langmuir surface area calculation
    """

    @pytest.mark.parametrize('file, expected_langmuir',
                             [(data['file'], data['langmuir_area']) for data in list(DATA.values())])
    def test_area_langmuir(self, file, expected_langmuir):
        """Test calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        langmuir_area = pygaps.area_langmuir(isotherm).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(langmuir_area, expected_langmuir,
                       err_relative, err_absolute)

    def test_area_langmuir_choice(self):
        """Test choice of points"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        langmuir_area = pygaps.area_langmuir(
            isotherm, limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(langmuir_area, data['s_langmuir_area'],
                       err_relative, err_absolute)

    @cleanup
    def test_area_langmuir_output(self):
        """Test verbosity"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        pygaps.area_langmuir(isotherm, verbose=True)
