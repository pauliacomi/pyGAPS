"""
This test module has tests relating to thickness model validations
"""

import pytest
import numpy

from pygaps.calculations.thickness_models import _THICKNESS_MODELS


class TestThicknessModels(object):
    """
    Tests the thickness models
    """

    @pytest.mark.parametrize('model, pressure, thickness', [
        (_THICKNESS_MODELS['Halsey'],
         [0.1, 0.4, 0.9], [0.46, 0.62, 1.28]),
        (_THICKNESS_MODELS['Harkins/Jura'],
         [0.1, 0.4, 0.9], [0.37, 0.57, 1.32]),
    ])
    def test_static_models(self, model, pressure, thickness):

        for index, value in enumerate(pressure):
            assert numpy.isclose(model(value), thickness[index], 0.01, 0.01)
