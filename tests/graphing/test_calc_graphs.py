"""
Tests calculation graphs such as PSD/t_plot/BET etc
"""

import pytest
from matplotlib.testing.decorators import cleanup

import pygaps.graphing.calc_graphs as graphing


@pytest.mark.graphing
class TestCalcGraphs():
    """Tests all calculation graphs"""
    @cleanup
    def test_bet_graph(self):
        """Test BET graph"""

        pressure = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        bet_points = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
        min_p = 2
        max_p = 6
        slope = 0.5
        intercept = 0.01
        mono_p = 0.33
        mono_bet = 0.23

        graphing.bet_plot(
            pressure, bet_points, min_p, max_p, slope, intercept, mono_p,
            mono_bet
        )

    @cleanup
    def test_roq_graph(self):
        """Test Rouquerol graph"""

        pressure = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        roq_points = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
        min_p = 2
        max_p = 6
        slope = 0.5
        intercept = 0.01

        graphing.roq_plot(pressure, roq_points, min_p, max_p, slope, intercept)
