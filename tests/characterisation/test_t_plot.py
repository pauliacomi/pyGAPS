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
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestTPlot():
    """Tests t-plot calculations."""
    def test_alphas_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "no suitable model exception"
        with pytest.raises(pgEx.ParameterError):
            pygaps.t_plot(basic_pointisotherm, thickness_model='random')

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_tplot(self, sample):
        """Test calculation with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('t_area', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            res = pygaps.t_plot(isotherm)
            results = res.get('results')

            err_relative = 0.1  # 10 percent
            err_absolute_area = 0.1  # units
            err_absolute_volume = 0.01  # units

            assert isclose(
                results[-1].get('adsorbed_volume'), sample['t_pore_volume'],
                err_relative, err_absolute_area
            )
            assert isclose(
                results[0].get('area'), sample['t_area'], err_relative,
                err_absolute_volume
            )

    def test_tplot_choice(self):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)

        res = pygaps.t_plot(isotherm, limits=[0.7, 1.0])
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(
            results[-1].get('adsorbed_volume'), sample['t_pore_volume'],
            err_relative, err_absolute_area
        )
        assert isclose(
            results[-1].get('area'), sample['s_t_area'], err_relative,
            err_absolute_volume
        )

    @cleanup
    def test_tplot_output(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.t_plot(isotherm, 'Halsey', verbose=True)
