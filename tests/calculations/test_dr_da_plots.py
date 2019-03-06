"""This test module has tests relating to Dubinin plots."""

import os

import pytest
from numpy import isclose

import pygaps

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestDAPlot():
    """
    Tests everything related to the DA and related plots
    """

    @pytest.mark.parametrize('file, exp_vol, exp_pot',
                             [(data['file'], data['dr_volume'], data['dr_potential']) for data in list(DATA.values())])
    def test_dr_plot(self, file, exp_vol, exp_pot):
        """Test calculation with takeda isotherm."""

        if exp_vol is None:
            return

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        res = pygaps.dr_plot(isotherm)

        dr_vol = res.get("pore_volume")
        dr_pot = res.get("adsorption_potential")

        err_relative = 0.05  # 5 percent
        err_absolute = 0.01  # 0.01 cm3/g

        assert isclose(dr_vol, exp_vol, err_relative, err_absolute)
        assert isclose(dr_pot, exp_pot, err_relative, err_absolute)

    @pytest.mark.parametrize('file, exp_vol, exp_pot',
                             [(data['file'], data['da_volume'], data['da_potential']) for data in list(DATA.values())])
    def test_da_plot(self, file, exp_vol, exp_pot):
        """Test calculation with takeda isotherm."""
        if exp_vol is None:
            return

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        res = pygaps.da_plot(isotherm, limits=[0, 0.01])

        da_vol = res.get("pore_volume")
        da_pot = res.get("adsorption_potential")

        err_relative = 0.05  # 5 percent
        err_absolute = 0.01  # 0.01 cm3/g

        assert isclose(da_vol, exp_vol, err_relative, err_absolute)
        assert isclose(da_pot, exp_pot, err_relative, err_absolute)

    @pytest.mark.parametrize('file, exp_vol, exp_pot',
                             [(data['file'], data['da_volume'], data['da_potential']) for data in list(DATA.values())])
    def test_da_display(self, file, exp_vol, exp_pot):
        """Test isotherm display."""
        if exp_vol is None:
            return

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        pygaps.da_plot(isotherm, verbose=True)
