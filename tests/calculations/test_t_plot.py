"""
This test module has tests relating to tplot calculations
"""

import os

import pytest
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import HERE


class TestTPlot(object):
    """
    Tests everything related to tplot calculation
    """

    def test_tplot_checks(self, basic_pointisotherm, basic_adsorbate, basic_sample):
        """Test checks"""

        isotherm = basic_pointisotherm
        adsorbate = basic_adsorbate

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(Exception):
            pygaps.t_plot(isotherm, thickness_model='Halsey')

        pygaps.data.GAS_LIST.append(adsorbate)
        isotherm.convert_mode_pressure("relative")

        pygaps.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_mode_adsorbent("volume")

        # Will raise a "isotherm loading not in volume mode exception"
        with pytest.raises(Exception):
            pygaps.t_plot(isotherm, thickness_model='Halsey')

        isotherm.convert_mode_adsorbent("mass")

        # Will raise a "no suitable model exception"
        with pytest.raises(Exception):
            pygaps.t_plot(isotherm, thickness_model='random')

        return

    @pytest.mark.parametrize('file, area, micropore_volume',
                             [(data['file'],
                               data['t_area'],
                               data['t_pore_volume']) for data in list(DATA.values())]
                             )
    def test_tplot(self, file, basic_adsorbate, area, micropore_volume):
        """Test calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

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

    def test_tplot_choice(self, basic_adsorbate):
        """Test choice of points"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        data = DATA['MCM-41']

        filepath = os.path.join(HERE, 'data', 'isotherms_json', data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

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

    def test_tplot_output(self, basic_adsorbate, noplot):
        """Test verbosity"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        data = DATA['MCM-41']

        filepath = os.path.join(HERE, 'data', 'isotherms_json', data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        pygaps.t_plot(isotherm, 'Halsey', verbose=True)
