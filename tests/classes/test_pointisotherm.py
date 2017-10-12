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

    def test_isotherm_create(self):
        "Checks isotherm can be created from basic data"
        isotherm_param = {
            'sample_name': 'carbon',
            'sample_batch': 'X1',
            'adsorbate': 'nitrogen',
            't_exp': 77,
        }

        isotherm_data = pandas.DataFrame({
            'pressure': [1, 2, 3, 4, 5, 3, 2],
            'loading': [1, 2, 3, 4, 5, 3, 2]
        })

        isotherm = pygaps.PointIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            **isotherm_param
        )

        return isotherm

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        "Checks isotherm can be created from isotherm"

        isotherm_data = pandas.DataFrame({
            'pressure': [1, 2, 3, 4, 5, 3, 2],
            'loading': [1, 2, 3, 4, 5, 3, 2]
        })

        # regular creation
        isotherm = pygaps.PointIsotherm.from_isotherm(
            basic_isotherm,
            isotherm_data,
        )

        return isotherm

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

        return isotherm

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
        assert basic_pointisotherm.data().equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
        }))

        # adsorption branch
        assert basic_pointisotherm.data(branch='ads').equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        }))

        # desorption branch
        assert basic_pointisotherm.data(branch='des').equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [4.5, 2.5],
            basic_pointisotherm.loading_key: [4.5, 2.5],
            other_key: [4.0, 4.0],
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
        assert set(basic_pointisotherm.pressure(branch='ads', unit='Pa')) == set(
            [100000, 200000, 300000, 400000, 500000, 600000])

        # Mode specified
        assert basic_pointisotherm.pressure(branch='ads', mode='relative')[
            0] == pytest.approx(0.12849, 0.001)

        # Range specified
        assert set(basic_pointisotherm.pressure(branch='ads', min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # Indexed option specified
        assert basic_pointisotherm.pressure(indexed=True).equals(pandas.Series(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5]
        ))

        return

    def test_isotherm_ret_loading(self, basic_pointisotherm, use_sample):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        # Standard return
        assert set(basic_pointisotherm.loading()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5])

        # Branch specified
        assert set(basic_pointisotherm.loading(branch='ads')) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        # Unit specified
        assert basic_pointisotherm.loading(branch='ads', unit='mol')[
            0] == pytest.approx(0.001, 1e-5)

        # Basis specified
        assert basic_pointisotherm.loading(branch='ads', basis='volume')[
            0] == pytest.approx(0.1, 1e-5)

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

    def test_isotherm_ret_loading_at(self, basic_pointisotherm, use_sample, use_adsorbate):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        # Standard return
        loading = basic_pointisotherm.loading_at(1)
        assert loading == pytest.approx(1.0, 1e-5)

        # Branch specified
        loading_branch = basic_pointisotherm.loading_at(1, branch='ads')
        assert loading_branch == pytest.approx(1.0, 1e-5)

        # Loading unit specified
        loading_lunit = basic_pointisotherm.loading_at(1, loading_unit='mol')
        assert loading_lunit == pytest.approx(0.001, 1e-5)

        # Pressure unit specified
        loading_punit = basic_pointisotherm.loading_at(
            100000, pressure_unit='Pa')
        assert loading_punit == pytest.approx(1.0, 1e-5)

        # Basis specified
        loading_bads = basic_pointisotherm.loading_at(
            1, adsorbent_basis='volume')
        assert loading_bads == pytest.approx(0.1, 1e-5)

        # Mode specified
        loading_mode = basic_pointisotherm.loading_at(
            0.5, pressure_mode='relative')
        assert loading_mode == pytest.approx(3.89137, 1e-5)

        # Interp_fill specified
        loading_fill = basic_pointisotherm.loading_at(
            10, interp_fill=(0, 20))
        assert loading_fill == pytest.approx(20.0, 1e-5)

        # Interp_type specified
        loading_type = basic_pointisotherm.loading_at(
            1, interpolation_type='slinear')
        assert loading_type == pytest.approx(1.0, 1e-5)

        return

    def test_isotherm_spreading_pressure_at(self, basic_pointisotherm, use_adsorbate):
        """Checks that all the functions in pointIsotherm return their specified parameter"""

        # Standard return
        spressure = basic_pointisotherm.spreading_pressure_at(1)
        assert spressure == pytest.approx(1.0, 1e-5)

        # Branch specified
        bpressure = basic_pointisotherm.spreading_pressure_at(1, branch='ads')
        assert bpressure == pytest.approx(1.0, 1e-5)

        # Pressure unit specified
        spressure_punit = basic_pointisotherm.spreading_pressure_at(
            100000, pressure_unit='Pa')
        assert spressure_punit == pytest.approx(1.0, 1e-5)

        # Mode specified
        spressure_mode = basic_pointisotherm.spreading_pressure_at(
            0.5, pressure_mode='relative')
        assert spressure_mode == pytest.approx(3.89137, 1e-5)

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
    def test_isotherm_convert_loading_basis(self, basic_pointisotherm, use_sample,
                                            isotherm_data, basis, multiplier):
        """Checks that the loading basis conversion function work as expected"""

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
    def test_isotherm_convert_pressure_mode(self, basic_pointisotherm, use_adsorbate,
                                            isotherm_data, mode, multiplier):
        """Checks that the pressure mode conversion function work as expected"""

        # Do the conversion
        basic_pointisotherm.convert_mode_pressure(mode)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    def test_isotherm_loading_interpolation(self, basic_pointisotherm, use_sample):
        """Checks that the interpolation works as expected"""

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

    def test_isotherm_from_model(self, basic_pointisotherm):
        """Checks that the isotherm can be created from a model"""

        # Generate the model
        model = pygaps.ModelIsotherm.from_pointisotherm(
            basic_pointisotherm, model='Henry')

        # Try to generate the new isotherm
        pygaps.PointIsotherm.from_modelisotherm(model)

        # Based on new
        pygaps.PointIsotherm.from_modelisotherm(
            model, pressure_points=[1, 2, 3])

        # Based on new
        pygaps.PointIsotherm.from_modelisotherm(
            model, pressure_points=basic_pointisotherm)

    @cleanup
    def test_isotherm_print_parameters(self, basic_pointisotherm):
        "Checks isotherm can print its own info"

        basic_pointisotherm.print_info(show=False)
