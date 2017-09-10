"""
This test module has tests relating to pore size distribution calculations
"""

import os

import pytest

import pygaps

from numpy import isclose
from .conftest import HERE
from .conftest import DATA


class TestPSD(object):
    """
    Tests everything related to pore size distribution calculation
    """

    def test_psd_meso_checks(self, basic_pointisotherm, basic_adsorbate, basic_sample):

        isotherm = basic_pointisotherm
        adsorbate = basic_adsorbate

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(Exception):
            pygaps.mesopore_size_distribution(isotherm, isotherm)

        pygaps.data.GAS_LIST.append(adsorbate)
        isotherm.convert_mode_pressure("relative")

        pygaps.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_mode_adsorbent("volume")

        # Will raise a "isotherm loading not in mass mode exception"
        with pytest.raises(Exception):
            pygaps.mesopore_size_distribution(isotherm, isotherm)

        isotherm.convert_mode_adsorbent("mass")

        # Will raise a "no model exception"
        with pytest.raises(Exception):
            pygaps.mesopore_size_distribution(isotherm, None)

        # Will raise a "no suitable model exception"
        with pytest.raises(Exception):
            pygaps.mesopore_size_distribution(isotherm, 'Test')

        # Will raise a "no applicable geometry exception"
        with pytest.raises(Exception):
            pygaps.mesopore_size_distribution(
                isotherm, 'BJH', pore_geometry='test')

        # Will raise a "no applicable branch exception"
        with pytest.raises(Exception):
            pygaps.mesopore_size_distribution(isotherm, 'BJH', branch='test')

    @pytest.mark.parametrize('method', [
        'BJH',
        'DH',
    ])
    @pytest.mark.parametrize('file', [
        (data['file']) for data in list(DATA.values())
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
            isotherm,
            psd_model=method,
            branch='desorption',
            verbose=True)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None

    def test_psd_micro_checks(self, basic_pointisotherm, basic_adsorbate, basic_sample):

        isotherm = basic_pointisotherm
        adsorbate = basic_adsorbate

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(isotherm, isotherm)

        pygaps.data.GAS_LIST.append(adsorbate)
        isotherm.convert_mode_pressure("relative")

        pygaps.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_mode_adsorbent("volume")

        # Will raise a "isotherm loading not in mass mode exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(isotherm, isotherm)

        isotherm.convert_mode_adsorbent("mass")

        # Will raise a "no model exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(isotherm, None)

        # Will raise a "no suitable model exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(isotherm, 'Test')

        # Will raise a "no applicable geometry exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(
                isotherm, 'HK', pore_geometry='test')

        # Will raise a "no applicable branch exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(isotherm, 'BJH', branch='test')

    @pytest.mark.parametrize('method', [
        'HK',
    ])
    @pytest.mark.parametrize('file', [
        (data['file']) for data in list(DATA.values())
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
            isotherm,
            psd_model=method,
            pore_geometry='slit',
            verbose=True)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None

    def test_psd_dft_checks(self, basic_pointisotherm):

        isotherm = basic_pointisotherm

        # Will raise a "no kernel exception"
        with pytest.raises(Exception):
            pygaps.micropore_size_distribution(isotherm, None)

    @pytest.mark.parametrize('file', [
        (data['file']) for data in list(DATA.values())
    ])
    def test_psd_dft(self, file, basic_adsorbate):
        """Test psd calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        result_dict = pygaps.dft_size_distribution(
            isotherm,
            'internal',
            verbose=True)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None
