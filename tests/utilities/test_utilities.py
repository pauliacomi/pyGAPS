"""
Tests utilities
"""

from pathlib import Path

import pytest

import pygaps.utilities as util


@pytest.mark.core
def test_convert_chemformula():
    assert util.string_utilities.convert_chemformula("N2") == "$N_{2}$"
    assert util.string_utilities.convert_chemformula(
        "C4H10"
    ) == "$C_{4}H_{10}$"


@pytest.mark.core
def test_convert_unit_ltx():
    assert util.string_utilities.convert_unit_ltx("mmol") == "mmol"
    assert util.string_utilities.convert_unit_ltx("g", True) == "g^{-1}"
    assert util.string_utilities.convert_unit_ltx("cm3") == "cm^{3}"
    assert util.string_utilities.convert_unit_ltx("cm3(STP)") == "cm^{3}_{STP}"
    assert util.string_utilities.convert_unit_ltx("cm3", True) == "cm^{-3}"


@pytest.mark.core
def test_file_paths():
    path = Path(__file__) / 'tst'

    with pytest.raises(Exception):
        util.python_utilities.get_file_paths(path)

    known_paths = [path / '1.tst', path / '2.tst']
    paths = util.python_utilities.get_file_paths(path, extension='tst')

    assert all([path in known_paths for path in paths])


@pytest.mark.core
def test_deep_merge():
    source = {'hello1': 1}
    overrides = {'hello2': 2}
    util.python_utilities.deep_merge(source, overrides)
    assert source == {'hello1': 1, 'hello2': 2}

    source = {'hello1': 0}
    overrides = {'hello1': {'bar': 1}}
    util.python_utilities.deep_merge(source, overrides)
    assert source == {'hello1': {'bar': 1}}

    source = {'hello': 'to_override'}
    overrides = {'hello': 'over'}
    util.python_utilities.deep_merge(source, overrides)
    assert source == {'hello': 'over'}

    source = {'hello': {'value': 'to_override', 'no_change': 1}}
    overrides = {'hello': {'value': 'over'}}
    util.python_utilities.deep_merge(source, overrides)
    assert source == {'hello': {'value': 'over', 'no_change': 1}}

    source = {'hello': {'value': 'to_override', 'no_change': 1}}
    overrides = {'hello': {'value': {}}}
    util.python_utilities.deep_merge(source, overrides)
    assert source == {'hello': {'value': {}, 'no_change': 1}}

    source = {'hello': {'value': {}, 'no_change': 1}}
    overrides = {'hello': {'value': 2}}
    util.python_utilities.deep_merge(source, overrides)
    assert source == {'hello': {'value': 2, 'no_change': 1}}
