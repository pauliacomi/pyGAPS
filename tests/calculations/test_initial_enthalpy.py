"""
This test module has tests relating to initial enthalpy of adsorption
"""

import os

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps

from .conftest import DATA_CALO
from .conftest import DATA_CALO_PATH


@pytest.mark.characterisation
class TestInitialEnthalpy(object):
    """
    Tests all initial enthalpy methods
    """

    @cleanup
    @pytest.mark.parametrize('file, expected',
                             [(data['file'], data['ienth']) for data in list(DATA_CALO.values())])
    def test_ienthalpy_comb(self, file, expected):
        "The combined polynomial method"

        filepath = os.path.join(DATA_CALO_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(text_file.read())

        ienth_poly = pygaps.initial_enthalpy_comp(
            isotherm, 'enthalpy', verbose=True).get('initial_enthalpy')

        err_relative = 0.1  # 10 percent
        err_absolute = 1   #

        assert isclose(ienth_poly, expected, err_relative, err_absolute)

    @pytest.mark.parametrize('file, expected',
                             [(data['file'], data['ienth']) for data in list(DATA_CALO.values())])
    def test_ienthalpy_point(self, file, expected):
        "The point method"

        filepath = os.path.join(DATA_CALO_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(text_file.read())

        ienth_poly = pygaps.initial_enthalpy_point(
            isotherm, 'enthalpy', verbose=True).get('initial_enthalpy')

        err_relative = 0.1  # 10 percent
        err_absolute = 1   #

        assert isclose(ienth_poly, expected, err_relative, err_absolute)
