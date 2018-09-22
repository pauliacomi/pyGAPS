# %%
import numpy
import pytest

import pygaps


@pytest.mark.core
class TestConversions(object):

    @pytest.mark.parametrize('value, basis_from, basis_to, unit_from, unit_to',
                             [
                                 (1, 'mass', 'mass', 'g', 'g'),
                                 (0.001, 'mass', 'mass', 'g', 'kg'),
                                 (217.078, 'mass', 'volume', 'g', 'cm3'),
                                 (0.0357, 'mass', 'molar', 'g', 'mol'),
                                 (35.7, 'mass', 'molar', 'g', 'mmol'),

                                 (1000, 'molar', 'molar', 'mol', 'mmol'),
                                 (28.01, 'molar', 'mass', 'mol', 'g'),
                                 (6081.12, 'molar', 'volume', 'mol', 'cm3'),

                                 (1e-6, 'volume', 'volume', 'cm3', 'm3'),
                                 (4.606E-3, 'volume', 'mass', 'cm3', 'g'),
                                 (6081.12, 'volume', 'molar', 'cm3', 'mol'),
                             ])
    def test_convert_loading(self, value, basis_from, basis_to,
                             unit_from, unit_to, use_adsorbate):

        result = pygaps.utilities.unit_converter.c_loading(
            1,
            basis_from=basis_from, basis_to=basis_to,
            unit_from=unit_from, unit_to=unit_to,
            adsorbate_name='TA', temp=77.344,
        )

        assert numpy.isclose(result, value, 0.01, 0.01)

    @pytest.mark.parametrize('value, basis_from, basis_to, unit_from, unit_to',
                             [
                                 (1, 'mass', 'mass', 'g', 'g'),
                                 (1000, 'mass', 'mass', 'g', 'kg'),
                                 (10, 'mass', 'volume', 'g', 'cm3'),
                                 (10, 'mass', 'molar', 'g', 'mol'),
                                 (0.01, 'mass', 'molar', 'g', 'mmol'),

                                 (0.001, 'molar', 'molar', 'mol', 'mmol'),
                                 (0.1, 'molar', 'mass', 'mol', 'g'),
                                 (1, 'molar', 'volume', 'mol', 'cm3'),

                                 (1e6, 'volume', 'volume', 'cm3', 'm3'),
                                 (0.1, 'volume', 'mass', 'cm3', 'g'),
                                 (1, 'volume', 'molar', 'cm3', 'mol'),
                             ])
    def test_convert_adsorbent(self, value, basis_from, basis_to,
                               unit_from, unit_to, use_sample):

        result = pygaps.utilities.unit_converter.c_adsorbent(
            1,
            basis_from=basis_from, basis_to=basis_to,
            unit_from=unit_from, unit_to=unit_to,
            sample_name='TEST', sample_batch='TB'
        )

        assert numpy.isclose(result, value, 0.01, 0.01)

    @pytest.mark.parametrize('value, mode_from, mode_to, unit_from, unit_to',
                             [
                                 (1, 'absolute', 'absolute', 'bar', 'bar'),
                                 (100000, 'absolute', 'absolute', 'bar', 'Pa'),
                                 (0.97, 'absolute', 'absolute', 'bar', 'atm'),
                                 (1, 'absolute', 'relative', 'bar', 'bar'),
                                 (1, 'relative', 'relative', 'bar', 'Pa'),
                                 (101193.756, 'relative', 'absolute', 'bar', 'Pa'),
                                 (101193.756, 'relative', 'absolute', 'Pa', 'Pa'),
                             ])
    def test_convert_pressure(self, value, mode_from, mode_to, unit_from, unit_to):

        result = pygaps.utilities.unit_converter.c_pressure(
            1,
            mode_from=mode_from, mode_to=mode_to,
            unit_from=unit_from, unit_to=unit_to,
            adsorbate_name='N2', temp=77.344
        )

        assert numpy.isclose(result, value, 0.01, 0.01)
