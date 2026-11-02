"""
This test module has tests relating to BET area calculation.

All functions in /calculations/area_bet.py are tested here.
The purposes are:

    - testing the user-facing API function (area_BET)
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
from numpy import maximum
from numpy import mean
from numpy import sqrt
from scipy import constants
from scipy import stats

import pygaps
import pygaps.characterisation.area_bet as ab
import pygaps.parsing.json as pgpj
import pygaps.utilities.exceptions as pgEx
from pygaps.utilities.pygaps_utilities import get_iso_loading_and_pressure_ordered
from pygaps.utilities.pygaps_utilities import get_pressure_limit_indices

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestAreaBET:
    """Tests BET surface area calculations."""

    def test_bet_fit_returns_regression_errors(self):
        pressure = array([0.1, 0.2, 0.3, 0.4])
        bet_points = array([1.13, 1.31, 1.58, 1.69])

        slope, intercept, corr_coef, slope_stderr, intercept_stderr = ab.bet_fit(
            pressure, bet_points
        )
        expected = stats.linregress(pressure, bet_points)

        assert isclose(slope, expected.slope)
        assert isclose(intercept, expected.intercept)
        assert isclose(corr_coef, expected.rvalue)
        assert isclose(slope_stderr, expected.stderr)
        assert isclose(intercept_stderr, expected.intercept_stderr)

    def test_basic_functions(self):
        """Test basic functionality."""
        P = linspace(0, 0.9)
        L = linspace(0.3, 10)

        # arrays should be equal
        with pytest.raises(pgEx.ParameterError):
            ab.area_BET_raw({'pressure': P[1:], 'loading': L, 'cross_section': 1})

        # should not take less than 3 points
        with pytest.raises(pgEx.CalculationError):
            ab.area_BET_raw(
                {'pressure': P[:2], 'loading': L[:2], 'cross_section': 1, 'p_limits': [-1, 10]}
            )

        # 3 will work
        result = ab.area_BET_raw(
            {'pressure': P[:3], 'loading': L[:3], 'cross_section': 1, 'p_limits': [-1, 10]}
        )
        assert isinstance(result, dict)
        assert {'area', 'bet_slope', 'bet_intercept', 'area_stderr'} <= result.keys()

        # Basic automatic limit test (using rouquerol)
        ab.area_BET_raw({'pressure': P, 'loading': L, 'cross_section': 1})

    @pytest.mark.parametrize(
        ('pressure', 'loading', 'cross_section', 'message'),
        [
            ([[0.1, 0.2, 0.3]], [0.01, 0.02, 0.03], 0.1, 'one-dimensional'),
            ([0.1, float('nan'), 0.3], [0.01, 0.02, 0.03], 0.1, 'finite'),
            ([0.1, 0.2, 0.3], [0.01, float('nan'), 0.03], 0.1, 'finite'),
            ([0.1, -0.2, 0.3], [0.01, 0.02, 0.03], 0.1, 'greater than or equal'),
            ([0.1, 0.2, 1.0], [0.01, 0.02, 0.03], 0.1, 'less than 1'),
            ([0.1, 0.2, 0.3], [0.01, -0.02, 0.03], 0.1, 'non-negative'),
            ([0.1, 0.3, 0.2], [0.01, 0.02, 0.03], 0.1, 'ascending'),
            ([0.1, 0.2, 0.3], [0.01, 0.02, 0.03], 0, 'positive finite'),
            ([0.1, 0.2, 0.3], [0.01, 0.02, 0.03], float('inf'), 'positive finite'),
        ],
    )
    def test_invalid_input_values_raise_parameter_error(
        self, pressure, loading, cross_section, message
    ):
        with pytest.raises(pgEx.ParameterError, match=message):
            ab.area_BET_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': cross_section,
                    'p_limits': (0.0, 0.99),
                }
            )

    def test_zero_loading_is_allowed_outside_selected_range(self):
        pressure = array([0.0, 0.1, 0.2, 0.3, 0.4])
        loading = array([0.0, 0.01, 0.018, 0.024, 0.028])

        result = ab.area_BET_raw(
            {
                'pressure': pressure,
                'loading': loading,
                'cross_section': 0.1,
                'p_limits': (0.1, 0.4),
            }
        )

        assert result['p_limit_indices'] == (1, 4)
        assert result['area'] > 0

    def test_zero_loading_in_selected_range_raises_parameter_error(self):
        with pytest.raises(pgEx.ParameterError, match='Loading must be positive'):
            ab.area_BET_raw(
                {
                    'pressure': [0.0, 0.1, 0.2, 0.3],
                    'loading': [0.0, 0.01, 0.02, 0.03],
                    'cross_section': 0.1,
                    'p_limits': (0.0, 0.3),
                }
            )

    def test_nonfinite_bet_transform_raises_calculation_error(self):
        with pytest.raises(pgEx.CalculationError, match='BET transform contains non-finite'):
            ab.area_BET_raw(
                {
                    'pressure': [0.1, 0.2, 0.3],
                    'loading': [1e-320, 2e-320, 3e-320],
                    'cross_section': 0.1,
                    'p_limits': (0.1, 0.3),
                }
            )

    def test_nonfinite_bet_fit_raises_calculation_error(self):
        with pytest.raises(pgEx.CalculationError, match='BET fit contains non-finite'):
            ab.area_BET_raw(
                {
                    'pressure': [0.1, 0.2, 0.3],
                    'loading': [1e-309, 2e-309, 3e-309],
                    'cross_section': 0.1,
                    'p_limits': (0.1, 0.3),
                }
            )

    def test_repeated_selected_pressures_without_variation_raise_calculation_error(self):
        with pytest.raises(pgEx.CalculationError, match='two distinct pressure values'):
            ab.area_BET_raw(
                {
                    'pressure': [0.1, 0.1, 0.1],
                    'loading': [0.01, 0.02, 0.03],
                    'cross_section': 0.1,
                    'p_limits': (0.1, 0.1),
                }
            )

    def test_limit_selection(self):
        """Selection excludes a decreasing first pair and rebases sliced data."""
        pressure = linspace(0.05, 0.5, 10)
        loading = ab.simple_bet(pressure, 0.02, 10)
        rouquerol = ab.roq_transform(pressure, loading)
        loading[0] = rouquerol[1] * 1.1 / (1 - pressure[0])

        full = ab.area_BET_raw(
            {'pressure': pressure, 'loading': loading, 'cross_section': 0.1}
        )
        suffix = ab.area_BET_raw(
            {'pressure': pressure[1:], 'loading': loading[1:], 'cross_section': 0.1}
        )

        assert full['p_limit_indices'] == (1, 9)
        assert suffix['p_limit_indices'] == (0, 8)

    @pytest.mark.parametrize('roq_change', ['decrease', 'plateau'])
    def test_automatic_limits_stop_before_nonincreasing_rouquerol_values(self, roq_change):
        """Do not include the first decreasing or repeated Rouquerol value."""
        pressure = linspace(0.05, 0.5, 10)
        loading = ab.simple_bet(pressure, 0.02, 10)
        roq_values = ab.roq_transform(pressure, loading)
        roq_values[6] = (
            roq_values[5] * 0.9 if roq_change == 'decrease' else roq_values[5]
        )
        loading = roq_values / (1 - pressure)

        result = ab.area_BET_raw(
            {'pressure': pressure, 'loading': loading, 'cross_section': 0.1}
        )

        assert result['p_limit_indices'] == (0, 5)

    def test_automatic_selection_uses_longest_valid_window(self):
        pressure = linspace(0.05, 0.5, 10)
        loading = ab.simple_bet(pressure, 0.02, 10)

        result = ab.area_BET_raw(
            {'pressure': pressure, 'loading': loading, 'cross_section': 0.1}
        )

        assert result['p_limit_indices'] == (0, 9)
        assert result['c_const'] > 0
        assert loading[0] < result['n_monolayer'] < loading[-1]
        assert pressure[0] <= result['p_monolayer'] <= pressure[-1]

    def test_automatic_selection_fails_without_valid_window(self):
        pressure = linspace(0.5, 0.8, 8)
        loading = ab.simple_bet(pressure, 0.02, 10)

        with pytest.raises(pgEx.CalculationError, match='No pressure range satisfies'):
            ab.area_BET_raw(
                {'pressure': pressure, 'loading': loading, 'cross_section': 0.1}
            )

    def test_explicit_limits_include_upper_endpoint(self):
        """Both pressure limits include observations exactly on their bounds."""
        pressure = array([0.1, 0.2, 0.3, 0.4])
        loading = ab.simple_bet(pressure, 0.02, 10)

        result = ab.area_BET_raw(
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

    def test_zero_pressure_limit_is_not_treated_as_unspecified(self):
        pressure = array([-0.1, 0.0, 0.1, 0.2])

        assert get_pressure_limit_indices(pressure, (0, 0.1)) == (1, 2)

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
            ab.area_BET_raw(
                {
                    'pressure': [0.1, 0.2, 0.3],
                    'loading': [0.01, 0.02, 0.03],
                    'cross_section': 0.1,
                    'p_limits': p_limits,
                }
            )

    def test_missing_required_input_raises_parameter_error(self):
        with pytest.raises(pgEx.ParameterError, match='cross_section'):
            ab.area_BET_raw({'pressure': [0.1], 'loading': [0.01]})

    def test_raw_input_must_be_a_dictionary(self):
        with pytest.raises(pgEx.ParameterError, match='dictionary'):
            ab.area_BET_raw([0.1, 0.2, 0.3])

    def test_monolayer_pressure_outside_selected_region_warns(self, caplog):
        pressure = linspace(0.5, 0.8, 8)
        loading = ab.simple_bet(pressure, 0.02, 10)

        with caplog.at_level(logging.WARNING):
            ab.area_BET_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': 0.1,
                    'p_limits': (0.5, 0.8),
                }
            )

        assert "The monolayer pressure is not within the BET region." in caplog.messages

    def test_monolayer_pressure_within_selected_region_does_not_warn(self, caplog):
        pressure = linspace(0.1, 0.4, 8)
        loading = ab.simple_bet(pressure, 0.02, 10)

        with caplog.at_level(logging.WARNING):
            result = ab.area_BET_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': 0.1,
                    'p_limits': (0.1, 0.4),
                }
            )

        assert pressure[0] <= result['p_monolayer'] <= pressure[-1]
        assert "The monolayer pressure is not within the BET region." not in caplog.messages

    @pytest.mark.parametrize(
        ('parameter_index', 'invalid_value', 'warning'),
        [
            (2, 0, "The C constant is not positive and finite."),
            (0, float('nan'), "The monolayer loading is not positive and finite."),
            (1, float('inf'), "The monolayer pressure is not positive and finite."),
            (3, -1, "The BET area is not positive and finite."),
        ],
    )
    def test_invalid_bet_parameters_warn(self, monkeypatch, caplog, parameter_index, invalid_value, warning):
        parameters = [0.02, 0.2, 10, 1.0]
        parameters[parameter_index] = invalid_value
        monkeypatch.setattr(ab, 'bet_parameters', lambda *_: tuple(parameters))
        pressure = linspace(0.1, 0.4, 8)
        loading = ab.simple_bet(pressure, 0.02, 10)

        with caplog.at_level(logging.WARNING):
            ab.area_BET_raw(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'cross_section': 0.1,
                    'p_limits': (0.1, 0.4),
                }
            )

        assert warning in caplog.messages

    @pytest.mark.parametrize('sample', DATA.values())
    def test_area_bet(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'bet_area' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        result = ab.area_BET(isotherm)
        area = result.get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['bet_area'], err_relative, err_absolute)
        assert isfinite(result['area_stderr'])
        assert result['area_stderr'] >= 0
        assert isfinite(result['bet_slope_stderr'])
        assert isfinite(result['bet_intercept_stderr'])
        cross_section = pygaps.Adsorbate.find(isotherm.adsorbate).get_prop('cross_sectional_area')
        pressure, loading = get_iso_loading_and_pressure_ordered(
            isotherm,
            'ads',
            {'loading_basis': 'molar', 'loading_unit': 'mol'},
            {'pressure_mode': 'relative'},
        )
        minimum, max_idx = result['p_limit_indices']
        fit_pressure = pressure[minimum : max_idx + 1]
        fit_loading = loading[minimum : max_idx + 1]
        fit = stats.linregress(fit_pressure, ab.bet_transform(fit_pressure, fit_loading))
        covariance = -mean(fit_pressure) * fit.stderr**2
        monolayer_variance = result['n_monolayer']**4 * (
            fit.stderr**2 + fit.intercept_stderr**2 + 2 * covariance
        )
        expected_area_stderr = (
            cross_section
            * 1e-18
            * constants.Avogadro
            * sqrt(maximum(monolayer_variance, 0))
        )
        assert isclose(result['bet_slope_stderr'], fit.stderr)
        assert isclose(result['bet_intercept_stderr'], fit.intercept_stderr)
        assert isclose(result['area_stderr'], expected_area_stderr)
        assert isclose(
            result['area'],
            result['n_monolayer'] * cross_section * 1e-18 * constants.Avogadro,
        )

    def test_area_BET_choice(self, data_char_path):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        area = ab.area_BET(isotherm, p_limits=[0.05, 0.30]).get("area")

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2

        assert isclose(area, sample['bet_area_s'], err_relative, err_absolute)

    def test_area_BET_branch(self, data_char_path, caplog):
        """Test branch to use."""

        sample = DATA['SiO2']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        with caplog.at_level(logging.WARNING):  # warns about the monolayer value
            area = ab.area_BET(isotherm, branch="des", p_limits=(0.05, 0.4)).get("area")
        assert caplog.records

        err_relative = 0.1  # 10 percent
        err_absolute = 0.1  # 0.1 m2
        assert isclose(area, sample['bet_area_des'], err_relative, err_absolute)

    @mpl_cleanup
    def test_area_BET_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        ab.area_BET(isotherm, verbose=True)
