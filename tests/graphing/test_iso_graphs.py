"""
Tests for the isotherm graphs
"""

import pygaps
import pytest


@pytest.mark.slowtest
class TestIsothermGraphs(object):

    def test_checks(self, basic_pointisotherm, basic_adsorbate):

        pygaps.ADSORBATE_LIST.append(basic_adsorbate)

        pygaps.plot_iso([basic_pointisotherm])

        pygaps.plot_iso([basic_pointisotherm], logx=True)

        pygaps.plot_iso([basic_pointisotherm], color=False)

        pygaps.plot_iso([basic_pointisotherm], branch=['des'])

        pygaps.plot_iso([basic_pointisotherm], unit_pressure='Pa')

        pygaps.plot_iso([basic_pointisotherm], unit_loading='mol')

        pygaps.plot_iso([basic_pointisotherm], mode_pressure='relative')

        pygaps.plot_iso([basic_pointisotherm],
                        fig_title='Testing figure title')

        pygaps.plot_iso([basic_pointisotherm], x_range=(0, 4))

        pygaps.plot_iso([basic_pointisotherm], y1_range=(3, 6))

        pygaps.plot_iso([basic_pointisotherm], legend_list=[
                        'sample_name', 'sample_batch', 'adsorbate', 't_exp'])

        pygaps.plot_iso(
            [basic_pointisotherm, basic_pointisotherm, basic_pointisotherm],
            legend_bottom=False)

        pygaps.plot_iso([basic_pointisotherm],
                        plot_type='property', secondary_key='enthalpy')

        pygaps.plot_iso([basic_pointisotherm],
                        plot_type='combo', secondary_key='enthalpy')

        return
