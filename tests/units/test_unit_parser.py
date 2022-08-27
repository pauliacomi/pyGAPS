import pytest

import pygaps.parsing.unit_parsing as unit_parsing


@pytest.mark.utilities
@pytest.mark.parametrize(
    "test, res", [
        ("\" mmol  / g \"", "mmol / g"),
        ("mmol g^(-1)", "mmol g-1"),
        ("cm³(STP)/g", "cm3stp/g"),
        ("cm³_{STP} g^{-1}", "cm3stp g-1"),
        ("ml  g-1 STP", "ml g-1 stp"),
        ("wt%", "wt%"),
    ]
)
def test_clean_string(test, res):
    out = unit_parsing.clean_string(test, unit_parsing.pre_proc_sub)
    assert out == res


@pytest.mark.utilities
@pytest.mark.parametrize(
    "test, res", [
        ("degC", "°C"),
        ("°C", "°C"),
        ("C", "°C"),
        ("degK", "K"),
        ("K", "K"),
    ]
)
def test_parse_temperature_string(test, res):
    out = unit_parsing.parse_temperature_string(test)
    assert out == res


@pytest.mark.utilities
@pytest.mark.parametrize(
    "test, res", [
        ("relative", ["relative", None]),
        ("relative%", ["relative%", None]),
        ("mbar", ["absolute", "mbar"]),
        ("kPa", ["absolute", "kPa"]),
        ("torr", ["absolute", "torr"]),
    ]
)
def test_parse_pressure_string(test, res):
    out = unit_parsing.parse_pressure_string(test)
    assert list(out.values()) == res


@pytest.mark.utilities
@pytest.mark.parametrize(
    "test, res", [
        ("wt%", ["percent", None, "mass", None]),
        ("molar%", ["percent", None, "molar", None]),
        ("%mol", ["percent", None, "molar", None]),
        ("fractional volume", ["fraction", None, "volume", None]),
        ("mass fraction", ["fraction", None, "mass", None]),
        ("mmol/g", ["molar", "mmol", "mass", "g"]),
        ("mmol g^-1", ["molar", "mmol", "mass", "g"]),
        ("mmol /g", ["molar", "mmol", "mass", "g"]),
        ("mol kg^{-1}", ["molar", "mol", "mass", "kg"]),
        ("cc STP / g", ["molar", "cc(STP)", "mass", "g"]),
        ("cm3 STP g-1", ["molar", "cm3(STP)", "mass", "g"]),
        ("cm³_{STP} g^{-1}", ["molar", "cm3(STP)", "mass", "g"]),
        ("ml(STP) / g", ["molar", "mL(STP)", "mass", "g"]),
        ("cc STP /g", ["molar", "cc(STP)", "mass", "g"]),
        ("cm3 g^-1 (STP)", ["molar", "cm3(STP)", "mass", "g"]),
        ("cm3 g^(-1), (STP)", ["molar", "cm3(STP)", "mass", "g"]),
        ("cc /cm3", ["volume_gas", "cc", "volume", "cm3"]),
        ("g /cm3", ["mass", "g", "volume", "cm3"]),
        ("ml L-1", ["volume_gas", "mL", "volume", "L"]),
    ]
)
def test_parse_loading_string(test, res):
    out = unit_parsing.parse_loading_string(test)
    assert list(out.values()) == res
