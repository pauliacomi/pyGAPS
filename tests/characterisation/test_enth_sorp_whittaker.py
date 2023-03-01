import pytest

import numpy as np

import pygaps.characterisation.enth_sorp_whittaker as we
import pygaps.parsing as pgp
import pygaps.modelling as pgm
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH

loading = np.linspace(0.1, 20, 100)
ref_enth = 10.382283558571492


@pytest.mark.characterisation
class TestWhittakerEnthalpy():
    def test_whittaker(self):
        isotherm = pgp.isotherm_from_aif(
            DATA_WHITTAKER_PATH / [ex['file'] for ex in DATA_WHITTAKER.values()][0]
        )
        model_isotherm = pgm.model_iso(
            isotherm,
            branch='ads',
            model='Toth',
            verbose=True,
        )
        loading = [1]
        res = we.whittaker_enthalpy(model_isotherm, loading)
        res_enth = res['enthalpy_sorption']
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
            we.whittaker_enthalpy(model_isotherms['Henry'], loading)

        we.whittaker_enthalpy(model_isotherms['Langmuir'], loading)
        we.whittaker_enthalpy(model_isotherms['Toth'], loading)
