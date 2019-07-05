"""
This test module has tests relating to micropore pore size calculations.

All functions in /calculations/psd_microporous.py are tested here.
The purposes are:

    - testing the user-facing API function (psd_microporous)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
It is difficult to store full pore size distributions, therefore the
cumulative pore volume as determined by each method is checked
versus stored values.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import os

import numpy as np
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps
import pygaps.characterisation.psd_microporous as pmic

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestPSDMicro():
    """Test pore size distribution calculation."""

    def test_psd_micro_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""
        # Will raise a "no model exception"
        with pytest.raises(pygaps.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, psd_model=None)

        # Will raise a "no suitable model exception"
        with pytest.raises(pygaps.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, psd_model='Test')

        # Will raise a "no applicable geometry exception"
        with pytest.raises(pygaps.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, pore_geometry='test')

        # Will raise a "no applicable branch exception"
        with pytest.raises(pygaps.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, branch='test')

    @pytest.mark.parametrize('method', [
        'HK',
    ])
    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_psd_micro(self, sample, method):
        """Test psd calculation with several model isotherms"""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('psd_micro_pore_size', None):

            filepath = os.path.join(DATA_N77_PATH, sample['file'])
            isotherm = pygaps.isotherm_from_jsonf(filepath)

            result_dict = pmic.psd_microporous(isotherm, psd_model=method)

            loc = np.where(result_dict['pore_distribution'] == max(result_dict['pore_distribution']))
            principal_peak = result_dict['pore_widths'][loc]

            err_relative = 0.05  # 5 percent
            err_absolute = 0.01  # 0.01

            assert np.isclose(
                principal_peak,
                sample['psd_micro_pore_size'],
                err_relative, err_absolute)

    @cleanup
    def test_psd_micro_verbose(self):
        """Test verbosity."""
        data = DATA['MCM-41']
        filepath = os.path.join(DATA_N77_PATH, data['file'])
        isotherm = pygaps.isotherm_from_jsonf(filepath)
        pygaps.psd_microporous(isotherm, verbose=True)
