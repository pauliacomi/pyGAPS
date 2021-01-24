"""
This test module has tests relating to Dubinin plots.

All functions in /calculations/dr_da_plots.py are tested here.
The purposes are:

    - testing the user-facing API function (dr_plot, da_plot)
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
class TestDAPlot():
    """Tests DA and DR plots."""
    def test_dr_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "negative exponent" error.
        with pytest.raises(pgEx.ParameterError):
            pygaps.da_plot(basic_pointisotherm, exp=-2)

        filepath = DATA_N77_PATH / DATA['Takeda 5A']['file']
        isotherm = pygaps.isotherm_from_json(filepath)

        # Will raise "bad limits" error.
        with pytest.raises(pgEx.CalculationError):
            pygaps.dr_plot(isotherm, limits=[0.2, 0.1])

        # These limits work
        pygaps.dr_plot(isotherm, limits=[0, 0.2])

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_dr_plot(self, sample):
        """Test calculation with several model isotherms."""
        sample = DATA[sample]
        # Exclude datasets where it is not applicable.
        if sample.get('dr_volume', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            res = pygaps.dr_plot(isotherm)

            dr_vol = res.get("pore_volume")
            dr_pot = res.get("adsorption_potential")

            err_relative = 0.05  # 5 percent
            err_absolute = 0.01  # 0.01 cm3/g

            assert isclose(
                dr_vol, sample['dr_volume'], err_relative, err_absolute
            )
            assert isclose(
                dr_pot, sample['dr_potential'], err_relative, err_absolute
            )

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_da_plot(self, sample):
        """Test calculation with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('da_volume', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            res = pygaps.da_plot(isotherm, limits=[0, 0.01])

            da_vol = res.get("pore_volume")
            da_pot = res.get("adsorption_potential")

            err_relative = 0.05  # 5 percent
            err_absolute = 0.01  # 0.01 cm3/g

            assert isclose(
                da_vol, sample['da_volume'], err_relative, err_absolute
            )
            assert isclose(
                da_pot, sample['da_potential'], err_relative, err_absolute
            )

    @cleanup
    def test_da_output(self):
        """Test verbosity."""
        sample = DATA['Takeda 5A']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.da_plot(isotherm, verbose=True)
