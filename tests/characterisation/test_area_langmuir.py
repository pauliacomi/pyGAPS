"""
This test module has tests relating to Langmuir area calculations.

All functions in /calculations/area_langmuir.py are tested here.
The purposes are:

    - testing the user-facing API function (area_langmuir)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import logging

import pytest
from numpy import array
from numpy import isclose
from numpy import isfinite
from numpy import linspace
from scipy import constants
from scipy import stats

import pygaps.characterisation.area_lang as al
import pygaps.parsing.json as pgpj
import pygaps.utilities.exceptions as pgEx
from pygaps.utilities.pygaps_utilities import get_iso_loading_and_pressure_ordered

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestAreaLangmuir:
    """Tests Langmuir surface area calculations."""

    def test_langmuir_fit_returns_regression_errors(self):
        pressure = array([0.1, 0.2, 0.3, 0.4])
        langmuir_points = array([1.13, 1.31, 1.58, 1.69])

        slope, intercept, corr_coef, slope_stderr, intercept_stderr = al.langmuir_fit(
            pressure, langmuir_points
        )
        expected = stats.linregress(pressure, langmuir_points)

        assert isclose(slope, expected.slope)
        assert isclose(intercept, expected.intercept)
        assert isclose(corr_coef, expected.rvalue)
        assert isclose(slope_stderr, expected.stderr)
        assert isclose(intercept_stderr, expected.intercept_stderr)

    def test_basic_functions(self):
        """Test basic functionality."""
        P = linspace(0, 1)
        L = linspace(0.3, 10)

        # arrays should be equal
        with pytest.raises(pgEx.ParameterError):
            al.area_langmuir_raw({'pressure': P[1:], 'loading': L, 'cross_section': 1})

        # Fewer than 3 points cannot support the regression.
        with pytest.raises(pgEx.CalculationError):
            al.area_langmuir_raw(
                {
                    'pressure': P[:2],
                    'loading': L[:2],
                    'cross_section': 1,
                    'p_limits': [-1, 10],
                }
            )

        # 3 will work
        result = al.area_langmuir_raw(
            {
                'pressure': P[:3],
                'loading': L[:3],
                'cross_section': 1,
                'p_limits': [-1, 10],
            }
        )
        assert isinstance(result, dict)
        assert {'area', 'langmuir_slope', 'langmuir_intercept', 'area_stderr'} <= result.keys()

        # test using autolimits
        al.area_langmuir_raw({'pressure': P, 'loading': L, 'cross_section': 1})

    @pytest.mark.parametrize(
        ('pressure', 'loading', 'cross_section', 'message'),
        [
            ([[0.1, 0.2, 0.3]], [0.01, 0.02, 0.03], 0.1, 'one-dimensional'),
            ([0.1, 0.2, 0.3], [0.01, float('nan'), 0.03], 0.1, 'finite'),
            ([0.1, -0.2, 0.3], [0.01, 0.02, 0.03], 0.1, 'between 0 and 1'),
            ([0.1, 1.1, 0.3], [0.01, 0.02, 0.03], 0.1, 'between 0 and 1'),
            ([0.1, 0.2, 0.3], [0.01, -0.02, 0.03], 0.1, 'non-negative'),
            ([0.1, 0.3, 0.2], [0.01, 0.02, 0.03], 0.1, 'ascending'),
            ([0.1, 0.2, 0.3], [0.01, 0.02, 0.03], 0, 'positive finite'),
            ([0.1, 0.2, 0.3], [0.01, 0.02, 0.03], float('inf'), 'positive finite'),
        ],
    )
    def test_invalid_input_values_raise_parameter_error(self, pressure, loading, cross_section, message):
        with pytest.raises(pgEx.ParameterError, match=message):
            al.area_langmuir_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': cross_section,
                    'p_limits': (0.0, 1.0),
                }
            )

    def test_zero_loading_is_allowed_outside_selected_range(self):
        pressure = array([0.0, 0.1, 0.2, 0.3, 0.4])
        loading = array([0.0, 0.01, 0.018, 0.024, 0.028])

        result = al.area_langmuir_raw({'pressure': pressure, 'loading': loading, 'cross_section': 0.1})

        assert result['p_limit_indices'][0] > 0
        assert result['area'] > 0

    def test_zero_loading_in_selected_range_raises_parameter_error(self):
        with pytest.raises(pgEx.ParameterError, match='Loading must be positive'):
            al.area_langmuir_raw(
                {
                    'pressure': [0.0, 0.1, 0.2, 0.3],
                    'loading': [0.0, 0.01, 0.02, 0.03],
                    'cross_section': 0.1,
                    'p_limits': (0.0, 0.3),
                }
            )

    def test_repeated_selected_pressures_without_variation_raise_calculation_error(self):
        with pytest.raises(pgEx.CalculationError, match='two distinct pressure values'):
            al.area_langmuir_raw(
                {
                    'pressure': [0.1, 0.1, 0.1],
                    'loading': [0.01, 0.02, 0.03],
                    'cross_section': 0.1,
                    'p_limits': (0.1, 0.1),
                }
            )

    def test_explicit_limits_include_upper_endpoint(self):
        """Both pressure limits include observations exactly on their bounds."""
        pressure = array([0.1, 0.2, 0.3, 0.4])
        loading = al.simple_lang(pressure, 0.02, 3)

        result = al.area_langmuir_raw(
            {
                'pressure': pressure,
                'loading': loading,
                'cross_section': 0.1,
                'p_limits': (0.1, 0.3),
            }
        )

        assert result['p_limit_indices'] == (0, 2)
        assert result['area'] > 0
        assert result['area_stderr'] >= 0

    def test_nonpositive_langmuir_parameters_emit_warnings(self, caplog):
        pressure = array([0.0625, 0.125, 0.1875, 0.25])
        transformed = 0.5 - pressure
        loading = pressure / transformed

        with caplog.at_level(logging.WARNING):
            result = al.area_langmuir_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': 0.1,
                    'p_limits': (pressure[0], pressure[-1]),
                }
            )

        assert result['langmuir_const'] < 0
        assert result['n_monolayer'] < 0
        assert result['area'] < 0
        assert "The Langmuir constant is not positive and finite." in caplog.text
        assert "The monolayer loading is not positive and finite." in caplog.text
        assert "The Langmuir area is not positive and finite." in caplog.text

    def test_nonfinite_langmuir_parameters_emit_warnings(self, caplog):
        pressure = array([0.0625, 0.125, 0.1875, 0.25])
        loading = pressure.copy()

        with caplog.at_level(logging.WARNING):
            result = al.area_langmuir_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': 0.1,
                    'p_limits': (pressure[0], pressure[-1]),
                }
            )

        assert result['langmuir_const'] == 0
        assert not isfinite(result['n_monolayer'])
        assert not isfinite(result['area'])
        assert "The Langmuir constant is not positive and finite." in caplog.text
        assert "The monolayer loading is not positive and finite." in caplog.text
        assert "The Langmuir area is not positive and finite." in caplog.text

    def test_nonfinite_langmuir_constant_emits_warning(self, caplog):
        pressure = array([0.0625, 0.125, 0.1875, 0.25])
        loading = array([1.0, 1.0, 1.0, 1.0])

        with caplog.at_level(logging.WARNING):
            result = al.area_langmuir_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': 0.1,
                    'p_limits': (pressure[0], pressure[-1]),
                }
            )

        assert not isfinite(result['langmuir_const'])
        assert "The Langmuir constant is not positive and finite." in caplog.text
        assert "The monolayer loading is not positive and finite." not in caplog.text
        assert "The Langmuir area is not positive and finite." not in caplog.text

    @pytest.mark.parametrize(
        'p_limits',
        [
            (0.3, 0.1),
            (0.1,),
            (0.1, float('nan')),
        ],
    )
    def test_invalid_pressure_limits_raise_parameter_error(self, p_limits):
        with pytest.raises(pgEx.ParameterError):
            al.area_langmuir_raw(
                {
                    'pressure': [0.1, 0.2, 0.3],
                    'loading': [0.01, 0.02, 0.03],
                    'cross_section': 0.1,
                    'p_limits': p_limits,
                }
            )

    def test_missing_required_input_raises_parameter_error(self):
        with pytest.raises(pgEx.ParameterError, match='cross_section'):
            al.area_langmuir_raw({'pressure': [0.1], 'loading': [0.01]})

    def test_raw_input_must_be_a_dictionary(self):
        with pytest.raises(pgEx.ParameterError, match='dictionary'):
            al.area_langmuir_raw([0.1, 0.2, 0.3])

    @pytest.mark.parametrize('sample', DATA.values())
    def test_area_langmuir(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'langmuir_area' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        result = al.area_langmuir(isotherm)
        area = result.get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['langmuir_area'], err_relative, err_absolute)
        assert isfinite(result['area_stderr'])
        assert result['area_stderr'] >= 0
        assert isfinite(result['langmuir_slope_stderr'])
        assert isfinite(result['langmuir_intercept_stderr'])
        assert result['cross_sectional_area'] > 0
        pressure, loading = get_iso_loading_and_pressure_ordered(
            isotherm,
            'ads',
            {'loading_basis': 'molar', 'loading_unit': 'mol'},
            {'pressure_mode': 'relative'},
        )
        minimum, max_idx = result['p_limit_indices']
        fit_pressure = pressure[minimum : max_idx + 1]
        fit_loading = loading[minimum : max_idx + 1]
        fit = stats.linregress(fit_pressure, al.langmuir_transform(fit_pressure, fit_loading))
        expected_area_stderr = (
            result['cross_sectional_area']
            * 1e-18
            * constants.Avogadro
            * result['n_monolayer']**2
            * fit.stderr
        )
        assert isclose(result['langmuir_slope_stderr'], fit.stderr)
        assert isclose(result['langmuir_intercept_stderr'], fit.intercept_stderr)
        assert isclose(result['area_stderr'], expected_area_stderr)
        assert isclose(
            result['area'],
            result['n_monolayer'] * result['cross_sectional_area'] * 1e-18 * constants.Avogadro,
        )

    def test_area_langmuir_choice(self, data_char_path):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = al.area_langmuir(isotherm, p_limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['langmuir_area_s'], err_relative, err_absolute)

    def test_area_langmuir_branch(self, data_char_path):
        """Test branch to use."""

        sample = DATA['Takeda 5A']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = al.area_langmuir(isotherm, branch="des").get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2
        assert isclose(area, sample['langmuir_area'], err_relative, err_absolute)

    @mpl_cleanup
    def test_area_langmuir_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        al.area_langmuir(isotherm, verbose=True)
