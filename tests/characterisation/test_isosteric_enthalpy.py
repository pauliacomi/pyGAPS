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
from matplotlib.testing.decorators import cleanup
from numpy import average
from numpy import isclose

import pygaps
import pygaps.characterisation.isosteric_enthalpy as ie
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_ISOSTERIC
from .conftest import DATA_ISOSTERIC_PATH


@pytest.mark.characterisation
class TestIsostericEnthalpy():
    """Tests isosteric enthalpy calculations."""
    def test_iso_enthalpy_checks(self, use_material):
        """Checks for built-in safeguards."""
        isotherms = []

        # load test data
        for sample in DATA_ISOSTERIC:
            filepath = DATA_ISOSTERIC_PATH / DATA_ISOSTERIC[sample]['file']
            isotherm = pygaps.isotherm_from_json(filepath)
            isotherms.append(isotherm)

        # Will raise a "requires more than one isotherm error"
        with pytest.raises(pgEx.ParameterError):
            ie.isosteric_enthalpy([isotherms[0]])

        # Will raise a "requires isotherms on the same material error"
        isotherms[0].material = 'Test'
        with pytest.raises(pgEx.ParameterError):
            ie.isosteric_enthalpy(isotherms)
        isotherms[0].material = isotherms[1].material

        # Will raise a "requires isotherm on the same basis error"
        isotherms[0].convert_material(basis_to='volume', unit_to='cm3')
        with pytest.raises(pgEx.ParameterError):
            ie.isosteric_enthalpy(isotherms)

    def test_iso_enthalpy(self):
        """Test calculation with several model isotherms."""
        isotherms = []

        for sample in DATA_ISOSTERIC:
            filepath = DATA_ISOSTERIC_PATH / DATA_ISOSTERIC[sample]['file']
            isotherm = pygaps.isotherm_from_json(filepath)
            isotherms.append(isotherm)

        result_dict = ie.isosteric_enthalpy(isotherms)

        assert isclose(average(result_dict['isosteric_enthalpy']), 29, 0.5)

    @cleanup
    def test_iso_enthalpy_output(self):
        """Test verbosity."""
        isotherms = []

        for sample in DATA_ISOSTERIC:
            filepath = DATA_ISOSTERIC_PATH / DATA_ISOSTERIC[sample]['file']
            isotherm = pygaps.isotherm_from_json(filepath)
            isotherms.append(isotherm)

        ie.isosteric_enthalpy(isotherms, verbose=True)
