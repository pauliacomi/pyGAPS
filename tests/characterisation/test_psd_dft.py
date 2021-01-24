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
from matplotlib.testing.decorators import cleanup

import pygaps
import pygaps.characterisation.psd_dft as pdft
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA
from .conftest import DATA_N77_PATH


@pytest.mark.characterisation
class TestPSDDFT():
    """Test pore size distribution calculation."""
    def test_psd_dft_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""
        # Will raise a "no kernel exception"
        with pytest.raises(pgEx.ParameterError):
            pdft.psd_dft(basic_pointisotherm, kernel=None)

        # Will raise a "no applicable branch exception"
        with pytest.raises(pgEx.ParameterError):
            pdft.psd_dft(basic_pointisotherm, branch='test')

    @pytest.mark.parametrize('kernel', [
        'DFT-N2-77K-carbon-slit',
    ])
    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_psd_dft(self, sample, kernel):
        """Test psd calculation with several model isotherms"""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('psd_dft_pore_volume', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            result_dict = pdft.psd_dft(isotherm, kernel=kernel)

            loc = np.where(
                result_dict['pore_distribution'] ==
                max(result_dict['pore_distribution'])
            )
            principal_peak = result_dict['pore_widths'][loc]

            err_relative = 0.05  # 5 percent
            err_absolute = 0.01  # 0.01

            assert np.isclose(
                principal_peak, sample['psd_micro_pore_size'], err_relative,
                err_absolute
            )

    @cleanup
    def test_psd_dft_verbose(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.psd_dft(isotherm, verbose=True)
