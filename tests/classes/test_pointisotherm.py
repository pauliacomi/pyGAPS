"""
This test module has tests relating to the pointisotherm class
"""
import numpy
import pandas
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps


@pytest.mark.core
class TestPointIsotherm(object):
    """
    Tests the pointisotherm class
    """
##########################

    def test_isotherm_create(self):
        "Checks isotherm can be created from basic data"

        pygaps.PointIsotherm(
            pandas.DataFrame({
                'pressure': [1, 2, 3, 4, 5, 3, 2],
                'loading': [1, 2, 3, 4, 5, 3, 2]
            }),
            loading_key='loading',
            pressure_key='pressure',
            sample_name='carbon',
            sample_batch='X1',
            adsorbate='nitrogen',
            t_exp=77,
        )
        return

    def test_isotherm_id(self, basic_pointisotherm):
        "Checks isotherm id works as intended"

        iso_id = basic_pointisotherm.id
        basic_pointisotherm.nothing = 'changed'
        assert iso_id == basic_pointisotherm.id
        basic_pointisotherm._data = basic_pointisotherm._data[:5]
        assert iso_id != basic_pointisotherm.id

        return

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
            pygaps.PointIsotherm(
                isotherm_data,
                loading_key=keys.get('loading_key'),
                pressure_key=keys.get('pressure_key'),
                **isotherm_parameters)

        return

    @pytest.mark.parametrize('branch, expected', [
        ('guess', 4.5),
        ('des', 1.0),
        ([False, False, True, True, True, True, True, True], 3.0),
    ])
    def test_isotherm_create_branches(self, isotherm_parameters, isotherm_data, branch, expected):
        "Tests if isotherm branches are well specified"

        isotherm = pygaps.PointIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            other_keys=['enthalpy'],
            branch=branch,
            ** isotherm_parameters
        )

        assert isotherm.pressure(branch='des')[0] == expected

    def test_isotherm_equality(self, isotherm_parameters, isotherm_data, basic_pointisotherm):
        "Checks isotherm id's are unique"

        isotherm = pygaps.PointIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            other_keys=['enthalpy'],
            **isotherm_parameters
        )

        assert isotherm == basic_pointisotherm

        isotherm.t_act = 0

        assert isotherm != basic_pointisotherm

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        "Checks isotherm can be created from isotherm"

        # regular creation
        isotherm = pygaps.PointIsotherm.from_isotherm(
            basic_isotherm,
            pandas.DataFrame({
                'pressure': [1, 2, 3, 4, 5, 3, 2],
                'loading': [1, 2, 3, 4, 5, 3, 2]
            }),
            pressure_key='pressure',
            loading_key='loading',
        )

        assert isotherm != basic_isotherm

    def test_isotherm_create_from_modelisotherm(self, basic_modelisotherm, basic_pointisotherm):
        "Checks isotherm can be created from isotherm"

        # regular creation
        isotherm = pygaps.PointIsotherm.from_modelisotherm(
            basic_modelisotherm,
            pressure_points=None
        )

        # Specifying points
        isotherm = pygaps.PointIsotherm.from_modelisotherm(
            basic_modelisotherm,
            pressure_points=[1, 2, 3, 4]
        )

        # Specifying isotherm
        isotherm = pygaps.PointIsotherm.from_modelisotherm(
            basic_modelisotherm,
            pressure_points=basic_pointisotherm
        )

        assert isotherm != basic_modelisotherm

##########################
    def test_isotherm_ret_has_branch(self, basic_pointisotherm):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        # branch
        assert basic_pointisotherm.has_branch(branch='ads')
        assert basic_pointisotherm.has_branch(branch='des')

        return

    def test_isotherm_ret_data(self, basic_pointisotherm):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        other_key = "enthalpy"

        # all data
        data = basic_pointisotherm.data()
        data2 = pandas.DataFrame({
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
        })
        assert data.equals(data2)

        # adsorption branch
        assert basic_pointisotherm.data(branch='ads').equals(pandas.DataFrame({
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }))

        # desorption branch
        assert basic_pointisotherm.data(branch='des').equals(pandas.DataFrame({
            other_key: [4.0, 4.0],
            basic_pointisotherm.loading_key: [4.5, 2.5],
            basic_pointisotherm.pressure_key: [4.5, 2.5],
        }, index=[6, 7]))

        return

    def test_isotherm_ret_pressure(self, basic_pointisotherm, use_adsorbate):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        # Regular return
        assert set(basic_pointisotherm.pressure()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5])

        # Branch specified
        assert set(basic_pointisotherm.pressure(
            branch='des')) == set([4.5, 2.5])

        # Unit specified
        assert set(basic_pointisotherm.pressure(branch='ads', pressure_unit='Pa')) == set(
            [100000, 200000, 300000, 400000, 500000, 600000])

        # Mode specified
        assert basic_pointisotherm.pressure(branch='ads', pressure_mode='relative')[
            0] == pytest.approx(0.12849, 0.001)

        # Mode and unit specified
        assert basic_pointisotherm.pressure(branch='ads',
                                            pressure_unit='Pa',
                                            pressure_mode='relative')[0] == pytest.approx(0.12849, 0.001)

        # Range specified
        assert set(basic_pointisotherm.pressure(branch='ads', min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # Indexed option specified
        assert basic_pointisotherm.pressure(indexed=True).equals(pandas.Series(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5]
        ))

        return

    def test_isotherm_ret_loading(self, basic_pointisotherm, use_sample, use_adsorbate):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        # Standard return
        assert set(basic_pointisotherm.loading()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5])

        # Branch specified
        assert set(basic_pointisotherm.loading(branch='ads')) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        # Loading unit specified
        assert basic_pointisotherm.loading(branch='ads', loading_unit='mol')[
            0] == pytest.approx(0.001, 1e-5)

        # Loading basis specified
        assert basic_pointisotherm.loading(branch='ads',
                                           loading_basis='volume',
                                           loading_unit='cm3')[0] == pytest.approx(0.8764, 1e-3)

        # Adsorbent unit specified
        assert basic_pointisotherm.loading(branch='ads', adsorbent_unit='kg')[
            0] == pytest.approx(1000, 1e-3)

        # Adsorbent basis specified
        assert basic_pointisotherm.loading(branch='ads',
                                           adsorbent_basis='volume',
                                           adsorbent_unit='cm3')[0] == pytest.approx(10, 1e-3)

        # All specified
        assert numpy.isclose(basic_pointisotherm.loading(branch='ads',
                                                         loading_unit='kg',
                                                         loading_basis='mass',
                                                         adsorbent_unit='m3',
                                                         adsorbent_basis='volume')[
            0], 280.1, 0.1, 0.1)

        # Range specified
        assert set(basic_pointisotherm.loading(branch='ads', min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # Indexed option specified
        assert basic_pointisotherm.loading(indexed=True).equals(pandas.Series(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5]
        ))

        return

    def test_isotherm_ret_other_data(self, basic_pointisotherm):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        other_key = "enthalpy"

        # Standard return
        assert set(basic_pointisotherm.other_data(other_key)) == set([
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0])

        # Branch specified
        assert set(basic_pointisotherm.other_data(other_key, branch='ads')
                   ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        # Range specified
        assert set(basic_pointisotherm.other_data(other_key, min_range=3, max_range=4.5)
                   ) == set([4.0, 4.0])

        # Indexed option specified
        assert basic_pointisotherm.other_data(other_key, indexed=True).equals(pandas.Series(
            [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0]
        ))

        return

##########################

    @pytest.mark.parametrize('inp, expected, parameters', [
        (1, 1, dict()),
        (1, 1, dict(branch='ads')),
        (100000, 1, dict(pressure_unit='Pa')),
        (0.5, 3.89137, dict(pressure_mode='relative')),
        (1, 0.001, dict(loading_unit='mol')),
        (1, 0.87648, dict(loading_basis='volume', loading_unit='cm3')),
        (1, 1000, dict(adsorbent_unit='kg')),
        (1, 10, dict(adsorbent_basis='volume', adsorbent_unit='cm3')),
        (0.5, 1090.11, dict(pressure_unit='Pa',
                            pressure_mode='relative',
                            loading_unit='kg',
                            loading_basis='mass',
                            adsorbent_unit='m3',
                            adsorbent_basis='volume')),
        (10, 20.0, dict(interp_fill=(0, 20))),
        (1, 1, dict(interpolation_type='slinear')),
    ])
    def test_isotherm_ret_loading_at(self, basic_pointisotherm, use_sample, use_adsorbate,
                                     inp, parameters, expected):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        assert numpy.isclose(basic_pointisotherm.loading_at(
            inp, **parameters), expected, 1e-5)

        return

    @pytest.mark.parametrize('inp, expected, parameters', [
        (1, 1, dict()),
        (4, 4, dict(branch='des')),
        (1, 100000, dict(pressure_unit='Pa')),
        (3.89137, 0.5, dict(pressure_mode='relative')),
        (0.02808, 1.00237, dict(loading_basis='mass', loading_unit='g')),
        (1000, 1, dict(adsorbent_unit='kg')),
        (10, 1, dict(adsorbent_basis='volume', adsorbent_unit='cm3')),
        (1.08948, 0.499711, dict(pressure_unit='Pa',
                                 pressure_mode='relative',
                                 loading_unit='g',
                                 loading_basis='mass',
                                 adsorbent_unit='cm3',
                                 adsorbent_basis='volume')),
        (10, 20.0, dict(interp_fill=(0, 20))),
        (1, 1, dict(interpolation_type='slinear')),
    ])
    def test_isotherm_ret_pressure_at(self, basic_pointisotherm, use_sample, use_adsorbate,
                                      inp, parameters, expected):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        assert numpy.isclose(basic_pointisotherm.pressure_at(
            inp, **parameters), expected, 1e-5)

        return

    @pytest.mark.parametrize('inp, expected, parameters', [
        (1, 1, dict()),
        (1, 1, dict(branch='ads')),
        (100000, 1, dict(pressure_unit='Pa')),
        (0.5, 3.89137, dict(pressure_mode='relative')),
    ])
    def test_isotherm_spreading_pressure_at(self, basic_pointisotherm, use_adsorbate,
                                            inp, parameters, expected):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        assert numpy.isclose(basic_pointisotherm.spreading_pressure_at(
            inp, **parameters), expected, 1e-5)

        return

##########################

    @pytest.mark.parametrize('unit, multiplier', [
                            ('bar', 1),
                            ('Pa', 1e5),
        pytest.param("bad_unit", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_pressure(self, basic_pointisotherm, isotherm_data, unit, multiplier):
        """Checks that the pressure conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_pressure(unit_to=unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('mode, multiplier', [
                            ('relative', 1 / 7.7827),
                            ('absolute', 1),
        pytest.param("bad_mode", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_pressure_mode(self, basic_pointisotherm, use_adsorbate,
                                            isotherm_data, mode, multiplier):
        """Checks that the pressure mode conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_pressure(mode_to=mode)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('unit, multiplier', [
                            ('mmol', 1),
                            ('mol', 1e-3),
                            ('cm3(STP)', 22.414),
        pytest.param("bad_unit", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_loading_unit(self, basic_pointisotherm, isotherm_data, unit, multiplier):
        """Checks that the loading conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_loading(unit_to=unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('basis, unit,multiplier', [
                            ('molar', 'mmol', 1),
                            ('mass', 'g', 0.028),
        pytest.param("bad_mode", 'unit', 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_loading_basis(self, basic_pointisotherm, use_sample,
                                            isotherm_data, basis, unit, multiplier):
        """Checks that the loading basis conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_loading(basis_to=basis, unit_to=unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('unit, multiplier', [
                            ('g', 1),
                            ('kg', 1000),
        pytest.param("bad_unit", 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_adsorbent_unit(self, basic_pointisotherm, isotherm_data, unit, multiplier):
        """Checks that the loading conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_adsorbent(unit_to=unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @pytest.mark.parametrize('basis, unit, multiplier', [
                            ('mass', 'g', 1),
                            ('volume', 'cm3', 10),
        pytest.param("bad_mode", 'unit', 1,
                                marks=pytest.mark.xfail),
    ])
    def test_isotherm_convert_adsorbent_basis(self, basic_pointisotherm, use_sample,
                                              isotherm_data, basis, unit, multiplier):
        """Checks that the loading basis conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_adsorbent(basis_to=basis, unit_to=unit)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.loading_key] * multiplier
        iso_converted = basic_pointisotherm.loading()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    @cleanup
    def test_isotherm_print_parameters(self, basic_pointisotherm):
        "Checks isotherm can print its own info"

        basic_pointisotherm.print_info(show=False)
