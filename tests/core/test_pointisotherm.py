"""Tests relating to the PointIsotherm class."""

import numpy
import pandas
import pytest
from pandas.testing import assert_series_equal

import pygaps
import pygaps.parsing as pgp
import pygaps.units.converter_mode as converters
import pygaps.utilities.exceptions as pgEx
from pygaps.modelling import model_from_dict

from ..test_utils import mpl_cleanup
from .conftest import LOADING_AT_PARAM
from .conftest import LOADING_PARAM
from .conftest import PRESSURE_AT_PARAM
from .conftest import PRESSURE_PARAM


@pytest.mark.core
class TestPointIsotherm:
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
            isotherm_data=pandas.DataFrame({'pressure': pressure, 'loading': loading}),
            pressure_key='pressure',
            loading_key='loading',
            **isotherm_param,
        )

        pygaps.PointIsotherm(
            isotherm_data=pandas.DataFrame(
                {
                    'pressure': pressure,
                    'loading': loading,
                    'extra_data': [f"load{e}" for e in range(len(loading))],
                }
            ),
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
                **isotherm_parameters,
            )

    @pytest.mark.parametrize(
        'branch, expected',
        [
            ('guess', 4.5),
            ('des', 1.0),
            ([False, False, True, True, True, True, True, True], 3.0),
        ],
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
            isotherm_data=isotherm_data, loading_key='loading', pressure_key='pressure', branch=branch, **isotherm_parameters
        )
        assert isotherm.pressure(branch='des')[0] == expected

    def test_isotherm_existing_branches(
        self,
        isotherm_parameters,
        isotherm_data,
    ):
        """Tests if isotherm branches are well specified."""
        isotherm_datab = isotherm_data.copy()
        isotherm_datab['branch'] = [False, False, True, True, True, True, True, True]
        isotherm = pygaps.PointIsotherm(isotherm_data=isotherm_datab, loading_key='loading', pressure_key='pressure', **isotherm_parameters)
        assert isotherm.pressure(branch='des')[0] == 3.0

    @pytest.mark.parametrize('index', [None, [10, 20, 30], ['same', 'same', 'other']])
    @pytest.mark.parametrize('branch, expected', [('guess', [1, 1, 1]), ('ads', [0, 0, 0]), ('des', [1, 1, 1])])
    def test_descending_dataframe_branches(self, index, branch, expected, isotherm_parameters):
        data = pandas.DataFrame({'pressure': [3, 2, 1], 'loading': [6, 4, 2]}, index=index)
        original = data.copy(deep=True)
        isotherm = pygaps.PointIsotherm(
            isotherm_data=data,
            pressure_key='pressure',
            loading_key='loading',
            branch=branch,
            **isotherm_parameters,
        )
        assert isotherm.data_raw['branch'].tolist() == expected
        assert isotherm.data_raw.index.equals(data.index)
        pandas.testing.assert_frame_equal(data, original)

    def test_descending_dataframe_explicit_branch_column(self, isotherm_parameters):
        data = pandas.DataFrame({'pressure': [3, 2, 1], 'loading': [6, 4, 2], 'branch': [0, 0, 0]})
        isotherm = pygaps.PointIsotherm(
            isotherm_data=data,
            pressure_key='pressure',
            loading_key='loading',
            branch='guess',
            **isotherm_parameters,
        )
        assert isotherm.data_raw['branch'].tolist() == [0, 0, 0]

    def test_isotherm_equality(
        self,
        isotherm_parameters,
        isotherm_data,
        basic_pointisotherm,
    ):
        """Check isotherm id's are unique"""

        isotherm = pygaps.PointIsotherm(isotherm_data=isotherm_data, loading_key='loading', pressure_key='pressure', **isotherm_parameters)

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
        isotherm = pygaps.PointIsotherm.from_modelisotherm(basic_modelisotherm, pressure_points=None)
        assert isotherm.loading_at(3) == pytest.approx(basic_modelisotherm.loading_at(3))

        # Specifying points
        isotherm = pygaps.PointIsotherm.from_modelisotherm(basic_modelisotherm, pressure_points=[1, 2, 3, 4])
        assert isotherm.loading_at(3) == pytest.approx(basic_modelisotherm.loading_at(3))

        # Specifying isotherm
        isotherm = pygaps.PointIsotherm.from_modelisotherm(basic_modelisotherm, pressure_points=basic_pointisotherm)
        assert isotherm.loading_at(3) == pytest.approx(basic_modelisotherm.loading_at(3))

    ##########################

    def test_isotherm_ret_has_branch(
        self,
        basic_pointisotherm,
    ):
        """Check that all the functions in pointIsotherm return their specified parameter."""
        assert basic_pointisotherm.has_branch(branch='ads')
        assert basic_pointisotherm.has_branch(branch='des')

    @pytest.mark.parametrize('branch', [None, 'all', 'ads', 'des'])
    def test_data_returns_independent_copy(self, basic_pointisotherm, branch):
        point = basic_pointisotherm
        before = point.data_raw.copy(deep=True)
        edited = point.data(branch=branch)
        edited.loc[:, point.loading_key] = 100
        edited.loc[:, 'branch'] = 1
        pandas.testing.assert_frame_equal(point.data_raw, before)

    @pytest.mark.parametrize('column', ['pressure', 'loading', 'branch'])
    @pytest.mark.parametrize('direct', [False, True])
    def test_data_updates_refresh_interpolators(self, isotherm_parameters, column, direct):
        point = pygaps.PointIsotherm(
            pressure=[0., 1., 2., 3.], loading=[0., 1., 2., 30.], branch='ads', **isotherm_parameters
        )
        point.loading_at(1.5)
        point.pressure_at(1.5)
        edited = point.data_raw if direct else point.data()
        if column == 'loading':
            edited.loc[2, column] = 20
            expected_loading, expected_pressure = 10.5, 1 + 0.5 / 19
        elif column == 'pressure':
            edited.loc[2, column] = 2.5
            expected_loading, expected_pressure = 1 + 0.5 / 1.5, 1.75
        else:
            edited.loc[1, column] = 1
            edited.loc[2, 'loading'] = 4
            expected_loading, expected_pressure = 3, 0.75
        if direct:
            point.reset_interpolators()
        else:
            point.update_data(edited)
            edited.loc[:, 'loading'] = 100

        assert point.l_interpolator is None
        assert point.p_interpolator is None
        assert point.loading_at(1.5) == pytest.approx(expected_loading)
        assert point.pressure_at(1.5) == pytest.approx(expected_pressure)

    @pytest.mark.parametrize('invalid', ['type', 'missing', 'duplicates', 'branch'])
    def test_update_data_invalid_preserves_state(self, basic_pointisotherm, invalid):
        point = basic_pointisotherm
        point.loading_at(2)
        point.pressure_at(2)
        before = point.data_raw.copy(deep=True)
        caches = (point.l_interpolator, point.p_interpolator)
        edited = point.data()
        if invalid == 'type':
            edited = []
        elif invalid == 'missing':
            edited = edited.drop(columns=['branch'])
        elif invalid == 'duplicates':
            edited = pandas.concat([edited, edited[['branch']]], axis=1)
        else:
            edited.loc[0, 'branch'] = 2
        with pytest.raises(pgEx.ParameterError):
            point.update_data(edited)
        pandas.testing.assert_frame_equal(point.data_raw, before)
        assert (point.l_interpolator, point.p_interpolator) == caches

    def test_isotherm_ret_data(
        self,
        basic_pointisotherm,
    ):
        """Check that all the functions in pointIsotherm return their specified parameter."""
        # all data
        assert (
            basic_pointisotherm.data()
            .drop('branch', axis=1)
            .equals(
                pandas.DataFrame(
                    {
                        basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
                        basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5],
                        "enthalpy": [5.2, 5.1, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0],
                        "text_data": ["a", "b", "c", "d", "e", "f", "g", "h"],
                    }
                )
            )
        )

        # adsorption branch
        assert (
            basic_pointisotherm.data(branch='ads')
            .drop('branch', axis=1)
            .equals(
                pandas.DataFrame(
                    {
                        basic_pointisotherm.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                        basic_pointisotherm.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                        "enthalpy": [5.2, 5.1, 5.0, 5.0, 5.0, 5.0],
                        "text_data": ["a", "b", "c", "d", "e", "f"],
                    }
                )
            )
        )

        # desorption branch
        assert (
            basic_pointisotherm.data(branch='des')
            .drop('branch', axis=1)
            .equals(
                pandas.DataFrame(
                    {
                        basic_pointisotherm.pressure_key: [4.5, 2.5],
                        basic_pointisotherm.loading_key: [4.5, 2.5],
                        "enthalpy": [4.0, 4.0],
                        "text_data": ["g", "h"],
                    },
                    index=[6, 7],
                )
            )
        )

        # Wrong branch
        with pytest.raises(pgEx.ParameterError):
            basic_pointisotherm.data(branch='random')

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            (4.5, {'branch': 'des'}),  # Branch specified
        ]
        + PRESSURE_PARAM,
    )
    def test_isotherm_ret_pressure(
        self,
        use_adsorbate,
        basic_pointisotherm,
        expected,
        parameters,
    ):
        """Check that the pressure functions of a pointIsotherm return their specified parameter."""
        assert basic_pointisotherm.pressure(**parameters)[0] == pytest.approx(expected, 1e-5)

    def test_isotherm_ret_pressure_indexed(
        self,
        basic_pointisotherm,
    ):
        """Indexed option specified."""
        assert_series_equal(
            basic_pointisotherm.loading(branch='ads', indexed=True), pandas.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], name='loading')
        )

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            (4.5, {'branch': 'des'}),  # Branch specified
        ]
        + LOADING_PARAM,
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
        assert basic_pointisotherm.loading(**parameters)[0] == pytest.approx(expected, 1e-5)

    def test_isotherm_ret_loading_indexed(
        self,
        basic_pointisotherm,
    ):
        """Indexed option specified."""
        assert basic_pointisotherm.loading(indexed=True).equals(pandas.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.5, 2.5]))

    def test_isotherm_ret_other_data(
        self,
        basic_pointisotherm,
    ):
        """Check that all the functions in pointIsotherm return their specified parameter."""

        other_key = "enthalpy"

        # Standard return
        assert set(basic_pointisotherm.other_data(other_key)) == set([5.2, 5.1, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0])

        # Branch specified
        assert set(basic_pointisotherm.other_data(other_key, branch='ads')) == set([5.2, 5.1, 5.0, 5.0, 5.0, 5.0])

        # Range specified
        assert set(basic_pointisotherm.other_data(other_key, limits=(3, 4.5))) == set([4.0, 4.0])

        # Indexed option specified
        assert basic_pointisotherm.other_data(other_key, indexed=True).equals(pandas.Series([5.2, 5.1, 5.0, 5.0, 5.0, 5.0, 4.0, 4.0]))

        # Error
        with pytest.raises(pgEx.ParameterError):
            basic_pointisotherm.other_data('random')

    ##########################

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        [
            (10, 20.0, {'interp_fill': (0, 20)}),  # Interpolate limit
            (1.5, 1.5, {'interpolation_type': 'slinear'}),  # Interpolate type
        ]
        + PRESSURE_AT_PARAM,
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
        'inp, expected, parameters',
        [
            (10, 20.0, {'interp_fill': (0, 20)}),
            (1, 1, {'interpolation_type': 'slinear'}),
        ]
        + LOADING_AT_PARAM,
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
        'inp, expected, parameters',
        [
            (1, 1, dict()),
            (1, 1, dict(branch='ads')),
            (100000, 1, dict(pressure_unit='Pa')),
            (0.5, 3.89137, dict(pressure_mode='relative')),
        ],
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
        assert basic_pointisotherm.spreading_pressure_at(inp, **parameters) == pytest.approx(expected, 1e-5)

    @pytest.mark.parametrize(
        'order, pressure, expected',
        [
            ([0, 1, 2], 0, 0),
            ([0, 1, 2], 0.5, 0.5),
            ([0, 1, 2], 1, 1),
            ([0, 1, 2], 1.5, 1 + 1.5 - 2 * numpy.log(1.5)),
            ([0, 1, 2], 2, 1 + 3 - 2 * numpy.log(2)),
            ([0, 1, 2], 2.5, 1 + 3 - 2 * numpy.log(2) + 2.5 - 6 * numpy.log(2.5 / 2)),
            ([0, 1, 2], 3, 1 + 3 - 2 * numpy.log(2) + 5 - 6 * numpy.log(3 / 2)),
            ([2, 1, 0], 2.5, 1 + 3 - 2 * numpy.log(2) + 2.5 - 6 * numpy.log(2.5 / 2)),
            ([1, 0, 2], 2.5, 1 + 3 - 2 * numpy.log(2) + 2.5 - 6 * numpy.log(2.5 / 2)),
        ],
    )
    def test_spreading_pressure_order_and_boundaries(self, isotherm_parameters, order, pressure, expected):
        point = pygaps.PointIsotherm(
            pressure=numpy.array([1, 2, 3])[order],
            loading=numpy.array([1, 4, 9])[order],
            branch='des',
            **isotherm_parameters,
        )
        before = point.data_raw.copy(deep=True)

        assert point.spreading_pressure_at(pressure, branch='des') == pytest.approx(expected)
        pandas.testing.assert_frame_equal(point.data_raw, before)

    @pytest.mark.parametrize('reverse, pressure, expected', [
        (False, 0, 0), (False, 0.5, 0.5), (False, 1, 1),
        (False, 1.5, 2.5 - 2 * numpy.log(1.5)),
        (True, 1.5, 2.5 - 2 * numpy.log(1.5)),
    ])
    def test_spreading_pressure_zero_origin(self, isotherm_parameters, reverse, pressure, expected):
        pressures = [0, 1, 2]
        loadings = [0, 1, 4]
        point = pygaps.PointIsotherm(
            pressure=pressures[::-1] if reverse else pressures,
            loading=loadings[::-1] if reverse else loadings,
            branch='ads',
            **isotherm_parameters,
        )

        with numpy.errstate(divide='raise', invalid='raise'):
            assert point.spreading_pressure_at(pressure) == pytest.approx(expected)

    @pytest.mark.parametrize('branch, cached_fill', [
        ('ads', 'uncached'), ('ads', None), ('ads', 9), ('ads', 'extrapolate'),
        ('des', None),
    ])
    def test_spreading_pressure_extrapolation(self, isotherm_parameters, cached_fill, branch):
        pressures = [1, 2, 3] if branch == 'ads' else [3, 2, 1]
        point = pygaps.PointIsotherm(
            pressure=pressures, loading=numpy.square(pressures), branch=branch, **isotherm_parameters
        )
        if cached_fill != 'uncached':
            point.loading_at(2, branch=branch, interp_fill=cached_fill)
        area = 1 + 3 - 2 * numpy.log(2) + 5 - 6 * numpy.log(3 / 2)

        with pytest.raises(pgEx.CalculationError, match='extrapolat'):
            point.spreading_pressure_at(4, branch=branch)

        assert point.spreading_pressure_at(0.5, branch=branch) == pytest.approx(0.5)
        assert point.spreading_pressure_at(4, branch=branch, interp_fill=9) == pytest.approx(area + 9 * numpy.log(4 / 3))
        assert point.spreading_pressure_at(4, branch=branch, interp_fill=(0, 12)) == pytest.approx(area + 12 * numpy.log(4 / 3))
        assert point.spreading_pressure_at(4, branch=branch, interp_fill='extrapolate') == pytest.approx(
            area + 5 - 6 * numpy.log(4 / 3)
        )

    def test_spreading_pressure_extrapolation_units(self, isotherm_parameters):
        point = pygaps.PointIsotherm(
            pressure=[3, 2, 1], loading=[9, 4, 1], branch='des', **isotherm_parameters
        )
        area = 1 + 3 - 2 * numpy.log(2) + 5 - 6 * numpy.log(3 / 2)

        assert point.spreading_pressure_at(
            400000, branch='des', pressure_unit='Pa', loading_unit='mol', interp_fill=9
        ) == pytest.approx((area + 9 * numpy.log(4 / 3)) / 1000)

    @pytest.mark.parametrize('interp_fill', [numpy.nan, numpy.inf])
    def test_spreading_pressure_invalid_fill(self, isotherm_parameters, interp_fill):
        point = pygaps.PointIsotherm(
            pressure=[1, 2], loading=[1, 4], branch='ads', **isotherm_parameters
        )

        with pytest.raises(pgEx.CalculationError, match='finite loading'):
            point.spreading_pressure_at(3, interp_fill=interp_fill)

    @pytest.mark.parametrize(
        'pressures, loadings, message',
        [
            ([1, 1, 2], [1, 1, 4], 'duplicate'),
            ([1, numpy.inf, 2], [1, 4, 4], 'finite'),
            ([1, 2, 3], [1, numpy.inf, 9], 'finite'),
            ([-1, 1, 2], [0, 1, 4], 'negative'),
            ([0, 1, 2], [1, 1, 4], 'zero pressure'),
            ([0], [0], 'positive pressure'),
        ],
    )
    def test_spreading_pressure_invalid_data(self, isotherm_parameters, pressures, loadings, message):
        point = pygaps.PointIsotherm(
            pressure=pressures, loading=loadings, branch='ads', **isotherm_parameters
        )

        with pytest.raises(pgEx.CalculationError, match=message):
            point.spreading_pressure_at(1.5)

    @pytest.mark.parametrize('pressure', [-1, numpy.nan, numpy.inf])
    def test_spreading_pressure_invalid_target(self, basic_pointisotherm, pressure):
        with pytest.raises(pgEx.ParameterError, match='finite, nonnegative'):
            basic_pointisotherm.spreading_pressure_at(pressure)

    def test_spreading_pressure_missing_branch(self, isotherm_parameters):
        point = pygaps.PointIsotherm(
            pressure=[1, 2], loading=[1, 4], branch='des', **isotherm_parameters
        )

        with pytest.raises(pgEx.CalculationError, match='positive pressure'):
            point.spreading_pressure_at(1.5, branch='ads')

    ##########################

    @pytest.mark.parametrize(
        'parameters',
        [
            (
                {
                    "pressure_mode": "absolute",
                    "pressure_unit": "Pa",
                }
            ),
            (
                {
                    "loading_basis": "mass",
                    "loading_unit": "g",
                }
            ),
            (
                {
                    "material_basis": "volume",
                    "material_unit": "cm3",
                }
            ),
            (
                {
                    "pressure_mode": "absolute",
                    "pressure_unit": "Pa",
                    "loading_basis": "mass",
                    "loading_unit": "g",
                    "material_basis": "volume",
                    "material_unit": "cm3",
                }
            ),
        ],
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
        'expected, parameters',
        [
            (
                1,
                {
                    "unit_to": "bar",
                },
            ),
            (
                1e5,
                {
                    "mode_to": "absolute",
                    "unit_to": "Pa",
                },
            ),
            (
                0.12849,
                {
                    "mode_to": "relative",
                },
            ),
            (
                12.849,
                {
                    "mode_to": "relative%",
                },
            ),
        ],
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

    def test_convert_pressure_pseudo_boolean(self, monkeypatch, fractional_conversion_parameters):
        parameters = fractional_conversion_parameters
        monkeypatch.setattr(parameters['adsorbate'], 't_critical', lambda: 50)
        monkeypatch.setattr(parameters['adsorbate'], 'p_critical', lambda: 100000)
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3], loading=[1, 2, 3], branch='ads', **parameters
        )
        point.convert_pressure(mode_to='relative', pseudo=True)
        numpy.testing.assert_allclose(point.pressure(), [0.25, 0.5, 0.75])

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            (
                1,
                {
                    "basis_to": "molar",
                    "unit_to": "mmol",
                },
            ),
            (
                1e-3,
                {
                    "unit_to": "mol",
                },
            ),
            (
                22.414,
                {
                    "unit_to": "cm3(STP)",
                },
            ),
            (
                0.028,
                {
                    "basis_to": "mass",
                    "unit_to": "g",
                },
            ),
            (
                0.876484,
                {
                    "basis_to": "volume_gas",
                    "unit_to": "cm3",
                },
            ),
            (
                0.0280135,
                {
                    'basis_to': 'fraction',
                },
            ),  # Fractional weight (will be 1/1000 mol * 28.01 g/mol)
            (
                2.80134,
                {
                    'basis_to': 'percent',
                },
            ),  # Percent weight
        ],
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
        'expected, parameters',
        [
            (
                1,
                {
                    "basis_to": "mass",
                    "unit_to": "g",
                },
            ),
            (
                1000,
                {
                    "unit_to": "kg",
                },
            ),
            (
                0.01,
                {
                    "basis_to": "molar",
                    "unit_to": "mmol",
                },
            ),
            (
                2,
                {
                    "basis_to": "volume",
                    "unit_to": "cm3",
                },
            ),
        ],
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

    @pytest.mark.parametrize('representation, conversion, arguments', [
        ('physical', 'pressure', 'omitted'),
        ('physical', 'pressure', 'basis'),
        ('physical', 'pressure', 'unit'),
        ('physical', 'pressure', 'explicit'),
        ('physical', 'loading', 'omitted'),
        ('physical', 'loading', 'basis'),
        ('physical', 'loading', 'unit'),
        ('physical', 'loading', 'explicit'),
        ('physical', 'material', 'omitted'),
        ('physical', 'material', 'basis'),
        ('physical', 'material', 'unit'),
        ('physical', 'material', 'explicit'),
        ('physical', 'all', 'explicit'),
        ('relative', 'pressure', 'basis'),
        ('relative', 'all', 'omitted'),
        ('fraction', 'material', 'basis'),
        ('fraction', 'all', 'omitted'),
        ('percent', 'all', 'basis'),
    ])
    def test_isotherm_convert_noop(self, isotherm_parameters, representation, conversion, arguments):
        parameters = isotherm_parameters.copy()
        if representation in ['fraction', 'percent']:
            parameters.update(loading_basis=representation, loading_unit=None)
        elif representation == 'relative':
            parameters.update(pressure_mode='relative', pressure_unit=None)
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3], loading=[1, 2, 3], branch='ads', **parameters
        )
        point.loading_at(2)
        point.pressure_at(2)
        before_data = point.data_raw.copy(deep=True)
        before_units = point.units.copy()
        before_metadata = point.to_dict()
        before_interpolators = (point.l_interpolator, point.p_interpolator)
        options = {}
        for variable in ['pressure', 'loading', 'material']:
            if conversion not in [variable, 'all']:
                continue
            basis = 'mode' if variable == 'pressure' else 'basis'
            if arguments in ['basis', 'explicit']:
                key = f'{variable}_{basis}' if conversion == 'all' else f'{basis}_to'
                options[key] = getattr(point, f'{variable}_{basis}')
            if arguments in ['unit', 'explicit']:
                key = f'{variable}_unit' if conversion == 'all' else 'unit_to'
                options[key] = getattr(point, f'{variable}_unit')

        method = point.convert if conversion == 'all' else getattr(point, f'convert_{conversion}')
        method(**options)

        pandas.testing.assert_frame_equal(point.data_raw, before_data)
        assert point.units == before_units
        assert point.to_dict() == before_metadata
        assert (point.l_interpolator, point.p_interpolator) == before_interpolators
        if conversion == 'all':
            rebuilt = pygaps.PointIsotherm(
                isotherm_data=point.data_raw.copy(),
                pressure_key=point.pressure_key, loading_key=point.loading_key,
                **point.to_dict(),
            )
            restored = pgp.isotherm_from_json(pgp.isotherm_to_json(point))
            for other in [rebuilt, restored]:
                assert other.units == before_units
                numpy.testing.assert_array_equal(other.pressure(), point.pressure())
                numpy.testing.assert_array_equal(other.loading(), point.loading())

    @pytest.mark.parametrize('loading_basis', ['fraction', 'percent'])
    def test_isotherm_convert_fractional_material_unit(self, isotherm_parameters, loading_basis):
        parameters = {**isotherm_parameters, 'loading_basis': loading_basis, 'loading_unit': None}
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3], loading=[0.01, 0.02, 0.03], branch='ads', **parameters
        )
        before = point.data_raw.copy(deep=True)

        point.convert_material(unit_to='kg')

        assert point.material_unit == 'kg'
        pandas.testing.assert_frame_equal(point.data_raw, before)
        with pytest.raises(pgEx.ParameterError, match='Unit selected'):
            point.convert_material(unit_to='bad_unit')
        assert point.material_unit == 'kg'
        pandas.testing.assert_frame_equal(point.data_raw, before)

    @pytest.mark.parametrize(
        'parameters, cause_message',
        [
            pytest.param({'unit_to': 'bad_unit'}, 'Unit selected for conversion', id='unit'),
            pytest.param({'mode_to': 'bad_mode'}, 'Basis selected for pressure', id='mode'),
        ],
    )
    def test_isotherm_convert_pressure_invalid(self, basic_pointisotherm, use_adsorbate, parameters, cause_message):
        before_data = basic_pointisotherm.data_raw.copy(deep=True)
        before_units = basic_pointisotherm.units.copy()

        with pytest.raises(pgEx.CalculationError, match='The isotherm cannot be converted') as error:
            basic_pointisotherm.convert_pressure(**parameters)

        assert isinstance(error.value.__cause__, pgEx.ParameterError)
        assert cause_message in str(error.value.__cause__)
        pandas.testing.assert_frame_equal(basic_pointisotherm.data_raw, before_data)
        assert basic_pointisotherm.units == before_units

    @pytest.mark.parametrize('conversion', ['loading', 'material'])
    @pytest.mark.parametrize(
        'parameters, message',
        [
            pytest.param({'unit_to': 'bad_unit'}, 'Unit selected for conversion', id='unit'),
            pytest.param({'basis_to': 'bad_basis'}, 'Basis selected for', id='basis'),
        ],
    )
    def test_isotherm_convert_invalid(self, basic_pointisotherm, use_adsorbate, use_material, conversion, parameters, message):
        before_data = basic_pointisotherm.data_raw.copy(deep=True)
        before_units = basic_pointisotherm.units.copy()

        with pytest.raises(pgEx.ParameterError, match=message):
            getattr(basic_pointisotherm, f'convert_{conversion}')(**parameters)

        pandas.testing.assert_frame_equal(basic_pointisotherm.data_raw, before_data)
        assert basic_pointisotherm.units == before_units

    @pytest.mark.parametrize('loading_basis, conversion, failure, cached', [
        ('fraction', 'loading', 'missing-density', True),
        ('fraction', 'material', 'missing-density', True),
        ('fraction', 'loading', 'invalid-unit', True),
        ('fraction', 'material', 'invalid-unit', True),
        ('percent', 'material', 'missing-density', True),
        ('fraction', 'loading', 'missing-density', False),
    ])
    def test_fractional_conversion_failure_preserves_state(
        self, monkeypatch, fractional_conversion_parameters, loading_basis, conversion, failure, cached,
    ):
        parameters = {**fractional_conversion_parameters, 'loading_basis': loading_basis, 'loading_unit': None}
        loadings = numpy.array([0.01, 0.02, 0.03])
        if loading_basis == 'percent':
            loadings *= 100
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3], loading=loadings, branch='ads', **parameters
        )
        if cached:
            point.loading_at(1.5)
            point.pressure_at(loadings[0] * 1.5)
        before_data = point.data_raw.copy(deep=True)
        before_metadata = point.to_dict()
        before_interpolators = (point.l_interpolator, point.p_interpolator)
        intermediate = []
        original_conversion = converters.c_loading

        def capture_conversion(*args, **kwargs):
            result = original_conversion(*args, **kwargs)
            intermediate.append(result.copy())
            return result

        monkeypatch.setattr(converters, 'c_loading', capture_conversion)
        if failure == 'missing-density':
            monkeypatch.delattr(point.adsorbate, 'liquid_density')
            monkeypatch.delattr(point.adsorbate, 'liquid_molar_density')
            error, message = pgEx.CalculationError, 'liquid_molar_density'
        else:
            error, message = pgEx.ParameterError, 'Unit selected'
        basis_to = 'volume' if conversion == 'material' else 'volume_liquid'
        unit_to = 'cm3' if failure == 'missing-density' else 'invalid'

        with pytest.raises(error, match=message):
            getattr(point, f'convert_{conversion}')(basis_to=basis_to, unit_to=unit_to)

        assert len(intermediate) == 1
        numpy.testing.assert_allclose(intermediate[0], [0.001, 0.002, 0.003])
        pandas.testing.assert_frame_equal(point.data_raw, before_data)
        assert point.to_dict() == before_metadata
        assert (point.l_interpolator, point.p_interpolator) == before_interpolators
        assert point.loading_at(1.5) == pytest.approx(loadings[0] * 1.5)
        assert point.pressure_at(loadings[0] * 1.5) == pytest.approx(1.5)

    @pytest.mark.parametrize('conversion', ['loading', 'material'])
    def test_fractional_conversion_success_resets_caches(self, fractional_conversion_parameters, conversion):
        parameters = {**fractional_conversion_parameters, 'loading_basis': 'fraction', 'loading_unit': None}
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3], loading=[0.01, 0.02, 0.03], branch='ads', **parameters
        )
        point.loading_at(1.5)
        point.pressure_at(0.015)
        basis_to = 'volume' if conversion == 'material' else 'volume_liquid'

        getattr(point, f'convert_{conversion}')(basis_to=basis_to, unit_to='cm3')

        assert point.l_interpolator is None
        assert point.p_interpolator is None
        expected = 0.06 if conversion == 'material' else 0.03
        assert point.loading_at(1.5) == pytest.approx(expected)
        assert point.pressure_at(expected) == pytest.approx(1.5)

    def test_isotherm_convert_complex(
        self,
        use_adsorbate,
        use_material,
        basic_pointisotherm,
    ):
        """Some more complex conversions are checked here."""

        # Convert from mmol/g -> wt% (g/g)
        basic_pointisotherm.convert_loading(basis_to='fraction')
        assert basic_pointisotherm.loading()[0] == pytest.approx(0.028, 0.001)
        # Convert from wt% (g/g) to vol% (cm3/cm3)
        basic_pointisotherm.convert_material(basis_to='volume', unit_to='cm3')
        assert basic_pointisotherm.loading()[0] == pytest.approx(0.08123, 0.001)
        # Convert from vol% (cm3/cm3) to vol% (m3/m3)
        basic_pointisotherm.convert_material(basis_to='volume', unit_to='m3')
        assert basic_pointisotherm.loading()[0] == pytest.approx(0.08123, 0.001)
        # Convert from vol% (m3/m3) to mol% (mol/mol)
        basic_pointisotherm.convert_material(basis_to='molar', unit_to='mol')
        assert basic_pointisotherm.loading()[0] == pytest.approx(0.01, 0.001)
        # Convert from mol% (mol/mol) to mmol/mol
        basic_pointisotherm.convert_loading(basis_to='molar', unit_to='mmol')
        assert basic_pointisotherm.loading()[0] == pytest.approx(10, 0.001)
        # Convert from mmol/mol to mmol/g
        basic_pointisotherm.convert_material(basis_to='mass', unit_to='g')
        assert basic_pointisotherm.loading()[0] == pytest.approx(1, 0.001)

    def test_fractional_loading_conversion_paths(self, fractional_conversion_parameters):
        parameters = fractional_conversion_parameters
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3],
            loading=[2, 4, 6],
            branch='ads',
            **parameters,
        )
        conversion = {
            'loading_basis': 'fraction',
            'material_basis': 'volume',
            'material_unit': 'cm3',
        }

        assert point.loading(**conversion)[1] == pytest.approx(0.16)
        assert point.loading_at(2, **conversion) == pytest.approx(0.16)
        assert point.loading_at(1.5, **conversion) == pytest.approx(0.12)
        assert point.pressure_at(0.16, loading_unit='cm3', **conversion) == pytest.approx(2)

        fractional_parameters = {**parameters, 'loading_basis': 'fraction', 'loading_unit': None}
        fractional_point = pygaps.PointIsotherm(
            pressure=[1, 2, 3],
            loading=[0.01, 0.02, 0.03],
            branch='ads',
            **fractional_parameters,
        )
        material_conversion = {'material_basis': 'volume', 'material_unit': 'cm3'}

        assert fractional_point.loading(**material_conversion)[0] == pytest.approx(0.04)
        assert fractional_point.loading_at(1, **material_conversion) == pytest.approx(0.04)
        assert fractional_point.loading(loading_basis='percent', **material_conversion)[0] == pytest.approx(4)
        assert fractional_point.pressure_at(
            0.04,
            loading_basis='fraction',
            loading_unit='cm3',
            **material_conversion,
        ) == pytest.approx(1)

        fractional_point.convert_material(basis_to='volume', unit_to='cm3')
        assert fractional_point.loading()[0] == pytest.approx(0.04)
        fractional_point.convert_loading(basis_to='percent')
        assert fractional_point.loading()[0] == pytest.approx(4)

    @pytest.mark.parametrize('model', ['Henry', 'Virial'])
    @pytest.mark.parametrize('coordinate', ['pressure', 'loading'])
    def test_from_modelisotherm_point_coordinates(self, isotherm_parameters, model, coordinate):
        parameters = {'K': 2.0}
        if model == 'Virial':
            parameters.update(A=0.0, B=0.0, C=0.0)
        model_isotherm = pygaps.ModelIsotherm(
            model=model_from_dict(
                {
                    'name': model,
                    'parameters': parameters,
                    'pressure_range': (0.5, 2.0),
                    'loading_range': (1.0, 4.0),
                }
            ),
            branch='ads',
            **isotherm_parameters,
        )
        reference = pygaps.PointIsotherm(
            pressure=[0.5, 1.0, 1.5, 2.0],
            loading=[1.0, 2.0, 3.0, 4.0],
            branch='ads',
            **isotherm_parameters,
        )
        # Coordinate isotherms may use units different from the model.
        reference.convert_pressure(unit_to='Pa', verbose=False)
        reference.convert_loading(unit_to='mol', verbose=False)
        result = pygaps.PointIsotherm.from_modelisotherm(model_isotherm, **{f'{coordinate}_points': reference})
        numpy.testing.assert_allclose(result.pressure(), [0.5, 1.0, 1.5, 2.0], rtol=1e-4)
        numpy.testing.assert_allclose(result.loading(), [1.0, 2.0, 3.0, 4.0], rtol=1e-4)


    ##########################

    @mpl_cleanup
    def test_isotherm_print_parameters(self, basic_pointisotherm):
        """Check isotherm can print its own info."""

        print(basic_pointisotherm)
        basic_pointisotherm.plot()
        basic_pointisotherm.print_info()
