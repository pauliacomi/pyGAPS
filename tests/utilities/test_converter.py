"""Tests unit converter."""
import pytest

import pygaps
from pygaps.utilities import converter_mode


@pytest.mark.core
class TestConversions():
    @pytest.mark.parametrize(
        'value, b_f, u_f, b_t, u_t, b_a, u_a',
        [
            (1, 'mass', 'g', 'mass', 'g', None, None),  # 1 g/g -> 1 g/g
            (0.001, 'mass', 'g', 'mass', 'kg', None,
             None),  # 1 g/g -> 0.001 kg/g
            (217.078, 'mass', 'g', 'volume', 'cm3', None,
             None),  # 1 g/g -> 217 cm3/g
            (0.0357, 'mass', 'g', 'molar', 'mol', None,
             None),  # 1 g/g -> 0.0357 mol/g
            (35.7, 'mass', 'g', 'molar', 'mmol', None,
             None),  # 1 g/g -> 35.7 mol/g
            (1000, 'molar', 'mol', 'molar', 'mmol', None,
             None),  # 1 mol/g -> 1 mmol/g
            (28.01, 'molar', 'mol', 'mass', 'g', None,
             None),  # 1 mol/g -> 28.01 g/g
            (6081.12, 'molar', 'mol', 'volume', 'cm3', None,
             None),  # 1 mol/g -> 6081 cm3/g
            (6.08112, 'molar', 'mmol', 'volume', 'cm3', None,
             None),  # 1 mmol/g -> 6.081 cm3/g
            (1e-6, 'volume', 'cm3', 'volume', 'm3', None,
             None),  # 1 cm3/g -> 1E-6 m3/g
            (4.606E-3, 'volume', 'cm3', 'mass', 'g', None,
             None),  # 1 cm3/g -> 4.6e-3 g/g
            (1.6444E-4, 'volume', 'cm3', 'molar', 'mol', None,
             None),  # 1 cm3/g -> 1.6444-4 mol/g
            (1, 'mass', 'g', 'fraction', None, 'mass',
             'g'),  # 1 g/g -> 1 fraction
            (0.001, 'mass', 'mg', 'fraction', None, 'mass',
             'g'),  # 1 mg/g -> 0.001 fraction
            (1000, 'mass', 'g', 'fraction', None, 'mass',
             'mg'),  # 1 g/mg -> 1000 fraction
            (1, 'fraction', None, 'mass', 'g', 'mass',
             'g'),  # 1 fraction -> 1 g/g
            (1000, 'fraction', None, 'mass', 'mg', 'mass',
             'g'),  # 1 fraction -> 1000 mg/g
            (100, 'mass', 'g', 'percent', None, 'mass',
             'g'),  # 1 g/g -> 100 percent
            (0.1, 'mass', 'mg', 'percent', None, 'mass',
             'g'),  # 1 mg/g -> 0.1 percent
            (100000, 'mass', 'g', 'percent', None, 'mass',
             'mg'),  # 1 g/mg -> 100000 percent
            (0.01, 'percent', None, 'mass', 'g', 'mass',
             'g'),  # 1 percent -> 0.01 g/g
            (10, 'percent', None, 'mass', 'mg', 'mass',
             'g'),  # 1 percent -> 10 mg/g
        ]
    )
    def test_convert_loading(
        self, value, b_f, u_f, b_t, u_t, b_a, u_a, use_adsorbate
    ):
        result = converter_mode.c_loading(
            1,
            basis_from=b_f,
            unit_from=u_f,
            basis_to=b_t,
            unit_to=u_t,
            adsorbate=pygaps.Adsorbate.find('N2'),
            temp=77.344,
            basis_material=b_a,
            unit_material=u_a,
        )

        assert result == pytest.approx(value, rel=1e-3)

    @pytest.mark.parametrize(
        'value, b_f, u_f, b_t, u_t',
        [
            (1, 'mass', 'g', 'mass', 'g'),  # 1 g/g -> 1 g/g
            (1000, 'mass', 'g', 'mass', 'kg'),  # 1 g/g -> 1000 g/kg
            (2, 'mass', 'g', 'volume', 'cm3'),  # 1 g/g -> 2 g/cm3
            (10, 'mass', 'g', 'molar', 'mol'),  # 1 g/g -> 10 g/mol
            (0.01, 'mass', 'g', 'molar', 'mmol'),  # 1 g/g -> 0.01 g/mmol
            (0.001, 'molar', 'mol', 'molar',
             'mmol'),  # 1 g/mol -> 0.001 g/mmol
            (0.1, 'molar', 'mol', 'mass', 'g'),  # 1 g/mol -> 0.1 g/g
            (0.2, 'molar', 'mol', 'volume', 'cm3'),  # 1 g/mol -> 0.2 g/cm3
            (1e6, 'volume', 'cm3', 'volume', 'm3'),  # 1 g/cm3 -> 1E6 g/m3
            (0.5, 'volume', 'cm3', 'mass', 'g'),  # 1 g/cm3 -> 0.5 g/g
            (5, 'volume', 'cm3', 'molar', 'mol'),  # 1 g/cm3 -> 5 g/g
        ]
    )
    def test_convert_material(self, value, b_f, u_f, b_t, u_t, use_material):

        result = converter_mode.c_material(
            1,
            basis_from=b_f,
            basis_to=b_t,
            unit_from=u_f,
            unit_to=u_t,
            material=pygaps.Material.find('TEST')
        )

        assert result == pytest.approx(value, rel=1e-3)

    @pytest.mark.parametrize(
        'value, m_f, u_f, m_t, u_t',
        [
            (1, 'absolute', 'bar', 'absolute', 'bar'),  # 1 bar -> 1 bar
            (100000, 'absolute', 'bar', 'absolute', 'Pa'),  # 1 bar -> 1E5 Pa
            (0.9869, 'absolute', 'bar', 'absolute',
             'atm'),  # 1 bar -> 0.98 atm
            (1, 'relative', 'bar', 'relative',
             'Pa'),  # 1 p/p0 (N2, 77K) -> 1 p/p0 (N2, 77K)
            (0.9882, 'absolute', 'bar', 'relative',
             'bar'),  # 1 bar -> ~0.98 p/p0 (N2, 77K)
            (101193.756, 'relative', None, 'absolute',
             'Pa'),  # 1 p/p0 -> 101K Pa
            (101193.756, 'relative', 'Pa', 'absolute',
             'Pa'),  # 1 p/p0 -> 101K Pa
        ]
    )
    def test_convert_pressure(self, value, m_f, u_f, m_t, u_t):

        result = converter_mode.c_pressure(
            1,
            mode_from=m_f,
            unit_from=u_f,
            mode_to=m_t,
            unit_to=u_t,
            adsorbate=pygaps.Adsorbate.find('N2'),
            temp=77.344
        )

        assert result == pytest.approx(value, rel=1e-3)
