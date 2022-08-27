"""
Tests python utilities
"""

import pytest

import pygaps.utilities as util


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
