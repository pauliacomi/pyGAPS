"""
This test module has tests relating to the pointisotherm class
"""
import pandas
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps


class TestPointIsotherm(object):
    """
    Tests the pointisotherm class
    """

    def test_isotherm_create(self, basic_pointisotherm):
        "Checks isotherm can be created from test data"
        return basic_pointisotherm

    @pytest.mark.parametrize('missing_key',
                             ['loading_key', 'pressure_key'])
    def test_isotherm_miss_key(self, isotherm_parameters, isotherm_data, missing_key):
        "Tests exception throw for missing data primary key (loading/pressure)"

        keys = dict(
            pressure_key="pressure",
            loading_key="loading",
        )

        del keys[missing_key]

        with pytest.raises(pygaps.ParameterError):
            pygaps.classes.pointisotherm.PointIsotherm(
                isotherm_data,
                loading_key=keys.get('loading_key'),
                pressure_key=keys.get('pressure_key'),
                **isotherm_parameters)

        return

    def test_isotherm_ret_funcs(self, basic_pointisotherm):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        other_key = "enthalpy"
        isotherm = basic_pointisotherm

        # branch
        assert isotherm.has_branch(branch='ads')
        assert isotherm.has_branch(branch='des')

        # data()
        assert isotherm.data().equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
        }))
        assert isotherm.data(branch='ads').equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        }))
        assert isotherm.data(branch='des').equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [4.5, 2.5],
            basic_pointisotherm.loading_key: [4.5, 2.5],
            other_key: [4.0, 4.0],
        }, index=[6, 7]))

        # pressure()
        assert set(isotherm.pressure()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5])
        assert set(isotherm.pressure(branch='ads')) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert set(isotherm.pressure(branch='des')) == set([4.5, 2.5])
        assert set(isotherm.pressure(branch='ads', min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # loading()
        assert set(isotherm.loading()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5])
        assert set(isotherm.loading(branch='ads')) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert set(isotherm.loading(branch='des')) == set([4.5, 2.5])
        assert set(isotherm.loading(branch='ads', min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # other_data()
        assert set(isotherm.other_data(other_key)) == set([
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0])
        assert set(isotherm.other_data(other_key, branch='ads')
                   ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        assert set(isotherm.other_data(
            other_key, branch='des')) == set([4.0, 4.0])

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
        basic_pointisotherm.convert_unit_loading(unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading()

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
        basic_pointisotherm.convert_unit_pressure(unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('basis, multiplier', [
                            ('mass', 1),
                            ('volume', 0.1),
        pytest.param("bad_mode", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_loading_basis(self, basic_pointisotherm, basic_sample,
                                            isotherm_data, basis, multiplier):
        """Checks that the loading basis conversion function work as expected"""

        # Add sample to list
        pygaps.data.SAMPLE_LIST.append(basic_sample)

        # Do the conversion
        basic_pointisotherm.convert_basis_adsorbent(basis)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('mode, multiplier', [
                            ('relative', 1 / 7.7827),
                            ('absolute', 1),
        pytest.param("bad_mode", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_pressure_mode(self, basic_pointisotherm,
                                            isotherm_data, mode, multiplier):
        """Checks that the pressure mode conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_mode_pressure(mode)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    def test_isotherm_loading_interpolation(self, basic_pointisotherm, basic_sample):
        """Checks that the interpolation works as expected"""

        # Add sample to list
        pygaps.data.SAMPLE_LIST.append(basic_sample)

        assert basic_pointisotherm.loading_at(3.5) == 3.5
        assert basic_pointisotherm.loading_at(
            10, interp_fill=10) == 10
        assert basic_pointisotherm.loading_at(
            1, loading_unit='mol') == 0.001
        assert basic_pointisotherm.loading_at(
            100000, pressure_unit='Pa') == 1
        assert basic_pointisotherm.loading_at(
            1, adsorbent_basis='volume') == 0.1
        assert basic_pointisotherm.loading_at(
            0.25697, pressure_mode='relative') == pytest.approx(2, 0.001)

    @cleanup
    def test_isotherm_print_parameters(self, basic_pointisotherm):
        "Checks isotherm can print its own info"

        basic_pointisotherm.print_info()
