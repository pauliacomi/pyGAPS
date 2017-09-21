"""
This test module has tests relating to the adsorbate class
"""

import os

import pytest

import pygaps

from ..calculations.conftest import DATA
from ..calculations.conftest import DATA_PATH


class TestModelIsotherm(object):
    """
    Tests the pointisotherm class
    """

    @pytest.mark.parametrize('file, ',
                             [(data['file']) for data in list(DATA.values())])
    def test_isotherm_create(self, file):
        "Checks isotherm can be created from test data"

        filepath = os.path.join(DATA_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.PointIsotherm.from_json(
                text_file.read())

        pygaps.ModelIsotherm.from_pointisotherm(isotherm, guess_model=True)
