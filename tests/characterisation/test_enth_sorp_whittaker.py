import numpy as np
import pytest

import pygaps.characterisation.enth_sorp_whittaker as we
import pygaps.modelling as pgm
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH

loading = np.linspace(0.1, 20, 100)


@pytest.mark.characterisation
class TestWhittakerEnthalpy():
    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_whittaker(self, testdata):
        isotherm = pgp.isotherm_from_aif(
            DATA_WHITTAKER_PATH / testdata['file']
        )
        model_isotherm = pgm.model_iso(
            isotherm,
            branch='ads',
            model='Toth',
            verbose=True,
        )
        loading = [1]
        res = we.enthalpy_sorption_whittaker(model_isotherm, loading)
        res_enth = res['enthalpy_sorption']
        ref_enth  = testdata['ref_enth']
        assert np.isclose(res_enth, ref_enth)

    @pytest.mark.parametrize('filepath', [ex['file'] for ex in DATA_WHITTAKER.values()])
    def test_whittaker_full(self, filepath):
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / filepath)

        model_isotherms = {}
        for model in ['Henry', 'Langmuir', 'Toth']:
            model_isotherm = pgm.model_iso(
                isotherm,
                branch='ads',
                model=model,
                verbose=True,
            )
            model_isotherms[model] = model_isotherm

        with pytest.raises(pgEx.ParameterError):
            we.enthalpy_sorption_whittaker(model_isotherms['Henry'], loading)

        we.enthalpy_sorption_whittaker(model_isotherms['Langmuir'], loading)
        we.enthalpy_sorption_whittaker(model_isotherms['Toth'], loading)
