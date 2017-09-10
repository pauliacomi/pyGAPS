"""
This test module has tests relating to alpha_s calculations
"""

import os

import pytest

import pygaps

from .conftest import DATA
from .conftest import HERE
from .conftest import approx


class TestAlphaSPlot(object):
    """
    Tests everything related to alpha-s calculation
    """

    def test_alphas_checks(self, basic_pointisotherm, basic_adsorbate, basic_sample):
        """Test checks"""

        isotherm = basic_pointisotherm
        adsorbate = basic_adsorbate

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(Exception):
            pygaps.alpha_s(isotherm, isotherm)

        pygaps.data.GAS_LIST.append(adsorbate)
        isotherm.convert_mode_pressure("relative")

        pygaps.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_mode_adsorbent("volume")

        # Will raise a "isotherm loading not in volume mode exception"
        with pytest.raises(Exception):
            pygaps.alpha_s(isotherm, isotherm)

        isotherm.convert_mode_adsorbent("mass")

        # Will raise a "no suitable model exception"
        with pytest.raises(Exception):
            pygaps.alpha_s(isotherm, isotherm)

        return

    @pytest.mark.xfail
    @pytest.mark.parametrize('file, area, micropore_volume',
                             [(data['file'],
                               data['t_area'],
                               data['t_pore_volume']) for data in list(DATA.values())]
                             )
    def test_alphas(self, file, basic_adsorbate, area, micropore_volume):
        """Test calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        res = pygaps.alpha_s(
            isotherm, isotherm)

        results = res.get('results')
        assert results is not None

        max_error = 0.3  # 30 percent

        assert approx(results[-1].get('adsorbed_volume'),
                      micropore_volume, max_error)
        assert approx(results[-1].get('area'), area, max_error)

    @pytest.mark.xfail
    def test_alphas_choice(self, basic_adsorbate):
        """Test choice of points"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        data = DATA['MCM-41']

        filepath = os.path.join(HERE, 'data', 'isotherms_json', data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        res = pygaps.alpha_s(
            isotherm, isotherm, limits=[0.7, 1.0])
        results = res.get('results')

        max_error = 0.3  # 30 percent

        assert approx(results[-1].get('adsorbed_volume'),
                      data['t_pore_volume'], max_error)
        assert approx(results[-1].get('area'), data['t_area'], max_error)

    def test_alphas_output(self, basic_adsorbate, noplot):
        """Test verbosity"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        data = DATA['MCM-41']

        filepath = os.path.join(HERE, 'data', 'isotherms_json', data['file'])

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        t_plot_r = pygaps.alpha_s(
            isotherm, isotherm, verbose=True)

        t_plot_r.get('results')
