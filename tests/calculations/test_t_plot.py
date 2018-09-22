"""
This test module has tests relating to tplot calculations
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestTPlot(object):
    """
    Tests everything related to tplot calculation
    """

    def test_tplot_checks(self, basic_pointisotherm, basic_sample):
        """Test checks"""

        # Will raise a "no suitable model exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.t_plot(basic_pointisotherm, thickness_model='random')

        return

    @pytest.mark.parametrize('file, area, micropore_volume',
                             [(data['file'],
                               data['t_area'],
                               data['t_pore_volume']) for data in list(DATA.values())]
                             )
    def test_tplot(self, file, area, micropore_volume):
        """Test calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        res = pygaps.t_plot(
            isotherm, thickness_model='Halsey')

        results = res.get('results')
        assert results is not None

        err_relative = 0.3  # 30 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(results[-1].get('adsorbed_volume'),
                       micropore_volume, err_relative, err_absolute_area)
        assert isclose(results[-1].get('area'), area,
                       err_relative, err_absolute_volume)

    def test_tplot_choice(self):
        """Test choice of points"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        res = pygaps.t_plot(
            isotherm, 'Halsey', limits=[0.7, 1.0])
        results = res.get('results')

        err_relative = 0.3  # 30 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(results[-1].get('adsorbed_volume'),
                       data['t_pore_volume'], err_relative, err_absolute_area)
        assert isclose(results[-1].get('area'),
                       data['t_area'], err_relative, err_absolute_volume)

    @cleanup
    def test_tplot_output(self, noplot):
        """Test verbosity"""

        data = DATA['MCM-41']

        filepath = os.path.join(DATA_N77_PATH, data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        pygaps.t_plot(isotherm, 'Halsey', verbose=True)
