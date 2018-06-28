"""
Tests for the isotherm graphs
"""

import pytest
from matplotlib.testing.decorators import cleanup

import pygaps


@pytest.mark.slowtest
class TestIsothermGraphs(object):
    """Tests regular isotherm graphs"""

    @cleanup
    def test_checks(self, basic_pointisotherm, basic_adsorbate):

        pygaps.ADSORBATE_LIST.append(basic_adsorbate)

        pygaps.plot_iso(basic_pointisotherm)
        pygaps.plot_iso(basic_pointisotherm, logx=True)
        pygaps.plot_iso(basic_pointisotherm, color=False)
        pygaps.plot_iso(basic_pointisotherm, branch=['des'])
        pygaps.plot_iso(basic_pointisotherm, unit_pressure='Pa')
        pygaps.plot_iso(basic_pointisotherm, unit_loading='mol')
        pygaps.plot_iso(basic_pointisotherm, mode_pressure='relative')
        pygaps.plot_iso(basic_pointisotherm,
                        fig_title='Testing figure title')
        pygaps.plot_iso(basic_pointisotherm, x_range=(0, 4))
        pygaps.plot_iso(basic_pointisotherm, x_range=(0, None))
        pygaps.plot_iso(basic_pointisotherm, y1_range=(3, None))
        pygaps.plot_iso(basic_pointisotherm, y1_range=(3, None))
        pygaps.plot_iso(basic_pointisotherm, legend_list=[
                        'sample_name', 'sample_batch', 'adsorbate', 't_exp'])

        pygaps.plot_iso(
            [basic_pointisotherm, basic_pointisotherm, basic_pointisotherm],
            legend_bottom=False)

        pygaps.plot_iso(basic_pointisotherm,
                        plot_type='property', secondary_key='enthalpy')
        pygaps.plot_iso(basic_pointisotherm,
                        plot_type='combined', secondary_key='enthalpy')
        pygaps.plot_iso(basic_pointisotherm, line_style=dict(linewidth=5))

        return
