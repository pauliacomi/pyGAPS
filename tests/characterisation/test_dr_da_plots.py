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
from numpy import isclose

import pygaps.characterisation.dr_da_plots as drda
import pygaps.parsing.json as pgpj
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestDAPlot():
    """Tests DA and DR plots."""

    def test_dr_checks(self, basic_pointisotherm, data_char_path):
        """Checks for built-in safeguards."""

        # Will raise a "negative exponent" error.
        with pytest.raises(pgEx.ParameterError):
            drda.da_plot(basic_pointisotherm, exp=-2)

        filepath = data_char_path / DATA['Takeda 5A']['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        # Will raise "bad limits" error.
        with pytest.raises(pgEx.CalculationError):
            drda.dr_plot(isotherm, p_limits=[0.2, 0.1])

        # These limits work
        drda.dr_plot(isotherm, p_limits=[0, 0.2])

    @pytest.mark.parametrize('sample', DATA.values())
    def test_dr_plot(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # Exclude datasets where it is not applicable.
        if 'dr_volume' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        res = drda.dr_plot(isotherm)

        dr_vol = res.get("pore_volume")
        dr_pot = res.get("adsorption_potential")

        err_relative = 0.05  # 5 percent
        err_absolute = 0.01  # 0.01 cm3/g

        assert isclose(dr_vol, sample['dr_volume'], err_relative, err_absolute)
        assert isclose(dr_pot, sample['dr_potential'], err_relative, err_absolute)

    @pytest.mark.parametrize('sample', DATA.values())
    def test_da_plot(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'da_volume' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        res = drda.da_plot(isotherm, p_limits=[0, 0.01])

        da_vol = res.get("pore_volume")
        da_pot = res.get("adsorption_potential")

        err_relative = 0.05  # 5 percent
        err_absolute = 0.01  # 0.01 cm3/g

        assert isclose(da_vol, sample['da_volume'], err_relative, err_absolute)
        assert isclose(da_pot, sample['da_potential'], err_relative, err_absolute)

    @mpl_cleanup
    def test_da_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['Takeda 5A']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        drda.da_plot(isotherm, verbose=True)
