"""
Test enth_sorp_whittaker module
"""

import numpy as np
import pytest

import pygaps.characterisation.enth_sorp_whittaker as we
import pygaps.modelling as pgm
import pygaps.parsing as pgp

from .conftest import DATA_WHITTAKER

loading = np.linspace(0.1, 20, 100)


@pytest.mark.characterisation
class TestWhittakerEnthalpy():

    @pytest.mark.parametrize('testdata', DATA_WHITTAKER.values())
    def test_whittaker_point(self, testdata, data_whittaker_path):
        """Whittaker method with PointIsotherm"""
        isotherm = pgp.isotherm_from_aif(data_whittaker_path / testdata['file'])
        local_loading = [1]
        res = we.enthalpy_sorption_whittaker(isotherm, model="Toth", loading=local_loading)
        res_enth = res['enthalpy_sorption']
        ref_enth = testdata['ref_enth']
        assert np.isclose(res_enth, ref_enth, rtol=0.1, atol=0.01)

    @pytest.mark.parametrize('testdata', DATA_WHITTAKER.values())
    def test_whittaker_model(self, testdata, data_whittaker_path):
        """Whittaker method with ModelIsotherm."""
        isotherm = pgp.isotherm_from_aif(data_whittaker_path / testdata['file'])
        isotherm.convert_pressure(mode_to="absolute", unit_to="Pa")
        model_isotherm = pgm.model_iso(
            isotherm,
            branch='ads',
            model='Toth',
            verbose=True,
        )
        local_loading = [1]
        res = we.enthalpy_sorption_whittaker(model_isotherm, loading=local_loading)
        res_enth = res['enthalpy_sorption']
        ref_enth = testdata['ref_enth']
        assert np.isclose(res_enth, ref_enth, rtol=0.1, atol=0.01)

    @pytest.mark.parametrize('testdata', DATA_WHITTAKER.values())
    def test_whittaker_fullrange(self, testdata, data_whittaker_path):
        """Whittaker method over a full loading range."""
        isotherm = pgp.isotherm_from_aif(data_whittaker_path / testdata['file'])
        isotherm.convert_pressure(mode_to="absolute", unit_to="Pa")

        model_isotherms = {}
        for model in pgm._WHITTAKER_MODELS:
            model_isotherm = pgm.model_iso(
                isotherm,
                branch='ads',
                model=model,
                verbose=True,
            )
            model_isotherms[model] = model_isotherm

        with pytest.raises(KeyError):
            we.enthalpy_sorption_whittaker(
                isotherm=model_isotherms['Henry'],
                loading=loading
            )

        for model in pgm._WHITTAKER_MODELS:
            we.enthalpy_sorption_whittaker(
                isotherm=model_isotherms[model],
                loading=loading
            )
