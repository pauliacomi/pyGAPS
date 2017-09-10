"""
This test module has tests relating to pore size distribution calculations
"""

import os

import pytest

import pygaps

# from .conftest import approx
from .conftest import HERE


class TestPSD(object):
    """
    Tests everything related to pore size distribution calculation
    """
    @pytest.mark.parametrize('method', [
        'BJH',
        'DH',
    ])
    @pytest.mark.parametrize('file', [
        ('MCM-41 N2 77.355.json'),
        #        ('NaY N2 77.355.json'),
        #        ('SiO2 N2 77.355.json'),
        #        ('Takeda 5A N2 77.355.json'),
        #        ('UiO-66(Zr) N2 77.355.json'),
    ])
    def test_psd_meso(self, file, basic_adsorbate, method):
        """Test psd calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        result_dict = pygaps.mesopore_size_distribution(
            isotherm, psd_model=method, branch='desorption', thickness_model='Halsey', verbose=False)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None

    @pytest.mark.parametrize('method', [
        'HK',
    ])
    @pytest.mark.parametrize('file', [
        ('Takeda 5A N2 77.355.json'),
        ('UiO-66(Zr) N2 77.355.json'),
    ])
    def test_psd_micro(self, file, basic_adsorbate, method):
        """Test psd calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        result_dict = pygaps.micropore_size_distribution(
            isotherm, psd_model=method, pore_geometry='slit', verbose=False)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None
