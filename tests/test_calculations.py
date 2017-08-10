import os

import pytest

import adsutils.calculations

# %%


HERE = os.path.dirname(__file__)


@pytest.mark.parametrize('file, expected_bet', [
    ('MCM-41 N2 77.json', 350.0),
    ('NaY N2 77.json', 700.0),
    ('SiO2 N2 77.json', 200.0),
    ('Takeda 5A N2 77.json', 1075.0),
    ('UiO-66(Zr) N2 77.json', 1250.0),
])
def test_BET(file, expected_bet, basic_gas):

    adsutils.data.GAS_LIST.append(basic_gas)

    filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

    with open(filepath, 'r') as text_file:
        isotherm = adsutils.isotherm_from_json(text_file.read())

    isotherm.convert_pressure_mode("relative")
    bet_area = adsutils.calculations.area_BET(isotherm)

    max_error = 0.1  # 10 percent

    assert (bet_area < expected_bet * (1 + max_error)
            ) and (bet_area > expected_bet * (1 - max_error))
