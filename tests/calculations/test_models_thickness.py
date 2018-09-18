"""
This test module has tests relating to thickness model validations
"""

import numpy
import pytest

import pygaps.calculations.models_thickness as mt
from pygaps.utilities.exceptions import ParameterError


@pytest.mark.characterisation
class TestThicknessModels(object):
    """
    Tests the thickness models
    """

    @pytest.mark.parametrize('model, pressure, thickness', [
        (mt._THICKNESS_MODELS['Halsey'],
         [0.1, 0.4, 0.9], [0.46, 0.62, 1.28]),
        (mt._THICKNESS_MODELS['Harkins/Jura'],
         [0.1, 0.4, 0.9], [0.37, 0.57, 1.32]),
    ])
    def test_static_models(self, model, pressure, thickness):

        for index, value in enumerate(pressure):
            assert numpy.isclose(model(value), thickness[index], 0.01, 0.01)

    def test_thickness_error(self):
        "Tests main errors"
        with pytest.raises(ParameterError):
            mt.get_thickness_model('bad_model')

    def test_thickness_callable(self):
        "Tests the callable method"

        def call_this():
            return 'called'

        ret = mt.get_thickness_model(call_this)

        assert ret() == 'called'
