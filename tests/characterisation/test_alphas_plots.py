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
from numpy import isclose

import pygaps
import pygaps.characterisation.alphas_plots as als
import pygaps.parsing.json as pgpj
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestAlphaSPlot():
    """Test alpha-s calculation."""

    def test_alphas_checks(self, use_adsorbate, basic_pointisotherm):
        """Checks for built-in safeguards."""

        # Will raise a "no reference isotherm" error
        with pytest.raises(pgEx.ParameterError):
            als.alpha_s(basic_pointisotherm, None)

        # Will raise a "no reference isotherm" error
        with pytest.raises(pgEx.ParameterError):
            als.alpha_s(basic_pointisotherm, 'isotherm')

        # Will raise a "adsorbate not the same" error
        ref_iso = pygaps.PointIsotherm(
            pressure=[0, 1],
            loading=[0, 1],
            material='test',
            adsorbate='argon',
            temperature=87,
        )
        with pytest.raises(pgEx.ParameterError):
            als.alpha_s(basic_pointisotherm, ref_iso)

        # Will raise a "bad reducing pressure" error
        with pytest.raises(pgEx.ParameterError):
            als.alpha_s(basic_pointisotherm, basic_pointisotherm, reducing_pressure=1.3)

        # Will raise a "bad reference_area value" error
        with pytest.raises(pgEx.ParameterError):
            als.alpha_s(basic_pointisotherm, basic_pointisotherm, reference_area='some')

    @pytest.mark.parametrize('sample', DATA.values())
    def test_alphas(self, sample, data_char_path):
        """Test calculation with several model isotherms."""
        # exclude datasets where it is not applicable
        if 'as_area' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        ref_filepath = data_char_path / DATA[sample['as_ref']]['file']
        ref_isotherm = pgpj.isotherm_from_json(ref_filepath)
        mref_isotherm = pygaps.ModelIsotherm.from_pointisotherm(ref_isotherm, model='BET')

        res = als.alpha_s(isotherm, mref_isotherm)
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(
            results[-1].get('adsorbed_volume'),
            sample['as_volume'],
            err_relative,
            err_absolute_area,
        )
        assert isclose(
            results[0].get('area'),
            sample['as_area'],
            err_relative,
            err_absolute_volume,
        )

    def test_alphas_choice(self, data_char_path):
        """Test choice of points."""

        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)

        res = als.alpha_s(isotherm, isotherm, t_limits=[0.7, 1.0])
        results = res.get('results')

        err_relative = 0.1  # 10 percent
        err_absolute_area = 0.1  # units
        err_absolute_volume = 0.01  # units

        assert isclose(results[-1].get('adsorbed_volume'), 0, err_relative, err_absolute_area)
        assert isclose(
            results[-1].get('area'), sample['s_as_area'], err_relative, err_absolute_volume
        )

    @mpl_cleanup
    def test_alphas_output(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgpj.isotherm_from_json(filepath)
        als.alpha_s(isotherm, isotherm, verbose=True)
