"""
Tests utilities
"""

import os

import pytest

import pygaps.utilities as utilities

HERE = os.path.dirname(__file__)


@pytest.mark.core
def test_matplotlib_chemformula():
    assert utilities.string_utilities.convert_chemformula(
        "C4H10") == "$C_{4}H_{10}$"


@pytest.mark.core
def test_file_paths():
    path = os.path.join(HERE, 'tst')

    with pytest.raises(Exception):
        utilities.folder_utilities.util_get_file_paths(path)

    known_paths = [os.path.join(path, '1.tst'), os.path.join(path, '2.tst')]
    paths = utilities.folder_utilities.util_get_file_paths(
        path, extension='.tst')

    assert paths == known_paths
