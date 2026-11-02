import numpy as np
import pytest

import pygaps
import pygaps.parsing as pgp
import pygaps.prediction.enthalpy_to_isotherm as eti
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_ETI
from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH


@pytest.mark.prediction
@pytest.mark.parametrize('enthalpy_key', ['isosteric_enthalpy', 'enthalpy_sorption'])
def test_prediction_dictionary_native_units_and_branch(enthalpy_key):
    isotherm = pygaps.PointIsotherm(
        pressure=[1, 2, 3, 2, 1],
        loading=[1, 2, 3, 2.5, 1.5],
        branch=[0, 0, 0, 1, 1],
        material='prediction-test',
        adsorbate='nitrogen',
        temperature=300,
        pressure_mode='absolute',
        pressure_unit='bar',
        loading_basis='molar',
        loading_unit='mol',
        material_basis='mass',
        material_unit='g',
    )
    predicted = eti.predict_isotherm_from_enthalpy_clapeyron(
        isotherm,
        300,
        {'loading': [1.5, 2.5], enthalpy_key: [20, 20]},
        branch='des',
    )
    np.testing.assert_allclose(predicted.pressure(), [1e5, 2e5])
    np.testing.assert_allclose(predicted.loading(), [1500, 2500])
    assert predicted.has_branch('des')
    np.testing.assert_allclose(isotherm.loading(branch='des'), [2.5, 1.5])


@pytest.mark.prediction
def test_prediction_accepts_clapeyron_result():
    from pygaps.characterisation import enthalpy_sorption_clapeyron

    isotherms = [
        pygaps.PointIsotherm(
            pressure=np.array([1.0, 2.0, 3.0]) * np.exp(20000 / 8.314462618 * (1 / 300 - 1 / temperature)),
            loading=[1.0, 2.0, 3.0],
            branch='ads',
            material='prediction-test',
            adsorbate='nitrogen',
            temperature=temperature,
            pressure_mode='absolute',
            pressure_unit='bar',
            loading_basis='molar',
            loading_unit='mmol',
            material_basis='mass',
            material_unit='g',
        )
        for temperature in (300, 310)
    ]
    result = enthalpy_sorption_clapeyron(isotherms, loading_points=[1.0, 2.0, 3.0])
    predicted = eti.predict_isotherm_from_enthalpy_clapeyron(isotherms[0], 310, result)
    np.testing.assert_allclose(predicted.pressure(), isotherms[1].pressure(pressure_unit='Pa'), rtol=1e-7)


@pytest.mark.prediction
def test_prediction_rejects_conflicting_enthalpy_aliases(basic_pointisotherm):
    with pytest.raises(pgEx.ParameterError, match='conflicting enthalpy'):
        eti.predict_isotherm_from_enthalpy_clapeyron(
            pygaps.PointIsotherm.from_isotherm(basic_pointisotherm, pressure=[1, 2, 3], loading=[1, 2, 3]),
            basic_pointisotherm.temperature,
            {'loading': [1, 2, 3], 'isosteric_enthalpy': [20, 20, 20], 'enthalpy_sorption': [21, 21, 21]},
        )


@pytest.mark.prediction
def test_prediction_embedded_enthalpy_uses_selected_branch(isotherm_parameters, isotherm_data):
    isotherm = pygaps.PointIsotherm(isotherm_data=isotherm_data, loading_key='loading', pressure_key='pressure', **isotherm_parameters)
    predicted = eti.predict_isotherm_from_enthalpy_clapeyron(isotherm, isotherm.temperature, branch='des')
    np.testing.assert_allclose(predicted.loading(), isotherm.loading(branch='des'))
    np.testing.assert_allclose(predicted.pressure(), isotherm.pressure(branch='des', pressure_unit='Pa'))


@pytest.mark.prediction
@pytest.mark.parametrize('branch', ['ads', 'des'])
def test_isosurface_interpolates_selected_branch(branch):
    isotherm = pygaps.PointIsotherm(
        pressure=[1, 2, 3, 2, 1],
        loading=[1, 2, 3, 2.5, 1.5],
        branch=[0, 0, 0, 1, 1],
        material='prediction-test',
        adsorbate='nitrogen',
        temperature=300,
        pressure_mode='absolute',
        pressure_unit='bar',
        loading_basis='molar',
        loading_unit='mmol',
        material_basis='mass',
        material_unit='g',
    )
    temperatures = np.array([300, 301])
    pressures = np.array([1.4e5, 1.8e5])
    grid = eti.predict_isosurface_from_enthalpy_clapeyron(
        isotherm,
        temperatures_prediction=temperatures,
        pressures_prediction=pressures,
        isosteric_enthalpy_dictionary={
            'loading': isotherm.loading(branch=branch),
            'isosteric_enthalpy': [20] * len(isotherm.loading(branch=branch)),
        },
        branch=branch,
        verbose=False,
    )

    pressure_factors = np.exp(20000 / eti.R * (1 / 300 - 1 / temperatures))
    expected = pressures[None, :] / (1e5 * pressure_factors[:, None])
    if branch == 'des':
        expected += 0.5
    np.testing.assert_allclose(grid.to_numpy(), expected)
    np.testing.assert_array_equal(grid.index, temperatures)
    np.testing.assert_array_equal(grid.columns, pressures)


@pytest.mark.prediction
def test_isosurface_accepts_native_units_and_celsius():
    isotherm = pygaps.PointIsotherm(
        pressure=[1, 2, 3],
        loading=[1, 2, 3],
        branch='ads',
        material='prediction-test',
        adsorbate='nitrogen',
        temperature=26.85,
        temperature_unit='\u00b0C',
        pressure_mode='absolute',
        pressure_unit='bar',
        loading_basis='molar',
        loading_unit='mol',
        material_basis='mass',
        material_unit='g',
    )
    grid = eti.predict_isosurface_from_enthalpy_clapeyron(
        isotherm,
        temperatures_prediction=[300],
        pressures_prediction=[1e5, 2e5, 3e5],
        isosteric_enthalpy_dictionary={'loading': [1, 2, 3], 'isosteric_enthalpy': [20, 20, 20]},
        verbose=False,
    )
    assert grid.shape == (1, 3)
    assert grid.loc[300, 2e5] == pytest.approx(2000)
    assert isotherm.temperature == pytest.approx(300)
    assert isotherm.temperature_unit == '\u00b0C'
    assert isotherm.to_dict()['temperature'] == pytest.approx(26.85)


@pytest.mark.prediction
class TestETI:
    """Test functions in enthalpy_to_isotherm"""

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_eti_checks(self, testdata):
        """Test that exceptions are raised"""
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / testdata['file'])

        # Raises 'no enthalpy error'
        with pytest.raises(pgEx.ParameterError):
            eti.predict_isotherm_from_enthalpy_clapeyron(isotherm=isotherm, temperature_prediction=300)

        # Raises 'incomplete isosteric enthalpy dictionary'
        for necessary_key in ['loading', 'isosteric_enthalpy']:
            isosteric_enthalpy_dictionary = {
                necessary_key: [],
            }
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
            isosteric_enthalpy_dictionary = {'loading': loading, 'isosteric_enthalpy': enthalpy}
            eti.predict_isotherm_from_enthalpy_clapeyron(
                isotherm=isotherm,
                temperature_prediction=300,
                isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary,
            )

        # Raises 'feature doesn't exist yet'
        with pytest.raises(pgEx.ParameterError):
            loading = isotherm.loading()
            enthalpy = [1 for n in loading]
            isosteric_enthalpy_dictionary = {'loading': loading, 'isosteric_enthalpy': enthalpy}
            eti.predict_isosurface_from_enthalpy_clapeyron(
                isotherm=isotherm, isosteric_enthalpy_dictionary=isosteric_enthalpy_dictionary, branch=None
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
            pressure_current=testdata['P_experiment'],
        )
        ref_pressure = testdata['P_predict']
        assert np.isclose(res_pressure, ref_pressure)

    @pytest.mark.parametrize('testdata', [ex for ex in DATA_WHITTAKER.values()])
    def test_isotherm_prediction_calculation(self, testdata):
        """
        Check if predicting at original temperature returns same isotherm
        """
        isotherm = pgp.isotherm_from_aif(DATA_WHITTAKER_PATH / testdata['file'])
        isotherm.convert_pressure(unit_to='Pa')
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
        for p_original, p_predict in zip(isotherm.pressure(), predicted_isotherm.pressure()):
            assert np.isclose(p_original, p_predict)
