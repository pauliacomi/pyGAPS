"""Direct mathematical contracts, with explicit known-defect regressions."""

import warnings

import numpy
import pandas
import pytest

from pygaps.utilities import math_utilities as math
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError

pytestmark = pytest.mark.utilities


@pytest.mark.parametrize(
    'pressure, expected',
    [
        ([1, 2, 3], [0, 0, 0]),
        ([1, 2, 3, 2, 1], [0, 0, 0, 1, 1]),
        ([1, 3, 3, 2], [0, 0, 1, 1]),
    ],
)
@pytest.mark.parametrize('index_kind', ['default', 'shifted', 'duplicate'])
def test_split_ads_data(pressure, expected, index_kind):
    index = None
    if index_kind == 'shifted':
        index = numpy.arange(len(pressure)) * 10 + 10
    elif index_kind == 'duplicate':
        index = ['row'] * len(pressure)
    data = pandas.DataFrame({'p': pressure}, index=index)
    original = data.copy(deep=True)
    result = math.split_ads_data(data, 'p')
    numpy.testing.assert_array_equal(result, expected)
    assert result.dtype == numpy.int8
    pandas.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize('index', [None, [1, 2, 3], ['same', 'same', 'other']])
def test_split_ads_data_descending(index):
    result = math.split_ads_data(pandas.DataFrame({'p': [3, 2, 1]}, index=index), 'p')
    numpy.testing.assert_array_equal(result, [1, 1, 1])


@pytest.mark.parametrize('pressure, expected', [([3], [0]), ([1, numpy.nan, 3, 2], [0, 0, 0, 1])])
def test_split_ads_data_single_point_and_missing(pressure, expected):
    data = pandas.DataFrame({'p': pressure})
    numpy.testing.assert_array_equal(math.split_ads_data(data, 'p'), expected)


@pytest.mark.parametrize(
    'limits, expected',
    [(None, (0, 7)), ((None, None), (0, 7)), ((3, None), (2, 7)), ((None, 7), (0, 5)), ((3, 7), (2, 5))],
)
def test_find_limit_indices(limits, expected):
    values = numpy.arange(1, 9)
    result = math.find_limit_indices(values, limits)
    assert result == expected
    selected = values[result[0] : result[1] + 1]
    assert len(selected) >= 3
    if limits is not None:
        if limits[0] is not None:
            assert numpy.all(selected >= limits[0])
        if limits[1] is not None:
            assert numpy.all(selected < limits[1])


@pytest.mark.parametrize('values, limits', [([], None), ([1, 2], None), (list(range(8)), (20, None)), (list(range(8)), (5, 3))])
def test_find_limit_indices_insufficient(values, limits):
    with pytest.raises(CalculationError, match='Not enough points'):
        math.find_limit_indices(values, limits)


@pytest.mark.parametrize('limits, expected', [((0, None), (5, 9)), ((None, 0), (0, 4))])
def test_find_limit_indices_zero_bound(limits, expected):
    assert math.find_limit_indices(numpy.arange(-5, 5), limits) == expected


@pytest.mark.parametrize('minimum', [1, 3, 5])
def test_find_limit_indices_exact_minimum(minimum):
    assert math.find_limit_indices(list(range(minimum)), smallest_selection=minimum) == (0, minimum - 1)
    with pytest.raises(CalculationError, match='Not enough points'):
        math.find_limit_indices(list(range(minimum - 1)), smallest_selection=minimum)


def test_find_limit_indices_duplicate_bounds():
    values = [0, 1, 1, 2, 3, 3, 4]
    assert math.find_limit_indices(values, (1, 3)) == (1, 3)


@pytest.mark.parametrize('nonuniform', [False, True])
def test_find_linear_sections_straight(nonuniform):
    x = numpy.geomspace(1, 10, 20) if nonuniform else numpy.linspace(1, 10, 20)
    assert math.find_linear_sections(x, 2 * x + 1) == [list(range(len(x)))]


def test_find_linear_sections_piecewise():
    x = numpy.linspace(1, 10, 80)
    y = numpy.where(x <= 5, x, 5 + 3 * (x - 5))
    sections = math.find_linear_sections(x, y)
    assert len(sections) == 2
    assert sections[0][0] == 0 and sections[1][-1] == len(x) - 1
    assert numpy.all(x[sections[0]] < 5)
    assert numpy.all(x[sections[1]] > 5)
    assert len(sections[0]) > 3 and len(sections[1]) > 3


def test_find_linear_sections_small_perturbation():
    x = numpy.linspace(1, 10, 40)
    y = 2 * x + 1 + 1e-6 * numpy.sin(numpy.arange(len(x)))
    assert math.find_linear_sections(x, y) == [list(range(len(x)))]


@pytest.mark.xfail(reason='P1-7: second derivative uses y rather than x as its coordinate', strict=True, raises=AssertionError)
def test_find_linear_sections_rejects_high_curvature_tail():
    x = numpy.linspace(0.1, 1, 40)
    y = x**10
    sections = math.find_linear_sections(x, y)
    # On normalized axes d²(x^10)/dx² = 90*x^8; this tail is well above the margin of 10.
    curved_tail = set(numpy.flatnonzero(x >= 0.85))
    assert not any(curved_tail.intersection(section) for section in sections)


@pytest.mark.xfail(reason='P1-7: a constant y coordinate causes undefined gradients', strict=True, raises=(RuntimeWarning, AssertionError))
def test_find_linear_sections_flat():
    x = numpy.linspace(1, 10, 20)
    with warnings.catch_warnings():
        warnings.simplefilter('error', RuntimeWarning)
        assert math.find_linear_sections(x, numpy.ones(len(x))) == [list(range(len(x)))]


def test_bspline_degree_zero():
    x, y = [1, 2, 3], [4, 5, 6]
    result_x, result_y = math.bspline(x, y, degree=0)
    assert result_x is x and result_y is y


@pytest.mark.parametrize('degree', [1, 2, 8])
def test_bspline_open_line(degree):
    result_x, result_y = math.bspline([0, 1, 2], [1, 3, 5], n=17, degree=degree)
    assert isinstance(result_x, numpy.ndarray) and isinstance(result_y, numpy.ndarray)
    assert result_x.shape == result_y.shape == (17,)
    assert numpy.isfinite(result_x).all() and numpy.isfinite(result_y).all()
    numpy.testing.assert_allclose(result_x, numpy.linspace(0, 2, 17), atol=1e-12)
    numpy.testing.assert_allclose(result_y, 2 * result_x + 1, atol=1e-12)


def test_bspline_linear_segments():
    result_x, result_y = math.bspline([0, 1, 2], [0, 2, 1], n=9, degree=1)
    expected_x = numpy.linspace(0, 2, 9)
    numpy.testing.assert_allclose(result_x, expected_x, atol=1e-12)
    numpy.testing.assert_allclose(result_y, numpy.where(expected_x <= 1, 2 * expected_x, 3 - expected_x), atol=1e-12)


def test_bspline_unequal_lengths():
    with pytest.raises(ParameterError, match='Arrays passed are not equal'):
        math.bspline([0, 1], [0])


@pytest.mark.parametrize('degree', [1, 2, 3])
def test_bspline_periodic_closed_curve(degree):
    x, y = math.bspline([0, 1, 1, 0], [0, 0, 1, 1], n=25, degree=degree, periodic=True)
    assert isinstance(x, numpy.ndarray) and isinstance(y, numpy.ndarray)
    assert x.shape == y.shape == (25,)
    assert numpy.isfinite(x).all() and numpy.isfinite(y).all()
    numpy.testing.assert_allclose([x[0], y[0]], [x[-1], y[-1]], atol=1e-12)


@pytest.mark.parametrize('degree', [1, 2, 3, 8])
def test_bspline_periodic_closure_notation_and_degree(degree):
    expected = math.bspline([0, 1, 1, 0], [0, 0, 1, 1], n=25, degree=min(degree, 3), periodic=True)
    actual = math.bspline([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], n=25, degree=degree, periodic=True)
    numpy.testing.assert_allclose(actual, expected, atol=1e-12)


@pytest.mark.parametrize(
    'degree, expected',
    [
        (1, [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]),
        (2, [[0.5, 0], [1, 0.5], [0.5, 1], [0, 0.5], [0.5, 0]]),
        (3, [[5 / 6, 1 / 6], [5 / 6, 5 / 6], [1 / 6, 5 / 6], [1 / 6, 1 / 6], [5 / 6, 1 / 6]]),
    ],
)
def test_bspline_periodic_uniform_basis(degree, expected):
    # At integer knots the uniform basis weights are (1), (1/2, 1/2), or (1/6, 4/6, 1/6).
    x, y = math.bspline([0, 1, 1, 0], [0, 0, 1, 1], n=5, degree=degree, periodic=True)
    numpy.testing.assert_allclose(numpy.column_stack((x, y)), expected, atol=1e-12)


@pytest.mark.parametrize('degree', [2, 3])
def test_bspline_periodic_tangent_continuity(degree):
    x, y = math.bspline([0, 1, 1, 0], [0, 0, 1, 1], n=4097, degree=degree, periodic=True)
    points = numpy.column_stack((x, y))
    step = 4 / (len(points) - 1)
    numpy.testing.assert_allclose((points[1] - points[0]) / step, (points[-1] - points[-2]) / step, atol=2e-3)


@pytest.mark.parametrize('x, y', [([], []), ([1], [2]), ([1, 1], [2, 2])])
def test_bspline_periodic_insufficient_points(x, y):
    with pytest.raises(ParameterError, match='at least two control points'):
        math.bspline(x, y, periodic=True)


@pytest.mark.parametrize('maximum', [1, 10, 100, 101])
def test_same_orders_of_maximum(maximum):
    expected = maximum <= 100
    assert bool(math.same_orders_of_maximum([[1, 10], [maximum]])) is expected
    assert bool(math.same_orders_of_maximum([[maximum], [1, 10]])) is expected
