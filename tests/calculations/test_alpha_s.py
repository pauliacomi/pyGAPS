"""
This test module has tests relating to alpha_s calculations
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestAlphaSPlot(object):
    """
    Tests everything related to alpha-s calculation
    """

    def test_alphas_checks(self, basic_pointisotherm):
        """Test checks"""

        # Will raise a "no reference isotherm exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.alpha_s(basic_pointisotherm, None)

        # Will raise a "bad reducing pressure exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.alpha_s(basic_pointisotherm, basic_pointisotherm,
                           reducing_pressure=1.3)

        return

    @pytest.mark.parametrize('file, area, micropore_volume',
                             [(data['file'],
                               data['bet_area'],
                               0) for data in list(DATA.values())]
                             )
    def test_alphas(self, file, area, micropore_volume):
        """Test calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        res = pygaps.alpha_s(
            isotherm, isotherm)

        results = res.get('results')
        assert results is not None

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(results[-1].get('adsorbed_volume'),
                       micropore_volume, err_relative, err_absolute_area)
        assert isclose(results[-1].get('area'),
                       area, err_relative, err_absolute_volume)

    def test_alphas_choice(self):
        """Test choice of points"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        res = pygaps.alpha_s(
            isotherm, isotherm, limits=[0.7, 1.0])
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(results[-1].get('adsorbed_volume'),
                       0, err_relative, err_absolute_area)
        assert isclose(results[-1].get('area'),
                       data['bet_area'], err_relative, err_absolute_volume)

    @cleanup
    def test_alphas_output(self, noplot):
        """Test verbosity"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        pygaps.alpha_s(isotherm, isotherm, verbose=True)
