"""Tests IAST graphs."""

import pytest
from matplotlib.testing.decorators import cleanup

import pygaps.graphing.iast_graphs as graphing


@pytest.mark.graphing
class TestIASTGraphs():
    """Test all IAST graphs."""
    @cleanup
    def test_svp_graph(self):
        """Test svp graph."""

        pressure = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        selectivity = [0.5, 0.5, 0.6, 0.6, 0.7, 0.8, 1.0]
        fraction = 0.3

        graphing.plot_iast_svp(
            pressure, selectivity, 'CO2', 'CH4', fraction, 'bar'
        )

    @cleanup
    def test_vle_graph(self):
        """Test vle graph."""

        x_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        y_data = [0.1, 0.3, 0.4, 0.5, 0.6, 0.7, 0.7]
        pressure = 2

        graphing.plot_iast_vle(x_data, y_data, 'CO2', 'CH4', pressure, 'bar')
