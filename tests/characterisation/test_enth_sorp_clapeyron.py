"""Tests relating to isosteric enthalpy calculations.

All functions in /calculations/isosteric_enthalpy.py are tested here.
The purposes are:

    - testing the user-facing API function (isosteric_enthalpy)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import pytest
from numpy import average
from numpy import isclose

import pygaps.characterisation.enth_sorp_clapeyron as ie
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA_ISOSTERIC


@pytest.mark.characterisation
class TestEnthalpySorptionClapeyron():
    """Tests isosteric enthalpy calculations."""

    def test_iso_enthalpy_checks(self, use_material, data_isosteric_path):
        """Checks for built-in safeguards."""
        isotherms = []

        # load test data
        for sample in DATA_ISOSTERIC.values():
            filepath = data_isosteric_path / sample['file']
            isotherm = pgp.isotherm_from_json(filepath)
            isotherms.append(isotherm)

        # Will raise a "requires more than one isotherm error"
        with pytest.raises(pgEx.ParameterError):
            ie.enthalpy_sorption_clapeyron([isotherms[0]])

        # Will raise a "requires isotherms on the same material error"
        isotherms[0].material = 'Test'
        with pytest.raises(pgEx.ParameterError):
            ie.enthalpy_sorption_clapeyron(isotherms)
        isotherms[0].material = isotherms[1].material

        # Will raise a "requires isotherm on the same basis error"
        isotherms[0].convert_material(basis_to='volume', unit_to='cm3')
        with pytest.raises(pgEx.ParameterError):
            ie.enthalpy_sorption_clapeyron(isotherms)

    def test_iso_enthalpy(self, data_isosteric_path):
        """Test calculation with several model isotherms."""
        isotherms = []

        for sample in DATA_ISOSTERIC.values():
            filepath = data_isosteric_path / sample['file']
            isotherm = pgp.isotherm_from_json(filepath)
            isotherms.append(isotherm)

        result_dict = ie.enthalpy_sorption_clapeyron(isotherms)

        assert isclose(average(result_dict['isosteric_enthalpy']), 29, 0.5)

    @mpl_cleanup
    def test_iso_enthalpy_output(self, data_isosteric_path):
        """Test verbosity."""
        isotherms = []

        for sample in DATA_ISOSTERIC.values():
            filepath = data_isosteric_path / sample['file']
            isotherm = pgp.isotherm_from_json(filepath)
            isotherms.append(isotherm)

        ie.enthalpy_sorption_clapeyron(isotherms, verbose=True)
