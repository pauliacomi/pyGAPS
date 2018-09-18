"""
This test module has tests relating to pore size distribution calculations
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestPSD(object):
    """
    Tests everything related to pore size distribution calculation
    """

    def test_psd_meso_checks(self, basic_pointisotherm, basic_sample):

        # Will raise a "no model exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.mesopore_size_distribution(basic_pointisotherm, None)

        # Will raise a "no suitable model exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.mesopore_size_distribution(basic_pointisotherm, 'Test')

        # Will raise a "no applicable geometry exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.mesopore_size_distribution(
                basic_pointisotherm, 'BJH', pore_geometry='test')

        # Will raise a "no applicable branch exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.mesopore_size_distribution(
                basic_pointisotherm, 'BJH', branch='test')

    @cleanup
    @pytest.mark.parametrize('method', [
        'BJH',
        'DH',
    ])
    @pytest.mark.parametrize('file', [
        (data['file']) for data in list(DATA.values())
    ])
    def test_psd_meso(self, file, method):
        """Test psd calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        result_dict = pygaps.mesopore_size_distribution(
            isotherm,
            psd_model=method,
            branch='des',
            verbose=True)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None

    def test_psd_micro_checks(self, basic_pointisotherm):

        # Will raise a "no model exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.micropore_size_distribution(basic_pointisotherm, None)

        # Will raise a "no suitable model exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.micropore_size_distribution(basic_pointisotherm, 'Test')

        # Will raise a "no applicable geometry exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.micropore_size_distribution(
                basic_pointisotherm, 'HK', pore_geometry='test')

        # Will raise a "no applicable branch exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.micropore_size_distribution(
                basic_pointisotherm, 'BJH', branch='test')

    @cleanup
    @pytest.mark.parametrize('method', [
        'HK',
    ])
    @pytest.mark.parametrize('file', [
        (data['file']) for data in list(DATA.values())
    ])
    def test_psd_micro(self, file, method):
        """Test psd calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        result_dict = pygaps.micropore_size_distribution(
            isotherm,
            psd_model=method,
            pore_geometry='slit',
            verbose=True)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None

    def test_psd_dft_checks(self, basic_pointisotherm):

        # Will raise a "no kernel exception"
        with pytest.raises(pygaps.ParameterError):
            pygaps.micropore_size_distribution(basic_pointisotherm, None)

        return

    @cleanup
    @pytest.mark.parametrize('file', [
        (data['file']) for data in list(DATA.values())
    ])
    def test_psd_dft(self, file):
        """Test psd calculation with several model isotherms"""

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        result_dict = pygaps.dft_size_distribution(
            isotherm,
            'internal',
            verbose=True)

        # max_error = 0.1  # 10 percent

        assert result_dict is not None

        return
