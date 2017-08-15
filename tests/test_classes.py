"""
This test module has tests relating to classes
"""

import pandas
import pytest

import adsutils


class TestIsotherm(object):
    """
    Tests the parent isotherm object
    """

    def test_isotherm_created(self, basic_isotherm):
        "Checks isotherm can be created from test data"
        return basic_isotherm

    @pytest.mark.parametrize('missing_key',
                             ['loading_key', 'pressure_key'])
    def test_isotherm_miss_key(self, isotherm_data, missing_key):
        "Tests exception throw for missing data primary key (loading/pressure)"

        keys = dict(
            pressure_key="pressure",
            loading_key="loading",
        )

        del keys[missing_key]

        with pytest.raises(Exception):
            adsutils.classes.isotherm.Isotherm(
                loading_key=keys['loading_key'],
                pressure_key=keys['pressure_key'],
                **isotherm_data)

        return

    @pytest.mark.parametrize('missing_param',
                             ['sample_name', 'sample_batch', 't_exp', 'gas'])
    def test_isotherm_miss_param(self, isotherm_data, missing_param):
        "Tests exception throw for missing required attributes"

        pressure_key = "pressure"
        loading_key = "loading"

        data = isotherm_data
        del data[missing_param]

        with pytest.raises(Exception):
            adsutils.classes.isotherm.Isotherm(
                loading_key=loading_key,
                pressure_key=pressure_key,
                **isotherm_data)

        return


class TestPointIsotherm(object):
    """
    Tests the pointisotherm class
    """

    def test_isotherm_ret_funcs(self, basic_isotherm, basic_pointisotherm):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        other_key = "enthalpy"
        other_keys = [other_key]

        isotherm = basic_pointisotherm

        assert set(isotherm.pressure_all()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
        assert set(isotherm.loading_all()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
        assert set(isotherm.other_key_ads(other_key)) == set([
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        assert isotherm.has_ads()
        assert isotherm.has_des()

        assert isotherm.adsdata().equals(pandas.DataFrame({
            basic_isotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            basic_isotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        }))

        assert isotherm.desdata().equals(pandas.DataFrame({
            basic_isotherm.pressure_key: [4.0, 2.0],
            basic_isotherm.loading_key: [4.0, 2.0],
            other_key: [5.0, 5.0],
        }, index=[6, 7]))

        assert set(isotherm.pressure_ads()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert set(isotherm.loading_ads()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert set(isotherm.other_key_ads(other_key)
                   ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        assert set(isotherm.pressure_des()) == set([4.0, 2.0])
        assert set(isotherm.loading_des()) == set([4.0, 2.0])
        assert set(isotherm.other_key_des(other_key)) == set([5.0, 5.0])

        return
