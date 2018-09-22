"""
This test module has tests relating to isosteric heat calculations
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import average
from numpy import isclose

import pygaps

from .conftest import DATA_ISOSTERIC
from .conftest import DATA_ISOSTERIC_PATH


@pytest.mark.characterisation
class TestIsostericHeat(object):
    """
    Tests everything related to isosteric heat calculation
    """

    def test_iso_heat_checks(self, use_sample):
        """Tests initial checks"""

        isotherms = []

        # load test data
        for temp in DATA_ISOSTERIC:

            filepath = os.path.join(
                DATA_ISOSTERIC_PATH, DATA_ISOSTERIC.get(temp)['file'])

            with open(filepath, 'r') as text_file:
                isotherm = pygaps.isotherm_from_json(
                    text_file.read())

            isotherms.append(isotherm)

        # Check multiple isotherms
        with pytest.raises(pygaps.ParameterError):
            pygaps.isosteric_heat([isotherms[0]])

        # Check same sample
        isotherms[0].sample_name = 'Test'

        with pytest.raises(pygaps.ParameterError):
            pygaps.isosteric_heat(isotherms)

        isotherms[0].sample_name = isotherms[1].sample_name

        # Check same basis
        isotherms[0].convert_adsorbent(basis_to='volume', unit_to='cm3')

        with pytest.raises(pygaps.ParameterError):
            pygaps.isosteric_heat(isotherms)

        return

    def test_iso_heat(self):
        """Tests calculation"""

        isotherms = []

        # load test data
        for temp in DATA_ISOSTERIC:

            filepath = os.path.join(
                DATA_ISOSTERIC_PATH, DATA_ISOSTERIC.get(temp)['file'])

            with open(filepath, 'r') as text_file:
                isotherm = pygaps.isotherm_from_json(
                    text_file.read())

            isotherms.append(isotherm)

        result_dict = pygaps.isosteric_heat(isotherms, verbose=False)

        assert isclose(average(result_dict['isosteric_heat']), 29, 3)

        return

    @cleanup
    def test_iso_heat_output(self):
        """Test verbosity"""

        isotherms = []

        # load test data
        for temp in DATA_ISOSTERIC:

            filepath = os.path.join(
                DATA_ISOSTERIC_PATH, DATA_ISOSTERIC.get(temp)['file'])

            with open(filepath, 'r') as text_file:
                isotherm = pygaps.isotherm_from_json(
                    text_file.read())

            isotherms.append(isotherm)

        pygaps.isosteric_heat(isotherms, verbose=True)

        return
