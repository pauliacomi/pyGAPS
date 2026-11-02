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
        P = linspace(0, 1)
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

    def test_limit_selection(self):
        """Test the automatic selection of limits."""

        P = [0.001, 0.004, 0.009, 0.015, 0.025, 0.042, 0.093, 0.124, 0.156, 0.186]
        L = [118, 135, 146, 155, 170, 172, 189, 195, 200, 203]

        # Enough points here
        ab.area_BET_raw({'pressure': P, 'loading': L, 'cross_section': 1})

        # Not enough points here
        with pytest.raises(pgEx.CalculationError):
            ab.area_BET_raw({'pressure': P[4:], 'loading': L[4:], 'cross_section': 1})

    @pytest.mark.parametrize(
        ('roq_values', 'expected_maximum'),
        [
            ([0.10, 0.20, 0.30, 0.25, 0.20], 2),
            ([0.10, 0.20, 0.30, 0.30, 0.35], 2),
        ],
    )
    def test_automatic_limits_stop_before_nonincreasing_rouquerol_values(
        self, roq_values, expected_maximum
    ):
        """Do not include the first decreasing or repeated Rouquerol value."""
        pressure = linspace(0.01, 0.05, len(roq_values))
        loading = roq_values / (1 - pressure)

        result = ab.area_BET_raw(
            {'pressure': pressure, 'loading': loading, 'cross_section': 0.1}
        )

        assert result['p_limit_indices'][1] == expected_maximum

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
        fit = stats.linregress(fit_pressure, ab.bet_transform(fit_pressure, fit_loading))
        covariance = -mean(fit_pressure) * fit.stderr**2
        monolayer_variance = result['n_monolayer']**4 * (
            fit.stderr**2 + fit.intercept_stderr**2 + 2 * covariance
        )
        expected_area_stderr = (
            result['cross_sectional_area']
            * 1e-18
            * constants.Avogadro
            * sqrt(maximum(monolayer_variance, 0))
        )
        assert isclose(result['bet_slope_stderr'], fit.stderr)
        assert isclose(result['bet_intercept_stderr'], fit.intercept_stderr)
        assert isclose(result['area_stderr'], expected_area_stderr)
        assert isclose(
            result['area'],
            result['n_monolayer'] * result['cross_sectional_area'] * 1e-18 * constants.Avogadro,
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
            area = ab.area_BET(isotherm, branch="des").get("area")
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
