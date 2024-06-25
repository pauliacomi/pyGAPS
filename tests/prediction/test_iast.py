"""
Tests relating to IAST calculations.

All functions in /calculations/iast.py are tested here.
The purposes are:

    - testing the user-facing API functions and graphical outputs
      (iast_binary_vle, iast_binary_svp)
    - testing individual low level functions against known results
      (iast, reverse_iast).

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import logging

import numpy
import pytest

import pygaps
import pygaps.parsing as pgp
import pygaps.prediction.iast as pgi
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA_IAST
from .conftest import DATA_IAST_PATH


@pytest.fixture()
def load_iast():
    """A fixture which loads files from the disk."""
    filepath = DATA_IAST_PATH / DATA_IAST['CH4']['file']
    ch4 = pgp.isotherm_from_json(filepath)
    filepath = DATA_IAST_PATH / DATA_IAST['C2H6']['file']
    c2h6 = pgp.isotherm_from_json(filepath)
    return ch4, c2h6


@pytest.fixture()
def load_iast_models(load_iast):
    """Create models from the disk files."""
    ch4, c2h6 = load_iast
    ch4_m = pygaps.ModelIsotherm.from_pointisotherm(ch4, model='Langmuir')
    c2h6_m = pygaps.ModelIsotherm.from_pointisotherm(c2h6, model='Langmuir')
    return ch4_m, c2h6_m


@pytest.mark.prediction
class TestIAST():
    """Test IAST calculations."""
    def test_iast_checks(self, load_iast, load_iast_models, caplog):
        """Checks for built-in safeguards."""

        ch4, c2h6 = load_iast

        # Raises "not enough components error"
        with pytest.raises(pgEx.ParameterError):
            pgi.iast_point_fraction([ch4], [0.1], 1)

        # Raises "different dimensions of arrays"
        with pytest.raises(pgEx.ParameterError):
            pgi.iast_point_fraction([ch4, c2h6], [0.1], 1)

        # Raises "model cannot be used with IAST"
        ch4_m = pygaps.ModelIsotherm.from_pointisotherm(ch4, model='Virial')
        with pytest.raises(pgEx.ParameterError):
            pgi.iast_point_fraction([ch4_m, c2h6], [0.6, 0.4], 1)

        # Warning "extrapolate outside range"
        with caplog.at_level(logging.WARNING):
            pgi.iast_point_fraction(load_iast_models, [0.5, 0.5], 100)
        assert caplog.records

    def test_iast(self, load_iast):
        """Test on pre-calculated data."""

        gas_fraction = [0.5, 0.5]
        adsorbed_fractions = [0.23064, 0.76936]

        loadings = pgi.iast_point_fraction(load_iast, gas_fraction, 1)

        assert numpy.isclose(adsorbed_fractions[0], loadings[0], 0.001)

    def test_iast_model(self, load_iast_models):
        """Test on pre-calculated data."""

        gas_fraction = [0.5, 0.5]
        adsorbed_fractions = [0.2833, 0.7167]

        loadings = pgi.iast_point_fraction(load_iast_models, gas_fraction, 1)

        assert numpy.isclose(adsorbed_fractions[0], loadings[0], 0.001)

    @mpl_cleanup
    def test_iast_verbose(self, load_iast):
        """Test verbosity."""
        pgi.iast_point_fraction(load_iast, [0.5, 0.5], 1, verbose=True)


@pytest.mark.modelling
class TestReverseIAST():
    """Test reverse IAST calculations."""
    def test_reverse_iast_checks(self, load_iast, load_iast_models, caplog):
        """Checks for built-in safeguards."""

        ch4, c2h6 = load_iast

        # Raises "not enough components error"
        with pytest.raises(pgEx.ParameterError):
            pgi.reverse_iast([ch4], [0.1], 1)

        # Raises "different dimensions of arrays"
        with pytest.raises(pgEx.ParameterError):
            pgi.reverse_iast([ch4, c2h6], [0.1], 1)

        # Raises "fractions do not add up to 1"
        with pytest.raises(pgEx.ParameterError):
            pgi.reverse_iast([ch4, c2h6], [0.1, 0.4], 1)

        # Raises "model cannot be used with IAST"
        ch4_m = pygaps.ModelIsotherm.from_pointisotherm(ch4, model='Virial')
        with pytest.raises(pgEx.ParameterError):
            pgi.reverse_iast([ch4_m, c2h6], [0.6, 0.4], 1)

        # Warning "extrapolate outside range"
        with caplog.at_level(logging.WARNING):
            pgi.reverse_iast(load_iast_models, [0.5, 0.5], 100)
        assert len(caplog.records) == 1

    def test_reverse_iast(self, load_iast):
        """Test on pre-calculated data."""

        ideal_ads_fraction = [0.5, 0.5]
        ideal_gas_fraction = [0.815, 0.185]

        gas_fraction, actual_loading = pgi.reverse_iast(load_iast, ideal_ads_fraction, 1)

        actual_ads_fraction = actual_loading / numpy.sum(actual_loading)

        assert numpy.isclose(ideal_gas_fraction[0], gas_fraction[0], atol=0.1)
        assert numpy.isclose(ideal_ads_fraction[0], actual_ads_fraction[0], atol=0.05)

    def test_reverse_iast_model(self, load_iast_models):
        """Test on pre-calculated data."""

        ideal_ads_fraction = [0.5, 0.5]
        ideal_gas_fraction = [0.885, 0.115]

        gas_fraction, actual_loading = pgi.reverse_iast(load_iast_models, ideal_ads_fraction, 1)

        actual_ads_fraction = actual_loading / numpy.sum(actual_loading)

        assert numpy.isclose(ideal_gas_fraction[0], gas_fraction[0], atol=0.1)
        assert numpy.isclose(ideal_ads_fraction[0], actual_ads_fraction[0], atol=0.05)

    @mpl_cleanup
    def test_reverse_iast_verbose(self, load_iast):
        """Test verbosity."""
        pgi.reverse_iast(load_iast, [0.23064, 0.76936], 1, verbose=True)


@pytest.mark.modelling
class TestIASTVLE():
    """Test IAST VLE function."""
    def test_iast_vle_checks(self, load_iast):
        """Checks for built-in safeguards."""

        ch4, c2h6 = load_iast

        # Raises "not enough components error"
        with pytest.raises(pgEx.ParameterError):
            pgi.iast_binary_vle([ch4], 1)

    def test_iast_vle(self, load_iast):
        """Tests the vle-pressure graph"""

        result_dict = pgi.iast_binary_vle(load_iast, 1)

        x_data = result_dict['x']
        y_data = result_dict['y']

        dev = sum(y_data - x_data)
        expected_dev = 6.7

        assert numpy.isclose(dev, expected_dev, atol=0.1)

    def test_iast_vle_model(self, load_iast_models):
        """Tests the vle-pressure graph"""

        result_dict = pgi.iast_binary_vle(load_iast_models, 1)

        x_data = result_dict['x']
        y_data = result_dict['y']

        dev = sum(y_data - x_data)
        expected_dev = 8.8

        assert numpy.isclose(dev, expected_dev, atol=0.1)

    @mpl_cleanup
    def test_iast_vle_verbose(self, load_iast):
        """Test verbosity."""
        pgi.iast_binary_vle(load_iast, 1, verbose=True)


@pytest.mark.modelling
class TestIASTSVP():
    """Test IAST SVP function."""
    def test_iast_svp_checks(self, load_iast):
        """Checks for built-in safeguards."""

        ch4, c2h6 = load_iast

        # Raises "not enough components error"
        with pytest.raises(pgEx.ParameterError):
            pgi.iast_binary_svp([ch4], [0.1], [1, 2])

        # Raises error not adds to one
        with pytest.raises(pgEx.ParameterError):
            pgi.iast_binary_svp([ch4, c2h6], [0.1, 0.4], [1, 2])

    def test_iast_svp(self, load_iast):
        """Test the selectivity-pressure graph with point."""

        rng = numpy.linspace(0.01, 10, 30)

        result_dict = pgi.iast_binary_svp(load_iast, [0.5, 0.5], rng)

        expected_avg = 0.19
        avg = numpy.average(result_dict['selectivity'])

        assert numpy.isclose(avg, expected_avg, atol=0.01)

    def test_iast_svp_model(self, load_iast_models):
        """Test the selectivity-pressure graph with models."""

        rng = numpy.linspace(0.01, 10, 30)

        result_dict = pgi.iast_binary_svp(load_iast_models, [0.5, 0.5], rng)

        expected_avg = 0.13
        avg = numpy.average(result_dict['selectivity'])

        assert numpy.isclose(avg, expected_avg, atol=0.01)

    @mpl_cleanup
    def test_iast_vle_verbose(self, load_iast):
        """Test verbosity."""
        rng = numpy.linspace(0.01, 10, 30)
        pgi.iast_binary_svp(load_iast, [0.5, 0.5], rng, verbose=True)
