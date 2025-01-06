# TODO Remove after this program no longer support Python 3.8.*
from __future__ import annotations

import numpy as np
import pytest

import pygaps.parsing as pgp
import pygaps.prediction.enthalpy_to_isotherm as eti
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_ETI
from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH


@pytest.mark.prediction
class TestETI():
    """Test functions in enthalpy_to_isotherm"""

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_eti_checks(self, testdata):
        """Test that exceptions are raised"""
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / testdata['file'])

        # Raises 'no enthalpy error'
        with pytest.raises(pgEx.ParameterError):
            eti.predict_isotherm_from_enthalpy_clapeyron(
                isotherm=isotherm, temperature_prediction=300
            )

        # Raises 'incomplete isosteric enthalpy dictionary'
        for necessary_key in ['loading', 'isosteric_enthalpy']:
            isosteric_enthalpy_dictionary = {necessary_key: [], }
            with pytest.raises(pgEx.ParameterError):
                eti.predict_isotherm_from_enthalpy_clapeyron(
                    isotherm=isotherm,
                    temperature_prediction=300,
                    isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
                )

        # Raises 'vectors are different lengths'
        with pytest.raises(pgEx.ParameterError):
            loading = isotherm.loading()
            enthalpy = [1 for n in loading[:-1]]
            isosteric_enthalpy_dictionary = {
                'loading': loading,
                'isosteric_enthalpy': enthalpy
            }
            eti.predict_isotherm_from_enthalpy_clapeyron(
                isotherm=isotherm,
                temperature_prediction=300,
                isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
            )

        # Raises 'feature doesn't exist yet'
        with pytest.raises(pgEx.ParameterError):
            loading = isotherm.loading()
            enthalpy = [1 for n in loading]
            isosteric_enthalpy_dictionary = {
                'loading': loading,
                'isosteric_enthalpy': enthalpy
            }
            eti.predict_isosurface_from_enthalpy_clapeyron(
                isotherm=isotherm,
                isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
                branch=None
            )

        pressure = np.linspace(1, 1000, 5)
        enthalpy = [1 for n in pressure]

        # Raises 'vectors different length'
        with pytest.raises(pgEx.ParameterError):
            eti.predict_pressure_raw(
                isosteric_enthalpy=enthalpy[:-1],
                temperature_prediction=298,
                temperature_current=300,
                pressure_current=pressure,
            )

        # Warns about temperature difference > 50 K
        with pytest.warns():
            assert eti.predict_pressure_raw(
                isosteric_enthalpy=enthalpy,
                temperature_prediction=298,
                temperature_current=398,
                pressure_current=pressure,
            )

    @pytest.mark.parametrize('testdata', list(DATA_ETI.values()))
    def test_predict_pressure_raw(self, testdata):
        """Predict single pressure point"""
        # dat = testdata['predict_presssure_raw_single_point']
        res_pressure = eti.predict_pressure_raw(
            isosteric_enthalpy=testdata['enthalpy'],
            temperature_prediction=testdata['T_predict'],
            temperature_current=testdata['T_experiment'],
            pressure_current=testdata['P_experiment']
        )
        ref_pressure = testdata['P_predict']
        assert np.isclose(res_pressure, ref_pressure)

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_isotherm_prediction_calculation(self, testdata):
        """
        Check if predicting at original temperature returns same isotherm
        """
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / testdata['file'])
        loading = list(isotherm.loading(branch='ads'))
        enthalpy = [abs(np.random.randn()) for n in loading]
        isosteric_enthalpy_dictionary = {
            'loading': loading,
            'enthalpy_sorption': enthalpy,
        }
        predicted_isotherm = eti.predict_isotherm_from_enthalpy_clapeyron(
            isotherm=isotherm,
            temperature_prediction=isotherm.temperature,
            isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
        )
        for p_original, p_predict in zip(
            isotherm.pressure(),
            predicted_isotherm.pressure()
        ):
            assert np.isclose(p_original, p_predict)
