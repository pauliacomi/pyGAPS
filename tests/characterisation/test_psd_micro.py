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

import numpy as np
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps
import pygaps.characterisation.psd_microporous as pmic
import pygaps.utilities.exceptions as pgEx
from pygaps.characterisation.models_hk import PROPERTIES_CARBON

from .conftest import DATA
from .conftest import DATA_N77_PATH

N2_PROPS = {
    'molecular_diameter': 0.3,
    'polarizability': 0.0017403,
    'magnetic_susceptibility': 3.6e-08,
    'surface_density': 6.71e+18,
    'liquid_density': 0.8076937566133804,
    'adsorbate_molar_mass': 28.01348
}


@pytest.mark.characterisation
class TestPSDMicro():
    """Test pore size distribution calculation."""
    def test_psd_micro_checks(self, basic_pointisotherm):
        """Checks for built-in safeguards."""
        # Will raise a "no model exception"
        with pytest.raises(pgEx.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, psd_model=None)

        # Will raise a "no suitable model exception"
        with pytest.raises(pgEx.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, psd_model='Test')

        # Will raise a "no applicable geometry exception"
        with pytest.raises(pgEx.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, pore_geometry='test')

        # Will raise a "no applicable branch exception"
        with pytest.raises(pgEx.ParameterError):
            pmic.psd_microporous(basic_pointisotherm, branch='test')

    def test_psd_micro_funcs(self):
        """Checks various functions from the module"""

        assert np.isclose(pmic._N_over_RT(77), 9.40645E+20)

        km_ads = 1.23E-13
        km_mat = 4.91E-13

        assert np.isclose(pmic._kirkwood_muller_dispersion_ads(1, 1), km_ads)
        assert np.isclose(
            pmic._kirkwood_muller_dispersion_mat(1, 1, 2, 2), km_mat
        )
        {'polarizability': 1, 'magnetic_susceptibility': 1}

        disp_dict = pmic._dispersion_from_dict({
            'polarizability': 1,
            'magnetic_susceptibility': 1
        }, {
            'polarizability': 2,
            'magnetic_susceptibility': 2
        })
        assert np.isclose(disp_dict[0], km_ads)
        assert np.isclose(disp_dict[1], km_mat)

    def test_psd_micro_solvers(self):
        """Check the HK and HK-CY solvers"""

        assert np.isclose(
            pmic._solve_hk([1], lambda x: np.log(x), 0.5, 1)[0], 1
        )

        assert np.isclose(
            pmic._solve_hk_cy([1.463017], np.array([0.5, 1]),
                              lambda x: np.log(x), 0.5, 1)[0], 1, 0.001
        )

    def test_psd_micro_hk(self):
        """Test H-K psd model with blank arrays"""

        x = [0.001, 0.002]
        y = [1, 2]

        pmic.psd_horvath_kawazoe(x, y, 77, 'slit', N2_PROPS, PROPERTIES_CARBON)
        pmic.psd_horvath_kawazoe(
            x, x, 77, 'cylinder', N2_PROPS, PROPERTIES_CARBON
        )
        pmic.psd_horvath_kawazoe(
            x, x, 77, 'sphere', N2_PROPS, PROPERTIES_CARBON
        )
        pmic.psd_horvath_kawazoe(
            x, x, 77, 'slit', N2_PROPS, PROPERTIES_CARBON, use_cy=True
        )

    def test_psd_micro_ry(self):
        """Test H-K psd model with blank arrays"""

        x = [0.001, 0.002]
        y = [1, 2]

        pmic.psd_horvath_kawazoe_ry(
            x, y, 77, 'slit', N2_PROPS, PROPERTIES_CARBON
        )
        pmic.psd_horvath_kawazoe_ry(
            x, x, 77, 'cylinder', N2_PROPS, PROPERTIES_CARBON
        )

        pmic.psd_horvath_kawazoe_ry(
            x, x, 77, 'sphere', N2_PROPS, PROPERTIES_CARBON
        )

        pmic.psd_horvath_kawazoe_ry(
            x, x, 77, 'slit', N2_PROPS, PROPERTIES_CARBON, use_cy=True
        )

    @pytest.mark.parametrize('sample', [sample for sample in DATA])
    def test_psd_micro(self, sample):
        """Test psd calculation with several model isotherms"""
        sample = DATA[sample]
        # exclude datasets where it is not applicable
        if sample.get('psd_micro_pore_size', None):

            filepath = DATA_N77_PATH / sample['file']
            isotherm = pygaps.isotherm_from_json(filepath)

            result_dict = pmic.psd_microporous(
                isotherm, psd_model='HK', pore_geometry='slit'
            )

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
    def test_psd_micro_verbose(self):
        """Test verbosity."""
        sample = DATA['MCM-41']
        filepath = DATA_N77_PATH / sample['file']
        isotherm = pygaps.isotherm_from_json(filepath)
        pygaps.psd_microporous(isotherm, verbose=True)
