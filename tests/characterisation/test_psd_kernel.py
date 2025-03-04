"""
This test module has tests relating to DFT fitting for pore size calculations.

All functions in /calculations/psd_dft.py are tested here.
The purposes are:

    - testing the user-facing API function (psd_dft)
    - testing individual low level functions against known results.

Functions are tested against pre-calculated values on real isotherms.
It is difficult to store full pore size distributions, therefore the
cumulative pore volume as determined by each method is checked
versus stored values.
All pre-calculated data for characterisation can be found in the
/.conftest file together with the other isotherm parameters.
"""

import numpy as np
import pytest

import pygaps.characterisation.psd_kernel as psdk
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from ..test_utils import mpl_cleanup
from .conftest import DATA


@pytest.mark.characterisation
class TestPSDKernel():
    """Test pore size distribution calculation."""

    def test_psd_dft_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""
        # Will raise a "no kernel exception"
        with pytest.raises(pgEx.ParameterError):
            psdk.psd_dft(basic_pointisotherm, kernel=None)

        # Will raise a "no applicable branch exception"
        with pytest.raises(pgEx.ParameterError):
            psdk.psd_dft(basic_pointisotherm, branch='test')

    @pytest.mark.parametrize('kernel', [
        'DFT-N2-77K-carbon-slit',
    ])
    @pytest.mark.parametrize('sample', DATA.values())
    def test_psd_dft(self, sample, kernel, data_char_path):
        """Test psd calculation with several model isotherms"""
        # exclude datasets where it is not applicable
        if 'psd_dft_pore_volume' not in sample:
            return

        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)

        result_dict = psdk.psd_dft(isotherm, kernel=kernel)

        loc = np.where(result_dict['pore_distribution'] == max(result_dict['pore_distribution']))
        principal_peak = result_dict['pore_widths'][loc]

        err_relative = 0.05  # 5 percent
        err_absolute = 0.01  # 0.01

        assert np.isclose(principal_peak, sample['psd_micro_pore_size'], err_relative, err_absolute)

    @mpl_cleanup
    def test_psd_dft_verbose(self, data_char_path):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = data_char_path / sample['file']
        isotherm = pgp.isotherm_from_json(filepath)
        psdk.psd_dft(isotherm, verbose=True)
