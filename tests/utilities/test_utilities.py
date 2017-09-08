"""
Tests utilities
"""

import pygaps.utilities as utilities


def test_matplotlib_chemformula():
    assert utilities.string_utilities.convert_chemformula(
        "C4H10") == "$C_{4}H_{10}$"
