"""
This test module has tests relating to the adsorbate class
"""

import os

import pandas
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps

from ..calculations.conftest import DATA
from ..calculations.conftest import DATA_PATH


class TestModelIsotherm(object):
    """
    Tests the pointisotherm class
    """

    def test_isotherm_create(self):
        "Checks isotherm can be created from basic data"
        isotherm_param = {
            'sample_name': 'carbon',
            'sample_batch': 'X1',
            'adsorbate': 'nitrogen',
            't_exp': 77,
        }

        isotherm_data = pandas.DataFrame({
            'pressure': [1, 2, 3, 4, 5, 3, 2],
            'loading': [1, 2, 3, 4, 5, 3, 2]
        })

        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            model='Henry',
            param_guess=None,
            optimization_method="Nelder-Mead",
            **isotherm_param
        )

        return isotherm

    @pytest.mark.parametrize('file, ',
                             [(data['file']) for data in list(DATA.values())])
    def test_isotherm_create_pointiso(self, file):
        "Checks isotherm can be created from a pointisotherm"

        filepath = os.path.join(DATA_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.PointIsotherm.from_json(
                text_file.read())

        isotherm = pygaps.ModelIsotherm.from_pointisotherm(
            isotherm, guess_model=True)

    @cleanup
    def test_isotherm_print_parameters(self, basic_pointisotherm):
        "Checks isotherm can print its own info"

        isotherm = pygaps.ModelIsotherm.from_pointisotherm(
            basic_pointisotherm, guess_model=True)

        isotherm.print_info(show=False)
