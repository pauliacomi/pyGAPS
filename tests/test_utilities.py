from adsutils.utilities import matplotlib_chemformula


def test_matplotlib_chemformula():
    assert matplotlib_chemformula.convert_chemformula(
        "C4H10") == "$C_{4}H_{10}$"
