import numpy as np
import pytest

import pygaps.prediction.enthalpy_to_isotherm as eti
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH
from .conftest import DATA_ETI


@pytest.mark.prediction
class TestETI():
    """Test functions in enthalpy_to_isotherm"""

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_eti_checks(self, testdata):
        """Test that exceptions are raised"""
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / testdata['file'])

        # Raises 'no enthalpy error'
        with pytest.raises(pgEx.ParameterError):
            eti.from_whittaker_and_isotherm(300, isotherm)

        # Raises 'incomplete isosteric enthalpy dictionary'
        for necessary_key in ['loading', 'enthalpy']:
            isosteric_enthalpy_dictionary = {necessary_key: [], }
            with pytest.raises(pgEx.ParameterError):
                eti.from_whittaker_and_isotherm(
                    300, isotherm,
                    isosteric_enthalpy_dictionary,
                )

        # Raises 'vectors are different lengths'
        with pytest.raises(pgEx.ParameterError):
            loading = isotherm.loading()
            enthalpy = [1 for n in loading[:-1]]
            isosteric_enthalpy_dictionary = {
                'loading': loading,
                'enthalpy': enthalpy
            }
            eti.from_whittaker_and_isotherm(
                300, isotherm,
                isosteric_enthalpy_dictionary
            )

        # Raises 'feature doesn't exist yet'
        with pytest.raises(pgEx.ParameterError):
            eti.predict_adsorption_heatmap(isotherm, branch=None)

        pressure = np.linspace(1, 1000, 5)
        enthalpy = [1 for n in pressure]

        # Raises 'vectors different length'
        with pytest.raises(pgEx.ParameterError):
            eti.predict_pressure_raw(298, 300, enthalpy[:-1], pressure)

        # Warns about temperature difference > 50 K
        with pytest.warns():
            eti.predict_pressure_raw(298, 398, enthalpy, pressure)

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_ETI.values()])
    def test_predict_pressure_raw(self, testdata):
        """Predict single pressure point"""
        dat = testdata['predict_presssure_raw_single_point']
        res_pressure = eti.predict_pressure_raw(
            dat['T_experiment'], dat['T_predict'],
            dat['enthalpy'], dat['P_experiment']
        )
        ref_pressure = dat['P_predict']
        assert np.isclose(res_pressure, ref_pressure)

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_isotherm_prediction_calculation(self, testdata):
        """
        Check if predicting at original temperature returns same isotherm
        """
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / testdata['file'])
        loading = isotherm.loading(branch='ads')
        enthalpy = [abs(np.random.randn()) for n in loading]
        isosteric_enthalpy_dictionary = {
            'loading': loading,
            'enthalpy': enthalpy,
        }
        predicted_isotherm = eti.from_whittaker_and_isotherm(
            T_predict=isotherm.temperature,
            original_isotherm=isotherm,
            isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
        )
        for p_original, p_predict in zip(
            isotherm.pressure(),
            predicted_isotherm.pressure()
        ):
            assert np.isclose(p_original, p_predict)
