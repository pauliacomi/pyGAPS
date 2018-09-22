"""
This test module has tests relating to Horvath-Kawazoe models
"""

import pytest

import pygaps.calculations.models_hk as hk
from pygaps.utilities.exceptions import ParameterError


@pytest.mark.characterisation
class TestHKModels(object):
    """
    Tests the HK models
    """

    def test_hk_model_string(self):
        "Just gets stored models"
        for model in hk._ADSORBENT_MODELS:
            assert hk.get_hk_model(model) == hk._ADSORBENT_MODELS[model]

        with pytest.raises(ParameterError):
            hk.get_hk_model('bad_model')

    def test_hk_model_dict(self):
        "Passes a dict model"

        model_dict = dict(
            molecular_diameter=0.276,            # nm
            polarizability=2.5E-30,            # m3
            magnetic_susceptibility=1.3E-34,   # m3
            surface_density=1.315E19,           # molecules/m2
        )

        assert hk.get_hk_model(model_dict) == model_dict

        model_dict.pop('molecular_diameter')

        with pytest.raises(ParameterError):
            hk.get_hk_model(model_dict)

    def test_hk_model_error(self):
        "Error when nothing is passed"
        with pytest.raises(ParameterError):
            hk.get_hk_model(None)
