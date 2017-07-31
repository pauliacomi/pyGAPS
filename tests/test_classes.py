"""
This test module has tests relating to module classes
"""

import pandas
import pytest

import adsutils


@pytest.fixture(scope="class")
def basic_isotherm():
    """
    Creates an isotherm from model data
    """

    pressure_key = "Pressure"
    loading_key = "Loading"
    enthalpy_key = "Enthalpy"

    df = pandas.DataFrame({
        pressure_key: [1, 2, 3, 4, 5, 6, 4, 2],
        loading_key: [1, 2, 3, 4, 5, 6, 4, 2],
        enthalpy_key: [5, 5, 5, 5, 5, 5, 5, 5],
    })

    info = {"id": 0,
            "is_real": "True",
            "exp_type": "Calorimetry",
            "date": "",
            "name": "TEST",
            "batch": "TB",
            "t_act": 100,
            "t_exp": 100,
            "machine": "M1",
            "gas": "N2",
            "user": "TU",
            "lab": "TL",
            "project": "TP",
            "comment": ""
            }

    isotherm = adsutils.PointIsotherm(
        df, info, loading_key=loading_key, pressure_key=pressure_key, enthalpy_key=enthalpy_key)

    return isotherm


@pytest.mark.usefixtures('basic_isotherm')
class test_pointisotherm:
    def test1(self):
        basic_isotherm.print_info()
