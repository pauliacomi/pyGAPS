"""
This test module has tests relating to classes
"""

import pandas
import pytest

import pygaps


class TestAdsorbate(object):
    """
    Tests the adsorbate class
    """

    def test_adsorbate_created(self, adsorbate_data, basic_adsorbate):
        "Checks adsorbate can be created from test data"

        assert adsorbate_data == basic_adsorbate.to_dict()

        with pytest.raises(Exception):
            pygaps.Adsorbate({})

    def test_adsorbate_retreived_list(self, adsorbate_data, basic_adsorbate):
        "Checks adsorbate can be retrieved from master list"
        pygaps.data.GAS_LIST.append(basic_adsorbate)
        uploaded_adsorbate = pygaps.Adsorbate.from_list(
            adsorbate_data.get('nick'))

        assert adsorbate_data == uploaded_adsorbate.to_dict()

        with pytest.raises(Exception):
            pygaps.Adsorbate.from_list('noname')

    def test_adsorbate_get_properties(self, adsorbate_data, basic_adsorbate):
        "Checks if properties of a adsorbate can be located"

        assert basic_adsorbate.get_prop(
            'common_name') == adsorbate_data['properties'].get('common_name')
        assert basic_adsorbate.common_name(
        ) == adsorbate_data['properties'].get('common_name')

        name = basic_adsorbate.properties.pop('common_name')
        with pytest.raises(Exception):
            basic_adsorbate.common_name()
        basic_adsorbate.properties['common_name'] = name

    @pytest.mark.parametrize('calculated', [True, False])
    def test_adsorbate_named_props(self, adsorbate_data, basic_adsorbate, calculated):
        temp = 77.355
        assert basic_adsorbate.molar_mass(calculated) == pytest.approx(
            adsorbate_data['properties'].get('molar_mass'), 0.001)
        assert basic_adsorbate.saturation_pressure(temp, calculate=calculated) == pytest.approx(
            adsorbate_data['properties'].get('saturation_pressure'), 0.001)
        assert basic_adsorbate.surface_tension(temp, calculate=calculated) == pytest.approx(
            adsorbate_data['properties'].get('surface_tension'), 0.001)
        assert basic_adsorbate.liquid_density(temp, calculate=calculated) == pytest.approx(
            adsorbate_data['properties'].get('liquid_density'), 0.001)

    def test_adsorbate_print(self, basic_adsorbate):
        """Checks the printing is done"""

        print(basic_adsorbate)


class TestSample(object):
    """
    Tests the sample class
    """

    def test_sample_created(self, sample_data, basic_sample):
        "Checks sample can be created from test data"

        assert sample_data == basic_sample.to_dict()

        with pytest.raises(Exception):
            pygaps.Sample({})

    def test_sample_retreived_list(self, sample_data, basic_sample):
        "Checks sample can be retrieved from master list"
        pygaps.data.SAMPLE_LIST.append(basic_sample)
        uploaded_sample = pygaps.Sample.from_list(
            sample_data.get('name'),
            sample_data.get('batch'))

        assert sample_data == uploaded_sample.to_dict()

        with pytest.raises(Exception):
            pygaps.Sample.from_list('noname', 'nobatch')

    def test_sample_get_properties(self, sample_data, basic_sample):
        "Checks if properties of a sample can be located"

        assert basic_sample.get_prop(
            'density') == sample_data['properties'].get('density')

        density = basic_sample.properties.pop('density')
        with pytest.raises(Exception):
            basic_sample.get_prop(
                'density') == sample_data['properties'].get('density')
        basic_sample.properties['density'] = density

    def test_sample_print(self, basic_sample):
        """Checks the printing is done"""

        print(basic_sample)


class TestIsotherm(object):
    """
    Tests the parent isotherm object
    """

    def test_isotherm_created(self, basic_isotherm):
        "Checks isotherm can be created from test data"
        return basic_isotherm

    @pytest.mark.parametrize('missing_param',
                             ['sample_name', 'sample_batch', 't_exp', 'adsorbate'])
    def test_isotherm_miss_param(self, isotherm_parameters, missing_param):
        "Tests exception throw for missing required attributes"

        pressure_key = "pressure"
        loading_key = "loading"

        data = isotherm_parameters
        del data[missing_param]

        with pytest.raises(Exception):
            pygaps.classes.isotherm.Isotherm(
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
            pygaps.classes.isotherm.Isotherm(
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

        assert isotherm_parameters == basic_isotherm.to_dict()

    def test_isotherm_print_parameters(self, basic_isotherm):
        "Checks isotherm can print its own info"

        print(basic_isotherm)


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

        with pytest.raises(Exception):
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
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        }))
        assert isotherm.data(branch='ads').equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            other_key: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        }))
        assert isotherm.data(branch='des').equals(pandas.DataFrame({
            basic_pointisotherm.pressure_key: [4.0, 2.0],
            basic_pointisotherm.loading_key: [4.0, 2.0],
            other_key: [5.0, 5.0],
        }, index=[6, 7]))

        # pressure()
        assert set(isotherm.pressure()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
        assert set(isotherm.pressure(branch='ads')) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert set(isotherm.pressure(branch='des')) == set([4.0, 2.0])
        assert set(isotherm.pressure(min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # loading()
        assert set(isotherm.loading()) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
        assert set(isotherm.loading(branch='ads')) == set(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert set(isotherm.loading(branch='des')) == set([4.0, 2.0])
        assert set(isotherm.loading(min_range=2.3, max_range=5.0)) == set(
            [3.0, 4.0, 5.0])

        # other_data()
        assert set(isotherm.other_data(other_key)) == set([
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        assert set(isotherm.other_data(other_key, branch='ads')
                   ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        assert set(isotherm.other_data(
            other_key, branch='des')) == set([5.0, 5.0])

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
        pygaps.data.SAMPLE_LIST.append(basic_sample)

        # Do the conversion
        basic_pointisotherm.convert_mode_adsorbent(mode)

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
    def test_isotherm_convert_pressure_mode(self, basic_pointisotherm, basic_adsorbate,
                                            isotherm_data, mode, multiplier):
        """Checks that the pressure mode conversion function work as expected"""

        # Add sample to list
        pygaps.data.GAS_LIST.append(basic_adsorbate)

        # Do the conversion
        basic_pointisotherm.convert_mode_pressure(mode)

        # Convert initial data
        converted = isotherm_data[basic_pointisotherm.pressure_key] * multiplier
        iso_converted = basic_pointisotherm.pressure()

        # Check if one datapoint is now as expected
        assert iso_converted[0] == pytest.approx(converted[0], 0.01)

    def test_isotherm_print_parameters(self, basic_pointisotherm):
        "Checks isotherm can print its own info"

        basic_pointisotherm.print_info()


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

        loading_key = 'loading'
        pressure_key = 'presure'
        isotherm_data['loading'] = data

        # pygaps.ModelIsotherm.from_isotherm(
        #     basic_isotherm,
        #     isotherm_data[:6],
        #     loading_key,
        #     pressure_key,
        #     model)
