import pytest

import pygaps.utilities.string_utilities as str_util


@pytest.mark.utilities
@pytest.mark.parametrize("test, res", [
    ("N2", "$N_{2}$"),
    ("C4H10", "$C_{4}H_{10}$"),
])
def test_convert_chemformula(test, res):
    assert str_util.convert_chemformula_ltx(test) == res


@pytest.mark.utilities
@pytest.mark.parametrize(
    "test, neg, res",
    [
        ("mmol", False, "mmol"),
        ("g", True, "g^{-1}"),
        ("cm3", False, "cm^{3}"),
        ("cm3(STP)", False, "cm^{3}_{STP}"),
        ("cm3", True, "cm^{-3}"),
    ],
)
def test_convert_unit_ltx(test, neg, res):
    assert str_util.convert_unit_ltx(test, neg) == res


@pytest.mark.utilities
@pytest.mark.parametrize(
    "test, res",
    [
        (None, None),
        ("none", None),
        ("None", None),
        ("true", True),
        ("False", False),
        ("30", 30),
        ("0", 0),
        ("1.2", 1.2),
        ("-2.24", -2.24),
        ("[1,2,3,4]", [1, 2, 3, 4]),
    ],
)
def test_cast_string(test, res):
    assert str_util.cast_string(test) == res
