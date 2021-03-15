"""Tests relating to the PointIsotherm class."""

import pandas
import pytest
from matplotlib.testing.decorators import cleanup
from pandas.testing import assert_series_equal

import pygaps
import pygaps.utilities.exceptions as pgEx

from .conftest import LOADING_AT_PARAM
from .conftest import LOADING_PARAM
from .conftest import PRESSURE_AT_PARAM
from .conftest import PRESSURE_PARAM


@pytest.mark.core
class TestPointIsotherm():
    """Test the PointIsotherm class."""

    ##########################

    def test_isotherm_create(self):
        """Check isotherm can be created from basic data."""

        isotherm_param = {
            'material': 'carbon',
            'adsorbate': 'nitrogen',
            'temperature': 77,
        }
        pressure = [1, 2, 3, 4, 5, 3, 2]
        loading = [1, 2, 3, 4, 5, 3, 2]

        pygaps.PointIsotherm(
            pressure=pressure,
            loading=loading,
            **isotherm_param,
        )

        pygaps.PointIsotherm(
            isotherm_data=pandas.DataFrame({
                'pressure': pressure,
                'loading': loading
            }),
            pressure_key='pressure',
            loading_key='loading',
            **isotherm_param,
        )

        # Wrong branch
        with pytest.raises(pgEx.ParameterError):
            pygaps.PointIsotherm(
                pressure=pressure,
                loading=loading,
                branch='random',
                **isotherm_param,
            )

    def test_isotherm_id(self, basic_pointisotherm):
        """Check isotherm id works as intended."""

        iso_id = basic_pointisotherm.iso_id
        basic_pointisotherm.new_param = 'changed'
        assert iso_id != basic_pointisotherm.iso_id
        basic_pointisotherm.data_raw = basic_pointisotherm.data_raw[:5]
        assert iso_id != basic_pointisotherm.iso_id

    @pytest.mark.parametrize('missing_key', ['loading_key', 'pressure_key'])
    def test_isotherm_miss_key(
        self,
        isotherm_data,
        isotherm_parameters,
        missing_key,
    ):
        """Tests exception throw for missing data primary key (loading/pressure)."""
        keys = dict(
            pressure_key="pressure",
            loading_key="loading",
        )

        del keys[missing_key]

        with pytest.raises(pgEx.ParameterError):
            pygaps.PointIsotherm(
                isotherm_data=isotherm_data,
                loading_key=keys.get('loading_key'),
                pressure_key=keys.get('pressure_key'),
                **isotherm_parameters
            )

    @pytest.mark.parametrize(
        'branch, expected', [
            ('guess', 4.5),
            ('des', 1.0),
            ([False, False, True, True, True, True, True, True], 3.0),
        ]
    )
    def test_isotherm_create_branches(
        self,
        isotherm_data,
        isotherm_parameters,
        branch,
        expected,
    ):
        """Tests if isotherm branches are well specified."""
        isotherm = pygaps.PointIsotherm(
            isotherm_data=isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            other_keys=['enthalpy'],
            branch=branch,
            **isotherm_parameters
        )
        assert isotherm.pressure(branch='des')[0] == expected

    def test_isotherm_existing_branches(
        self,
        isotherm_parameters,
        isotherm_data,
    ):
        """Tests if isotherm branches are well specified."""
        isotherm_datab = isotherm_data.copy()
        isotherm_datab['branch'] = [
            False, False, True, True, True, True, True, True
        ]
        isotherm = pygaps.PointIsotherm(
            isotherm_data=isotherm_datab,
            loading_key='loading',
            pressure_key='pressure',
            other_keys=['enthalpy'],
            **isotherm_parameters
        )
        assert isotherm.pressure(branch='des')[0] == 3.0

    def test_isotherm_equality(
        self,
        isotherm_parameters,
        isotherm_data,
        basic_pointisotherm,
    ):
        """Check isotherm id's are unique"""

        isotherm = pygaps.PointIsotherm(
            isotherm_data=isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            other_keys=['enthalpy'],
            **isotherm_parameters
        )

        assert isotherm == basic_pointisotherm

        isotherm.temperature = 0
        assert isotherm != basic_pointisotherm

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        """Check isotherm can be created from isotherm."""
        pygaps.PointIsotherm.from_isotherm(
            basic_isotherm,
            pressure=[1, 2, 3, 4, 5, 3, 2],
            loading=[1, 2, 3, 4, 5, 3, 2],
        )

    def test_isotherm_create_from_modelisotherm(
        self,
        basic_modelisotherm,
        basic_pointisotherm,
    ):
        """Check isotherm can be created from isotherm."""

        # regular creation
        isotherm = pygaps.PointIsotherm.from_modelisotherm(
            basic_modelisotherm, pressure_points=None
        )
        assert isotherm.loading_at(3) == pytest.approx(
            basic_modelisotherm.loading_at(3)
        )

        # Specifying points
        isotherm = pygaps.PointIsotherm.from_modelisotherm(
            basic_modelisotherm, pressure_points=[1, 2, 3, 4]
        )
        assert isotherm.loading_at(3) == pytest.approx(
            basic_modelisotherm.loading_at(3)
        )

        # Specifying isotherm
        isotherm = pygaps.PointIsotherm.from_modelisotherm(
            basic_modelisotherm, pressure_points=basic_pointisotherm
        )
        assert isotherm.loading_at(3) == pytest.approx(
            basic_modelisotherm.loading_at(3)
        )

    ##########################

    def test_isotherm_ret_has_branch(
        self,
        basic_pointisotherm,
    ):
        """Check that all the functions in pointIsotherm return their specified parameter."""
        assert basic_pointisotherm.has_branch(branch='ads')
        assert basic_pointisotherm.has_branch(branch='des')

    def test_isotherm_ret_data(
        self,
        basic_pointisotherm,
    ):
        """Check that all the functions in pointIsotherm return their specified parameter."""
        # all data
        assert basic_pointisotherm.data().drop('branch', axis=1).equals(
            pandas.DataFrame({
                basic_pointisotherm.pressure_key:
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
                basic_pointisotherm.loading_key:
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
                "enthalpy": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
            })
        )

        # adsorption branch
        assert basic_pointisotherm.data(
            branch='ads'
        ).drop('branch', axis=1).equals(
            pandas.DataFrame({
                basic_pointisotherm.pressure_key:
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                basic_pointisotherm.loading_key:
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "enthalpy": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            })
        )

        # desorption branch
        assert basic_pointisotherm.data(
            branch='des'
        ).drop('branch', axis=1).equals(
            pandas.DataFrame({
                basic_pointisotherm.pressure_key: [4.5, 2.5],
                basic_pointisotherm.loading_key: [4.5, 2.5],
                "enthalpy": [4.0, 4.0],
            },
                             index=[6, 7])
        )

        # Wrong branch
        with pytest.raises(pgEx.ParameterError):
            basic_pointisotherm.data(branch='random')

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            (4.5, {
                'branch': 'des'
            }),  # Branch specified
        ] + PRESSURE_PARAM
    )
    def test_isotherm_ret_pressure(
        self,
        use_adsorbate,
        basic_pointisotherm,
        expected,
        parameters,
    ):
        """Check that the pressure functions of a pointIsotherm return their specified parameter."""
        assert basic_pointisotherm.pressure(
            **parameters
        )[0] == pytest.approx(expected, 1e-5)

    def test_isotherm_ret_pressure_indexed(
        self,
        basic_pointisotherm,
    ):
        """Indexed option specified."""
        assert_series_equal(
            basic_pointisotherm.loading(branch='ads', indexed=True),
            pandas.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], name='loading')
        )

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            (4.5, {
                'branch': 'des'
            }),  # Branch specified
        ] + LOADING_PARAM
    )
    def test_isotherm_ret_loading(
        self,
        use_adsorbate,
        use_material,
        basic_pointisotherm,
        expected,
        parameters,
    ):
        """Check that the loading functions of a pointIsotherm return their specified parameter."""
        assert basic_pointisotherm.loading(
            **parameters
        )[0] == pytest.approx(expected, 1e-5)

    def test_isotherm_ret_loading_indexed(
        self,
        basic_pointisotherm,
    ):
        """Indexed option specified."""
        assert basic_pointisotherm.loading(indexed=True).equals(
            pandas.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5])
        )

    def test_isotherm_ret_other_data(
        self,
        basic_pointisotherm,
    ):
        """Check that all the functions in pointIsotherm return their specified parameter."""

        other_key = "enthalpy"

        # Standard return
        assert set(basic_pointisotherm.other_data(other_key)
                   ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0])

        # Branch specified
        assert set(basic_pointisotherm.other_data(other_key, branch='ads')
                   ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        # Range specified
        assert set(basic_pointisotherm.other_data(other_key, limits=(3, 4.5))
                   ) == set([4.0, 4.0])

        # Indexed option specified
        assert basic_pointisotherm.other_data(other_key, indexed=True).equals(
            pandas.Series([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0])
        )

        # Error
        with pytest.raises(pgEx.ParameterError):
            basic_pointisotherm.other_data('random')

    ##########################

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        [
            (10, 20.0, {
                'interp_fill': (0, 20)
            }),  # Interpolate limit
            (1.5, 1.5, {
                'interpolation_type': 'slinear'
            }),  # Interpolate type
        ] + PRESSURE_AT_PARAM
    )
    def test_isotherm_ret_pressure_at(
        self,
        use_material,
        use_adsorbate,
        basic_pointisotherm,
        inp,
        parameters,
        expected,
    ):
        """Check the PointIsotherm pressure_at(loading) function."""
        assert basic_pointisotherm.pressure_at(
            inp,
            **parameters,
        ) == pytest.approx(expected, 1e-5)

    @pytest.mark.parametrize(
        'inp, expected, parameters', [
            (10, 20.0, {
                'interp_fill': (0, 20)
            }),
            (1, 1, {
                'interpolation_type': 'slinear'
            }),
        ] + LOADING_AT_PARAM
    )
    def test_isotherm_ret_loading_at(
        self,
        use_material,
        use_adsorbate,
        basic_pointisotherm,
        inp,
        parameters,
        expected,
    ):
        """Returning a loading at a particular point specified parameter."""
        assert basic_pointisotherm.loading_at(
            inp,
            **parameters,
        ) == pytest.approx(expected, 1e-5)

    @pytest.mark.parametrize(
        'inp, expected, parameters', [
            (1, 1, dict()),
            (1, 1, dict(branch='ads')),
            (100000, 1, dict(pressure_unit='Pa')),
            (0.5, 3.89137, dict(pressure_mode='relative')),
        ]
    )
    def test_isotherm_spreading_pressure_at(
        self,
        use_adsorbate,
        basic_pointisotherm,
        inp,
        parameters,
        expected,
    ):
        """Check the PointIsotherm spreading pressure calculation."""
        assert basic_pointisotherm.spreading_pressure_at(
            inp, **parameters
        ) == pytest.approx(expected, 1e-5)

    ##########################

    @pytest.mark.parametrize(
        'parameters', [
            ({
                "pressure_mode": "absolute",
                "pressure_unit": "Pa",
            }),
            ({
                "loading_basis": "mass",
                "loading_unit": "g",
            }),
            ({
                "material_basis": "volume",
                "material_unit": "cm3",
            }),
            ({
                "pressure_mode": "absolute",
                "pressure_unit": "Pa",
                "loading_basis": "mass",
                "loading_unit": "g",
                "material_basis": "volume",
                "material_unit": "cm3",
            }),
        ]
    )
    def test_isotherm_convert(
        self,
        use_adsorbate,
        use_material,
        basic_pointisotherm,
        parameters,
    ):
        """Check convenience conversion function."""
        # Do the conversion
        basic_pointisotherm.convert(**parameters)

        # Check for good parameters as well
        for p in [
            'pressure_mode',
            'pressure_unit',
            'loading_basis',
            'loading_unit',
            'material_basis',
            'material_unit',
        ]:
            if p in parameters:
                assert getattr(basic_pointisotherm, p) == parameters[p]

    @pytest.mark.parametrize(
        'expected, parameters', [
            (1, {
                "unit_to": "bar",
            }),
            (1e5, {
                "mode_to": "absolute",
                "unit_to": "Pa",
            }),
            (0.12849, {
                "mode_to": "relative",
            }),
            (12.849, {
                "mode_to": "relative%",
            }),
            pytest.param(1, {"unit_to": "bad_unit"}, marks=pytest.mark.xfail),
            pytest.param(1, {"mode_to": "bad_mode"}, marks=pytest.mark.xfail),
        ]
    )
    def test_isotherm_convert_pressure(
        self,
        use_adsorbate,
        basic_pointisotherm,
        expected,
        parameters,
    ):
        """Check that the pressure conversion function works as expected."""

        # Do the conversion
        basic_pointisotherm.convert_pressure(**parameters)
        converted = basic_pointisotherm.pressure()[0]

        # Check if one datapoint is now as expected
        assert converted == pytest.approx(expected, 0.01)

        # Check for good parameters as well
        if 'mode_to' in parameters:
            assert basic_pointisotherm.pressure_mode == parameters['mode_to']
        if 'unit_to' in parameters:
            assert basic_pointisotherm.pressure_unit == parameters['unit_to']

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            (1, {
                "basis_to": "molar",
                "unit_to": "mmol",
            }),
            (1e-3, {
                "unit_to": "mol",
            }),
            (22.414, {
                "unit_to": "cm3(STP)",
            }),
            (0.028, {
                "basis_to": "mass",
                "unit_to": "g",
            }),
            (0.876484, {
                "basis_to": "volume",
                "unit_to": "cm3",
            }),
            (0.0280135, {
                'basis_to': 'fraction',
            }),  # Fractional weight (will be 1/1000 mol * 28.01 g/mol)
            (2.80134, {
                'basis_to': 'percent',
            }),  # Percent weight
            pytest.param(1, {"unit_to": "bad_unit"}, marks=pytest.mark.xfail),
            pytest.param(
                1, {"basis_to": "bad_basis"}, marks=pytest.mark.xfail
            ),
        ]
    )
    def test_isotherm_convert_loading(
        self,
        use_adsorbate,
        use_material,
        basic_pointisotherm,
        expected,
        parameters,
    ):
        """Check that the loading conversion function works as expected."""

        # Do the conversion
        basic_pointisotherm.convert_loading(**parameters)
        converted = basic_pointisotherm.loading()[0]

        # Check if one datapoint is now as expected
        assert converted == pytest.approx(expected, 0.01)

        # Check for good parameters as well
        if 'basis_to' in parameters:
            assert basic_pointisotherm.loading_basis == parameters['basis_to']
        if 'unit_to' in parameters:
            assert basic_pointisotherm.loading_unit == parameters['unit_to']

    @pytest.mark.parametrize(
        'expected, parameters', [
            (1, {
                "basis_to": "mass",
                "unit_to": "g",
            }),
            (1000, {
                "unit_to": "kg",
            }),
            (0.01, {
                "basis_to": "molar",
                "unit_to": "mmol",
            }),
            (2, {
                "basis_to": "volume",
                "unit_to": "cm3",
            }),
            pytest.param(1, {"unit_to": "bad_unit"}, marks=pytest.mark.xfail),
            pytest.param(
                1, {"basis_to": "bad_basis"}, marks=pytest.mark.xfail
            ),
        ]
    )
    def test_isotherm_convert_material(
        self,
        use_adsorbate,
        use_material,
        basic_pointisotherm,
        expected,
        parameters,
    ):
        """Check that the loading conversion function work as expected."""

        # Do the conversion
        basic_pointisotherm.convert_material(**parameters)
        converted = basic_pointisotherm.loading()[0]

        # Check if one datapoint is now as expected
        assert converted == pytest.approx(expected, 0.01)

        # Check for good parameters as well
        if 'basis_to' in parameters:
            assert basic_pointisotherm.material_basis == parameters['basis_to']
        if 'unit_to' in parameters:
            assert basic_pointisotherm.material_unit == parameters['unit_to']

    def test_isotherm_convert_complex(
        self,
        use_adsorbate,
        use_material,
        basic_pointisotherm,
    ):
        """Some more complex conversions are checked here."""

        # Convert from mmol/g -> wt% (g/g)
        basic_pointisotherm.convert_loading(basis_to='fraction')
        assert (
            basic_pointisotherm.loading()[0] == pytest.approx(0.028, 0.001)
        )
        # Convert from wt% (g/g) to vol% (cm3/cm3)
        basic_pointisotherm.convert_material(basis_to='volume', unit_to='cm3')
        assert (
            basic_pointisotherm.loading()[0] == pytest.approx(1.7529, 0.001)
        )
        # Convert from vol% (cm3/cm3) to vol% (m3/m3)
        basic_pointisotherm.convert_material(basis_to='volume', unit_to='m3')
        assert (
            basic_pointisotherm.loading()[0] == pytest.approx(1.7529, 0.001)
        )
        # Convert from vol% (m3/m3) to mol% (mol/mol)
        basic_pointisotherm.convert_material(basis_to='molar', unit_to='mol')
        assert (basic_pointisotherm.loading()[0] == pytest.approx(0.01, 0.001))
        # Convert from mol% (mol/mol) to mmol/mol
        basic_pointisotherm.convert_loading(basis_to='molar', unit_to='mmol')
        assert (basic_pointisotherm.loading()[0] == pytest.approx(10, 0.001))
        # Convert from mmol/mol to mmol/g
        basic_pointisotherm.convert_material(basis_to='mass', unit_to='g')
        assert (basic_pointisotherm.loading()[0] == pytest.approx(1, 0.001))

    ##########################

    @cleanup
    def test_isotherm_print_parameters(self, basic_pointisotherm):
        """Check isotherm can print its own info."""

        print(basic_pointisotherm)
        basic_pointisotherm.plot()
        basic_pointisotherm.print_info()
