"""
Tests for the isotherm graphs
"""

import pytest
from matplotlib.testing.decorators import cleanup

import pygaps


@pytest.mark.graphing
class TestIsothermGraphs():
    """Tests regular isotherm graphs"""
    @cleanup
    def test_basic_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm)

    @cleanup
    def test_multi_plot(self, basic_pointisotherm):
        pygaps.plot_iso([
            basic_pointisotherm, basic_pointisotherm, basic_pointisotherm
        ])

    @cleanup
    def test_data_plot(self, basic_pointisotherm):
        pygaps.plot_iso(
            basic_pointisotherm,
            x_data='pressure',
            y1_data='loading',
            y2_data='enthalpy'
        )
        pygaps.plot_iso(
            basic_pointisotherm, x_data='loading', y1_data='enthalpy'
        )

    @cleanup
    def test_branch_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm, branch='ads', fig_title='ads')
        pygaps.plot_iso(basic_pointisotherm, branch='des', fig_title='des')
        pygaps.plot_iso(basic_pointisotherm, branch='all', fig_title='all')
        pygaps.plot_iso(
            basic_pointisotherm, branch='all-nol', fig_title='all-nol'
        )

    @cleanup
    def test_convert_plot(self, basic_pointisotherm, basic_adsorbate):
        pygaps.ADSORBATE_LIST.append(basic_adsorbate)
        pygaps.plot_iso(basic_pointisotherm, pressure_unit='Pa')
        pygaps.plot_iso(basic_pointisotherm, loading_unit='mol')
        pygaps.plot_iso(basic_pointisotherm, pressure_mode='relative')
        pygaps.ADSORBATE_LIST.remove(basic_adsorbate)

    @cleanup
    def test_range_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm, x_range=(0, 4))
        pygaps.plot_iso(basic_pointisotherm, x_range=(0, None))
        pygaps.plot_iso(basic_pointisotherm, y1_range=(3, None))
        pygaps.plot_iso(basic_pointisotherm, y1_range=(3, None))

    @cleanup
    def test_log_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm, logx=True)

    @cleanup
    def test_color_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm, color=False)
        pygaps.plot_iso(basic_pointisotherm, color=3)
        pygaps.plot_iso(basic_pointisotherm, color=['red'])

    @cleanup
    def test_title_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm, fig_title='Testing figure title')

    @cleanup
    def test_style_plot(self, basic_pointisotherm):
        pygaps.plot_iso(basic_pointisotherm, line_style=dict(linewidth=5))

    @cleanup
    def test_legend_plot(self, basic_pointisotherm):
        pygaps.plot_iso(
            basic_pointisotherm,
            lgd_keys=['material', 'adsorbate', 'temperature']
        )
