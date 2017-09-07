import os

import pytest

import pygaps.calculations

HERE = os.path.dirname(__file__)


def approx(value1, value2, error):
    return (value1 < value2 * (1 + error)
            ) and (value1 > value2 * (1 - error))


class TestBET(object):
    """
    Tests everything related to BET surface area calculation
    """

    def test_BET_checks(self, basic_pointisotherm, basic_adsorbate, basic_sample):
        """Test BET chacks"""

        isotherm = basic_pointisotherm
        adsorbate = basic_adsorbate
        c_s_area = adsorbate.properties.pop("cross_sectional_area")

        # Will raise a "isotherm not in relative pressure mode exception"
        with pytest.raises(Exception):
            pygaps.area_BET(isotherm)

        pygaps.data.GAS_LIST.append(adsorbate)
        isotherm.convert_mode_pressure("relative")
        isotherm.convert_unit_loading("cm3 STP")

        # Will raise a "isotherm loading not in mmol exception"
        with pytest.raises(Exception):
            pygaps.area_BET(isotherm)

        pygaps.data.SAMPLE_LIST.append(basic_sample)
        isotherm.convert_unit_loading("mmol")
        isotherm.convert_mode_adsorbent("volume")

        # Will raise a "isotherm loading not in volume mode exception"
        with pytest.raises(Exception):
            pygaps.area_BET(isotherm)

        isotherm.convert_mode_adsorbent("mass")
        pygaps.data.GAS_LIST = []

        # Will raise a "adsorbate not found exception"
        with pytest.raises(Exception):
            pygaps.area_BET(isotherm)

        # Will raise a "adsorbate has no cross sectional area"
        with pytest.raises(Exception):
            pygaps.area_BET(isotherm)

        adsorbate.properties["cross_sectional_area"] = c_s_area
        pygaps.data.GAS_LIST = []
        pygaps.data.GAS_LIST.append(adsorbate)

        return

    @pytest.mark.parametrize('file, expected_bet', [
        ('MCM-41 N2 77.355.json', 400.0),
        ('NaY N2 77.355.json', 700.0),
        ('SiO2 N2 77.355.json', 200.0),
        ('Takeda 5A N2 77.355.json', 1075.0),
        ('UiO-66(Zr) N2 77.355.json', 1250.0),
    ])
    def test_BET(self, file, expected_bet, basic_adsorbate):
        """Test BET calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        bet_area = pygaps.area_BET(isotherm).get("bet_area")

        max_error = 0.1  # 10 percent

        assert approx(bet_area, expected_bet, max_error)


class TestTPlot(object):
    """
    Tests everything related to tplot calculation
    """
    @pytest.mark.parametrize('file, area, micropore_volume', [
        ('MCM-41 N2 77.355.json', 60, -0.1),
        ('NaY N2 77.355.json', 100, 0.17),
        ('SiO2 N2 77.355.json', 250, -0.1),
        ('Takeda 5A N2 77.355.json', 85, 0),
        ('UiO-66(Zr) N2 77.355.json', 3.5, 0.13),
    ])
    def test_tplot(self, file, basic_adsorbate, area, micropore_volume):
        """Test BET calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        t_plot_r = pygaps.t_plot(
            isotherm, 'Halsey')

        results = t_plot_r.get('results')
        assert results is not None

        # max_error = 0.1  # 10 percent

        # assert approx(results[0].get('adsorbed_volume'),
        #              micropore_volume, max_error)
        # assert approx(results[-1].get('area'), area, max_error)


class TestAlphaSPlot(object):
    """
    Tests everything related to alpha-s calculation
    """


class TestPSD(object):
    """
    Tests everything related to pore size distribution calculation
    """
    @pytest.mark.parametrize('method', [
        'BJH',
        'DH',
    ])
    @pytest.mark.parametrize('file', [
        ('MCM-41 N2 77.355.json'),
        #        ('NaY N2 77.355.json'),
        #        ('SiO2 N2 77.355.json'),
        #        ('Takeda 5A N2 77.355.json'),
        #        ('UiO-66(Zr) N2 77.355.json'),
    ])
    def test_psd_meso(self, file, basic_adsorbate, method):
        """Test psd calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        result_dict = pygaps.mesopore_size_distribution(
            isotherm, psd_model=method, branch='desorption', thickness_model='Halsey', verbose=True)

        # max_error = 0.1  # 10 percent

    @pytest.mark.parametrize('method', [
        'HK',
    ])
    @pytest.mark.parametrize('file', [
        ('Takeda 5A N2 77.355.json'),
        ('UiO-66(Zr) N2 77.355.json'),
    ])
    def test_psd_micro(self, file, basic_adsorbate, method):
        """Test psd calculation with several model isotherms"""
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        filepath = os.path.join(HERE, 'data', 'isotherms_json', file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.isotherm_from_json(
                text_file.read())

        isotherm.convert_mode_pressure('relative')

        result_dict = pygaps.micropore_size_distribution(
            isotherm, psd_model=method, pore_geometry='slit', verbose=True)

        # max_error = 0.1  # 10 percent
