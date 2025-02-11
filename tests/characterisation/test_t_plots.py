"""
This test module has tests relating to t-plots

All functions in /calculations/tplot.py are tested here.
The purposes are:

    - testing the user-facing API function (tplot)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import pytest
from numpy import isclose

import pygaps.characterisation.t_plots as pt
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestTPlot():
    """Tests t-plot calculations."""

    def test_t_plot_checks(self, use_adsorbate, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "no suitable model exception"
        with pytest.raises(pgEx.ParameterError):
            pt.t_plot(basic_pointisotherm, thickness_model='random')

    @pytest.mark.parametrize('sample', DATA.values())
    def test_t_plot(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 't_area' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        res = pt.t_plot(isotherm)
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(
            results[-1].get('adsorbed_volume'),
            sample['t_pore_volume'],
            err_relative,
            err_absolute_area,
        )
        assert isclose(
            results[0].get('area'),
            sample['t_area'],
            err_relative,
            err_absolute_volume,
        )

    def test_t_plot_choice(self, data_char_path):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        res = pt.t_plot(isotherm, t_limits=[0.7, 1.0])
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(
            results[-1].get('adsorbed_volume'),
            sample['t_pore_volume'],
            err_relative,
            err_absolute_area,
        )
        assert isclose(
            results[-1].get('area'),
            sample['s_t_area'],
            err_relative,
            err_absolute_volume,
        )

    @mpl_cleanup
    def test_t_plot_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        pt.t_plot(isotherm, 'Halsey', verbose=True)
