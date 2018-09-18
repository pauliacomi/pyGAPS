"""
This test module has tests relating to IAST calculations
"""
import os

import numpy
import pytest

import pygaps
from pygaps.utilities.exceptions import ParameterError

from .conftest import DATA_IAST
from .conftest import DATA_IAST_PATH


@pytest.fixture()
def load_iast():
    """
    Loads the files from disk
    """
    filepath = os.path.join(DATA_IAST_PATH, DATA_IAST['CH4'].get('file'))

    with open(filepath, 'r') as text_file:
        ch4 = pygaps.isotherm_from_json(
            text_file.read())

    filepath = os.path.join(DATA_IAST_PATH, DATA_IAST['C2H6'].get('file'))

    with open(filepath, 'r') as text_file:
        c2h6 = pygaps.isotherm_from_json(
            text_file.read())

    return ch4, c2h6


@pytest.fixture()
def load_iast_models(load_iast):
    """
    Creates models from the disk files
    """

    ch4, c2h6 = load_iast

    ch4_model = pygaps.ModelIsotherm.from_pointisotherm(ch4, model='Langmuir')
    c2h6_model = pygaps.ModelIsotherm.from_pointisotherm(
        c2h6, model='Langmuir')

    return ch4_model, c2h6_model


@pytest.mark.modelling
class TestIAST(object):
    """Tests IAST calculations"""

    def test_iast_checks(self, load_iast):

        ch4, c2h6 = load_iast

        # IAST CHECKS
        # Raises error components
        with pytest.raises(ParameterError):
            pygaps.iast([ch4], [0.1])

        # Raises error different dimensions
        with pytest.raises(ParameterError):
            pygaps.iast([ch4, c2h6], [0.1])

        # REVERSE IAST CHECKS
        # Raises error components
        with pytest.raises(ParameterError):
            pygaps.reverse_iast([ch4], [0.1], 2)

        # Raises error different dimensions
        with pytest.raises(ParameterError):
            pygaps.reverse_iast([ch4, c2h6], [0.1], 2)

        # Raises error sum not adds to one
        with pytest.raises(ParameterError):
            pygaps.reverse_iast([ch4, c2h6], [0.1, 0.4], 2)

        # VLE CHECKS
        # Raises error components
        with pytest.raises(ParameterError):
            pygaps.iast_binary_vle([ch4], 1)

        # SVP CHECKS
        # Raises error components
        with pytest.raises(ParameterError):
            pygaps.iast_binary_svp([ch4], [0.1], [1, 2])

        # Raises error not adds to one
        with pytest.raises(ParameterError):
            pygaps.iast_binary_svp([ch4, c2h6], [0.1, 0.4], [1, 2])

    def test_iast(self, load_iast):

        ch4, c2h6 = load_iast

        adsorbed_fractions = [0.23064, 0.76936]
        partial_pressures = [0.5, 0.5]

        loadings = pygaps.iast([ch4, c2h6], partial_pressures, verbose=True)

        assert numpy.isclose(adsorbed_fractions[0], loadings[0], 0.001)

    def test_reverse_iast(self, load_iast):

        ch4, c2h6 = load_iast

        ideal_loadings = [0.23064, 0.76936]
        ideal_pressures = [0.5, 0.5]

        partial_pressures, loadings = pygaps.reverse_iast(
            [ch4, c2h6], ideal_loadings, 1, verbose=True)

        assert numpy.isclose(ideal_loadings[0], loadings[0], atol=0.05)
        assert numpy.isclose(
            ideal_pressures[0], partial_pressures[0], atol=0.1)

    def test_iast_svp(self, load_iast):
        """Tests the selectivity-pressure graph"""

        ch4, c2h6 = load_iast

        rng = numpy.linspace(0.01, 10, 30)

        result_dict = pygaps.iast_binary_svp([ch4, c2h6], [0.5, 0.5], rng)

        expected_avg = 0.19
        avg = numpy.average(result_dict['selectivity'])

        assert numpy.isclose(avg, expected_avg, atol=0.01)

    def test_iast_svp_model(self, load_iast_models):
        """Tests the selectivity-pressure graph"""

        ch4, c2h6 = load_iast_models

        rng = numpy.linspace(0.01, 10, 30)

        result_dict = pygaps.iast_binary_svp([ch4, c2h6], [0.5, 0.5], rng)

        expected_avg = 0.13
        avg = numpy.average(result_dict['selectivity'])

        assert numpy.isclose(avg, expected_avg, atol=0.01)

    def test_iast_vle(self, load_iast):
        """Tests the vle-pressure graph"""

        ch4, c2h6 = load_iast

        result_dict = pygaps.iast_binary_vle([ch4, c2h6], 1)

        x_data = result_dict['x']
        y_data = result_dict['y']

        dev = sum(y_data - x_data)
        expected_dev = 6.7

        assert numpy.isclose(dev, expected_dev, atol=0.1)
