import adsutils.utilities as utilities


def test_matplotlib_chemformula():
    assert utilities.matplotlib_chemformula.convert_chemformula(
        "C4H10") == "$C_{4}H_{10}$"
