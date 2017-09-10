"""
This test module has tests relating to the adsorbate class
"""

import pytest

import pygaps


class TestModelIsotherm(object):
    """
    Tests the pointisotherm class
    """

    @pytest.mark.xfail
    @pytest.mark.parametrize('model, data', [
        ("Langmuir", [3.0, 6.0, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        ("Quadratic", [3.0, 6.0, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        ("Henry", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0]),
        ("TemkinApprox", [3.0, 6.0, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        ("DSLangmuir", [3.0, 5.5, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        # ("TSLangmuir", [3.2, 5.4, 6.8, 7.8, 8.5, 9.0, 0, 0]),
        # ("BET", [3.2, 5.4, 6.8, 7.8, 8.5, 9.0, 0, 0]),
    ])
    def test_isotherm_create(self, isotherm_data, basic_isotherm, model, data):
        "Checks isotherm can be created from test data"

        loading_key = 'loading'
        pressure_key = 'presure'
        isotherm_data['loading'] = data

        pygaps.ModelIsotherm.from_isotherm(
            basic_isotherm,
            isotherm_data[:6],
            loading_key,
            pressure_key,
            model)
