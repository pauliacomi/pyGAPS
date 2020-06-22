"""
Tests utilities
"""

from pathlib import Path

import pytest

import pygaps.utilities as utilities


@pytest.mark.core
def test_matplotlib_chemformula():
    assert utilities.string_utilities.convert_chemformula(
        "C4H10"
    ) == "$C_{4}H_{10}$"


@pytest.mark.core
def test_file_paths():
    path = Path(__file__) / 'tst'

    with pytest.raises(Exception):
        utilities.folder_utilities.util_get_file_paths(path)

    known_paths = [path / '1.tst', path / '2.tst']
    paths = utilities.folder_utilities.util_get_file_paths(
        path, extension='tst'
    )

    assert all([path in known_paths for path in paths])
