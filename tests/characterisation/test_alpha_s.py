"""
This test module has tests relating to alpha-s plots.

All functions in /calculations/alphas.py are tested here.
The purposes are:

    - testing the user-facing API function (alpha_s)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import pytest
from matplotlib.testing.decorators import cleanup
from numpy import isclose

import pygaps
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestAlphaSPlot():
    """Test alpha-s calculation."""
    def test_alphas_checks(self, use_adsorbate, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "no reference isotherm" error
        with pytest.raises(pgEx.ParameterError):
            pygaps.alpha_s(basic_pointisotherm, None)

        # Will raise a "no reference isotherm" error
        with pytest.raises(pgEx.ParameterError):
            pygaps.alpha_s(basic_pointisotherm, 'isotherm')

        # Will raise a "adsorbate not the same" error
        ref_iso = pygaps.PointIsotherm(
            pressure=[0, 1],
            loading=[0, 1],
            material='test',
            adsorbate='argon',
            temperature=87
        )
        with pytest.raises(pgEx.ParameterError):
            pygaps.alpha_s(basic_pointisotherm, ref_iso)

        # Will raise a "bad reducing pressure" error
        with pytest.raises(pgEx.ParameterError):
            pygaps.alpha_s(
                basic_pointisotherm,
                basic_pointisotherm,
                reducing_pressure=1.3
            )

        # Will raise a "bad reference_area value" error
        with pytest.raises(pgEx.ParameterError):
            pygaps.alpha_s(
                basic_pointisotherm,
                basic_pointisotherm,
                reference_area='some'
            )

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_alphas(self, sample):
        """Test calculation with several model isotherms."""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('as_area', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)
            ref_filepath = DATA_N77_PATH / DATA[sample['as_ref']]['file']
            ref_isotherm = pygaps.isotherm_from_json(ref_filepath)
            mref_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
                ref_isotherm, model='BET'
            )

            res = pygaps.alpha_s(isotherm, mref_isotherm)
            results = res.get('results')

            err_relative = 0.1  # 10 percent
            err_absolute_area = 0.1  # units
            err_absolute_volume = 0.01  # units

            assert isclose(
                results[-1].get('adsorbed_volume'), sample['as_volume'],
                err_relative, err_absolute_area
            )
            assert isclose(
                results[0].get('area'), sample['as_area'], err_relative,
                err_absolute_volume
            )

    def test_alphas_choice(self):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)

        res = pygaps.alpha_s(isotherm, isotherm, limits=[0.7, 1.0])
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(
            results[-1].get('adsorbed_volume'), 0, err_relative,
            err_absolute_area
        )
        assert isclose(
            results[-1].get('area'), sample['s_as_area'], err_relative,
            err_absolute_volume
        )

    @cleanup
    def test_alphas_output(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.alpha_s(isotherm, isotherm, verbose=True)
