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
    def test_isotherm_miss_key(self, isotherm_parameters, missing_key):
        "Tests exception throw for missing data primary key (loading/pressure)"

        keys = dict(
            pressure_key="pressure",
            loading_key="loading",
        )

        del keys[missing_key]

        with pytest.raises(Exception):
            adsutils.classes.isotherm.Isotherm(
                loading_key=keys.get('loading_key'),
                pressure_key=keys.get('pressure_key'),
                **isotherm_parameters)

        return

    @pytest.mark.parametrize('missing_param',
                             ['sample_name', 'sample_batch', 't_exp', 'gas'])
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        "Tests exception throw for missing required attributes"

        pressure_key = "pressure"
        loading_key = "loading"

        data = isotherm_parameters
        del data[missing_param]

        with pytest.raises(Exception):
            adsutils.classes.isotherm.Isotherm(
                loading_key=loading_key,
                pressure_key=pressure_key,
                **data)

        return

    @pytest.mark.parametrize('prop, set_to', [
                            ('mode_adsorbent', None),
                            ('mode_adsorbent', 'something'),
                            ('mode_pressure', None),
                            ('mode_pressure', 'something'),
                            ('unit_loading', None),
                            ('unit_loading', 'something'),
                            ('unit_pressure', None),
                            ('unit_pressure', 'something')])
    def test_isotherm_mode_and_units(self, isotherm_parameters, prop, set_to):
        "Tests exception throw for missing or wrong unit"

        pressure_key = "pressure"
        loading_key = "loading"

        props = dict(
            mode_adsorbent='mass',
            mode_pressure='absolute',
            unit_loading='mmol',
            unit_pressure='bar',
        )

        props[prop] = set_to

        with pytest.raises(Exception):
            adsutils.classes.isotherm.Isotherm(
                loading_key=loading_key,
                pressure_key=pressure_key,
                mode_adsorbent=props.get('mode_adsorbent'),
                mode_pressure=props.get('mode_pressure'),
                unit_loading=props.get('unit_loading'),
                unit_pressure=props.get('unit_pressure'),
                **isotherm_parameters)

        return

    def test_isotherm_get_parameters(self, isotherm_parameters, basic_isotherm):
        "Checks isotherm returns the same dict as was used to create it"

        assert isotherm_parameters == basic_isotherm.get_parameters()

    def test_isotherm_print_parameters(self, basic_isotherm):
        "Checks isotherm can print its own info"

        return basic_isotherm.print_info()


class TestPointIsotherm(object):
    """
    Tests the pointisotherm class
    """

    def test_isotherm_create(self, basic_pointisotherm):
        "Checks isotherm can be created from test data"
        return basic_pointisotherm

    def test_isotherm_ret_funcs(self, basic_pointisotherm):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        other_key = "enthalpy"

        isotherm = basic_pointisotherm

        assert set(isotherm.pressure_all()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
        assert set(isotherm.loading_all()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
        assert set(isotherm.other_key_ads(other_key)) == set([
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        assert isotherm.has_ads()
        assert isotherm.has_des()

        assert isotherm.data_ads().equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        }))

        assert isotherm.data_des().equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [4.0, 2.0],
            basic_pointisotherm.loading_key: [4.0, 2.0],
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

    @pytest.mark.parametrize('unit, multiplier', [
                            ('mmol', 1),
                            ('mol', 1e-3),
                            ('cm3 STP', 22.414),
        pytest.param("bad_unit", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_loading(self, basic_pointisotherm, isotherm_data, unit, multiplier):
        """Checks that the loading conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_loading(unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading_all()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('unit, multiplier', [
                            ('bar', 1),
                            ('Pa', 1e5),
        pytest.param("bad_unit", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_pressure(self, basic_pointisotherm, isotherm_data, unit, multiplier):
        """Checks that the pressure conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_pressure(unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure_all()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('mode, multiplier', [
                            ('mass', 1),
                            ('volume', 22.5),
        pytest.param("bad_mode", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_loading_mode(self, basic_pointisotherm, basic_sample,
                                           isotherm_data, mode, multiplier):
        """Checks that the loading mode conversion function work as expected"""

        # Add sample to list
        adsutils.data.SAMPLE_LIST.append(basic_sample)

        # Do the conversion
        basic_pointisotherm.convert_adsorbent_mode(mode)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading_all()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('mode, multiplier', [
                            ('absolute', 1),
                            ('relative', 1 / 7.7827),
        pytest.param("bad_mode", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_pressure_mode(self, basic_pointisotherm, basic_gas,
                                            isotherm_data, mode, multiplier):
        """Checks that the pressure mode conversion function work as expected"""

        # Add sample to list
        adsutils.data.GAS_LIST.append(basic_gas)

        # Do the conversion
        basic_pointisotherm.convert_pressure_mode(mode)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure_all()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    def test_isotherm_print_parameters(self, basic_isotherm):
        "Checks isotherm can print its own info"

        return basic_isotherm.print_info()


class TestModelIsotherm(object):
    """
    Tests the pointisotherm class
    """

    @pytest.mark.parametrize('model, data', [
        ("Langmuir", [3.0, 6.0, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        ("Quadratic", [3.0, 6.0, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        ("Henry", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0]),
        ("TemkinApprox", [3.0, 6.0, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        ("DSLangmuir", [3.0, 5.5, 7.0, 8.0, 8.5, 8.8, 0, 0]),
        # ("TSLangmuir", [3.2, 5.4, 6.8, 7.8, 8.5, 9.0, 0, 0]),
        # ("BET", [3.2, 5.4, 6.8, 7.8, 8.5, 9.0, 0, 0]),
    ])
    def test_isotherm_create(self, isotherm_data, basic_isotherm, model, data):
        "Checks isotherm can be created from test data"

        isotherm_data['loading'] = data

        adsutils.ModelIsotherm.from_isotherm(
            basic_isotherm,
            isotherm_data[:6],
            model)
