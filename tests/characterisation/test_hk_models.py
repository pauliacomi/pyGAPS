"""
Tests relating to Horvath-Kawazoe model validation.

All functions in /calculations/models_hk.py are tested here.
The purposes are:

    - testing that the "function getter" is performing as expected.

"""

import pytest

import pygaps.characterisation.models_hk as hk
import pygaps.utilities.exceptions as pgEx


@pytest.mark.characterisation
class TestHKModels():
    """Tests the HK models."""
    def test_get_hk_model_string(self):
        """Just gets stored models."""
        for model in hk._ADSORBENT_MODELS:
            assert hk.get_hk_model(model) == hk._ADSORBENT_MODELS[model]

    def test_get_hk_model_error(self):
        """Check if errors are raised."""
        with pytest.raises(pgEx.ParameterError):
            hk.get_hk_model('bad_model')

    def test_get_hk_model_dict(self):
        """When passing a dict, we check for consistency and return the same dict."""
        model_dict = dict(
            molecular_diameter=0.276,  # nm
            polarizability=2.5E-3,  # nm3
            magnetic_susceptibility=1.3E-7,  # nm3
            surface_density=1.315E19,  # molecules/m2
        )

        assert hk.get_hk_model(model_dict) == model_dict

        # dictionary parameters should be checked
        model_dict.pop('molecular_diameter')

        with pytest.raises(pgEx.ParameterError):
            hk.get_hk_model(model_dict)
