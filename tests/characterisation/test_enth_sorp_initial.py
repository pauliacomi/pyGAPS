"""
Tests relating to initial enthalpy of adsorption calculations.

All functions in /calculations/initial_enthalpy.py are tested here.
The purposes are:

    - testing the user-facing API function (initial_enthalpy_x)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import pytest
from numpy import isclose

import pygaps.characterisation.enth_sorp_initial as ie
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA_CALO


@pytest.mark.characterisation
class TestInitialEnthalpyPoint():
    """Test point initial enthalpy methods."""

    def test_ienthalpy_point_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "can't find enthalpy column error"
        with pytest.raises(pgEx.ParameterError):
            ie.initial_enthalpy_point(basic_pointisotherm, 'wrong')

    @pytest.mark.parametrize('sample', DATA_CALO.values())
    def test_ienthalpy_point(self, sample, data_calo_path):
        """The point method."""
        filepath = data_calo_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        ienth_poly = ie.initial_enthalpy_point(isotherm, 'enthalpy').get('initial_enthalpy')

        err_relative = 0.1  # 10 percent
        err_absolute = 1  #

        assert isclose(ienth_poly, sample['ienth'], err_relative, err_absolute)

    @mpl_cleanup
    def test_ienthalpy_point_output(self, data_calo_path):
        """Test verbosity."""
        sample = DATA_CALO['Takeda 5A']
        filepath = data_calo_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        ie.initial_enthalpy_point(isotherm, 'enthalpy', verbose=True)


@pytest.mark.characterisation
class TestInitialEnthalpyFit():
    """Test fitting initial enthalpy methods."""

    def test_ienthalpy_comp_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "can't find enthalpy column error"
        with pytest.raises(pgEx.ParameterError):
            ie.initial_enthalpy_comp(basic_pointisotherm, 'wrong')

    @pytest.mark.parametrize('sample', DATA_CALO.values())
    def test_ienthalpy_comb(self, sample, data_calo_path):
        """The combined polynomial method"""
        filepath = data_calo_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        ienth_poly = ie.initial_enthalpy_comp(isotherm, 'enthalpy').get('initial_enthalpy')

        err_relative = 0.1  # 10 percent
        err_absolute = 1  #

        assert isclose(ienth_poly, sample['ienth'], err_relative, err_absolute)

    @mpl_cleanup
    def test_ienthalpy_comb_output(self, data_calo_path):
        """Test verbosity."""
        sample = DATA_CALO['Takeda 5A']
        filepath = data_calo_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        ie.initial_enthalpy_comp(isotherm, 'enthalpy', verbose=True)
