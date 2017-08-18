import os

import pytest

import adsutils.calculations

# %%


HERE = os.path.dirname(__file__)


class TestBET(object):
    """
    Tests everything related to BET surface area calculation
    """

    def test_BET_checks(self, basic_pointisotherm, basic_gas, basic_sample):
        """Test BET chacks"""

        isotherm = basic_pointisotherm
        gas = basic_gas
        c_s_area = gas.properties.pop("cross_sectional_area")

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(Exception):
            adsutils.calculations.area_BET(isotherm)

        adsutils.data.GAS_LIST.append(gas)
        isotherm.convert_pressure_mode("relative")
        isotherm.convert_loading("cm3 STP")

        # Will raise a "isotherm loading not in mmol exception"
        with pytest.raises(Exception):
            adsutils.calculations.area_BET(isotherm)

        adsutils.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_loading("mmol")
        isotherm.convert_adsorbent_mode("volume")

        # Will raise a "isotherm loading not in volume mode exception"
        with pytest.raises(Exception):
            adsutils.calculations.area_BET(isotherm)

        isotherm.convert_adsorbent_mode("mass")
        adsutils.data.GAS_LIST = []

        # Will raise a "gas not found exception"
        with pytest.raises(Exception):
            adsutils.calculations.area_BET(isotherm)

        # Will raise a "gas has no cross sectional area"
        with pytest.raises(Exception):
            adsutils.calculations.area_BET(isotherm)

        gas.properties["cross_sectional_area"] = c_s_area
        adsutils.data.GAS_LIST = []
        adsutils.data.GAS_LIST.append(gas)

        return

    @pytest.mark.parametrize('file, expected_bet', [
        ('MCM-41 N2 77.json', 350.0),
        ('NaY N2 77.json', 700.0),
        ('SiO2 N2 77.json', 200.0),
        ('Takeda 5A N2 77.json', 1075.0),
        ('UiO-66(Zr) N2 77.json', 1250.0),
    ])
    def test_BET(self, file, expected_bet, basic_gas):
        """Test BET calculation with several model isotherms"""
        adsutils.data.GAS_LIST.append(basic_gas)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = adsutils.isotherm_from_json(
                text_file.read(), mode_pressure='relative')

        bet_area = adsutils.calculations.area_BET(isotherm).get("bet_area")

        max_error = 0.1  # 10 percent

        assert (bet_area < expected_bet * (1 + max_error)
                ) and (bet_area > expected_bet * (1 - max_error))


class TestTPlot(object):
    """
    Tests everything related to tplot calculation
    """
    @pytest.mark.parametrize('file', [
        ('MCM-41 N2 77.json'),
        ('NaY N2 77.json'),
        ('SiO2 N2 77.json'),
        ('Takeda 5A N2 77.json'),
        ('UiO-66(Zr) N2 77.json'),
    ])
    def test_tplot(self, file, basic_gas):
        """Test BET calculation with several model isotherms"""
        adsutils.data.GAS_LIST.append(basic_gas)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = adsutils.isotherm_from_json(
                text_file.read(), mode_pressure='relative')

        result_dict = adsutils.t_plot(
            isotherm, 'Halsey')

        max_error = 0.1  # 10 percent


class TestPSD(object):
    """
    Tests everything related to pore size dist calculation
    """
    @pytest.mark.parametrize('file', [
        ('MCM-41 N2 77.json'),
        ('NaY N2 77.json'),
        ('SiO2 N2 77.json'),
        ('Takeda 5A N2 77.json'),
        ('UiO-66(Zr) N2 77.json'),
    ])
    def test_psd(self, file, basic_gas):
        """Test BET calculation with several model isotherms"""
        adsutils.data.GAS_LIST.append(basic_gas)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = adsutils.isotherm_from_json(
                text_file.read(), mode_pressure='relative')

        result_dict = adsutils.pore_size_distribution(
            isotherm, 'BJH', branch='desorption', thickness_model='Halsey',
            verbose=True)

        max_error = 0.1  # 10 percent
