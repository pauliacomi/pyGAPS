"""
Tests utilities
"""

from pathlib import Path

import pytest

import pygaps.utilities as util


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
    assert util.string_utilities.cast_string(test) == res


@pytest.mark.utilities
@pytest.mark.parametrize("test, res", [("N2", "$N_{2}$"), ("C4H10", "$C_{4}H_{10}$")])
def test_convert_chemformula(test, res):
    assert util.string_utilities.convert_chemformula(test) == res


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
    assert util.string_utilities.convert_unit_ltx(test, neg) == res


@pytest.mark.utilities
def test_file_paths():
    path = Path(__file__) / 'tst'

    with pytest.raises(Exception):
        util.python_utilities.get_file_paths(path)

    known_paths = [path / '1.tst', path / '2.tst']
    paths = util.python_utilities.get_file_paths(path, extension='tst')

    assert all([path in known_paths for path in paths])


# yapf: disable
@pytest.mark.utilities
@pytest.mark.parametrize(
    "source, overrides, res",
    [
        ({'h1': 1}, {'h2': 2}, {'h1': 1, 'h2': 2}),
        ({'h1': 0}, {'h1': {'b': 1}}, {'h1': {'b': 1}}),
        ({'h': "to"}, {'h': "tov"}, {'h': "tov"}),
        ({'h': {'a': 1, 'b': 2}}, {'h': {'a': 2, 'b': 2}}, {'h': {'a': 2, 'b': 2}}),
        ({'h': {'a': 1, 'b': 2}}, {'h': {'a': {}, 'b': 2}}, {'h': {'a': {}, 'b': 2}}),
        ({'h': {'a': {}, 'b': 2}}, {'h': {'a': 2}}, {'h': {'a': 2, 'b': 2}}),
    ]
)
def test_deep_merge(source, overrides, res):
    util.python_utilities.deep_merge(source, overrides)
    assert source == res
# yapf: enable
