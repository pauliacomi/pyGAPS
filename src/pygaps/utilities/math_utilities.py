"""Function-independent mathematical calculations."""

from collections.abc import Sequence
from itertools import groupby

import numpy

from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


def split_ads_data(data, pressure_key):
    """Mark adsorption as 0 and desorption as 1, independently of index labels.

    The first maximum belongs to adsorption unless it starts a descending dataset.
    A single point is treated as adsorption. Missing pressures are skipped when
    locating the maximum, as in pandas' ``idxmax``.
    """
    split = numpy.zeros(data.shape[0], dtype=numpy.int8)
    pressure = data[pressure_key].reset_index(drop=True)
    maximum = pressure.index.get_loc(pressure.idxmax())
    inflexion = 0 if maximum == 0 and len(split) > 1 else maximum + 1
    split[inflexion:] = 1
    return split


def find_limit_indices(
    array: "Sequence[float] | numpy.ndarray",
    limits: "tuple[float | None, float | None] | None" = None,
    smallest_selection: int = 3,
):
    """Return inclusive endpoint indexes for a selection in an ascending array.

    Bounds are lower-inclusive and upper-exclusive; ``None`` leaves a bound open.
    ``smallest_selection`` is the minimum number of selected points.
    """
    # select the maximum and minimum of the points
    index_min = 0
    index_max = len(array) - 1  # As we want absolute position

    # Set default values
    if limits is None:
        limits = (None, None)

    # Search
    if limits[0] is not None:
        index_min = numpy.searchsorted(array, limits[0])
    if limits[1] is not None:
        index_max = numpy.searchsorted(array, limits[1]) - 1
    if index_max - index_min + 1 < smallest_selection:
        raise CalculationError(f"Not enough points (at least {smallest_selection}) in the selected region.")
    return index_min, index_max


def find_linear_sections(xdata, ydata):
    """Find all sections of a curve which are linear."""
    linear_sections = []

    xdata_adj = xdata / max(xdata)
    ydata_adj = ydata / max(ydata)

    # To do this we calculate the second
    # derivative of the thickness plot
    second_deriv = numpy.gradient(numpy.gradient(ydata_adj, xdata_adj), xdata_adj)

    # We then find the points close to zero in the second derivative
    # These are the points where the graph is linear
    margin = 10
    close_zero = numpy.abs(second_deriv) < margin

    # This snippet divides the the points in linear sections
    # where linearity holds at least for a number of measurements
    continuous_p = 3

    for k, g in groupby(enumerate(close_zero), lambda x: x[1]):
        group = list(g)
        if len(group) > continuous_p and k:
            linear_sections.append(list(map(lambda x: x[0], group)))

    return linear_sections


def bspline(xs, ys, n=100, degree=2, periodic=False):
    """
    Calculate n samples on a b-spline.

    Adapted from:
    https://stackoverflow.com/questions/24612626/b-spline-interpolation-with-python

    Parameters
    ----------
    xs : array
        X points of the curve to fit
    ys : array
        Y points of the curve to fit
    n  : int
        Number of samples to return
    degree : int
        Curve degree, clipped to the number of control points minus one.
        Degree zero returns the original input objects unchanged.
    periodic : bool
        True samples one full period of a uniform control-point spline, including
        matching endpoints. A repeated terminal first point is closure notation
        and is removed. At least two control points must remain.
        False samples an open spline with clamped endpoints.
    """
    # Check if arrays are equal in size
    count = len(xs)
    if len(ys) != count:
        raise ParameterError("Arrays passed are not equal")

    # Do nothing if order is 0
    if degree == 0:
        return xs, ys

    cv = numpy.stack((xs, ys), axis=-1)

    if periodic:
        if count > 1 and numpy.array_equal(cv[0], cv[-1]):
            cv = cv[:-1]
        count = len(cv)
        if count < 2:
            raise ParameterError("A periodic spline requires at least two control points.")
        degree = numpy.clip(degree, 1, count - 1)
        # Wrapping k coefficients needs count + 2*k + 1 knots for one period.
        cv = numpy.concatenate((cv, cv[:degree]))
        kv = numpy.arange(-degree, count + degree + 1, dtype='int')
        rng = numpy.linspace(0, count, n)
    else:
        degree = numpy.clip(degree, 1, count - 1)
        kv = numpy.concatenate(
            (
                [0] * degree,
                numpy.arange(count - degree + 1),
                [count - degree] * degree,
            )
        )
        rng = numpy.linspace(0, (count - degree), n)

    # Calculate result
    from scipy import interpolate

    res = numpy.array(interpolate.splev(rng, (kv, cv.T, degree))).T

    return (
        numpy.array([x[0] for x in res]),
        numpy.array([y[1] for y in res]),
    )


def same_orders_of_maximum(vals):
    """
    Determine if the maximum of two lists are within one order of magnitude.

    Parameters
    ----------
    vals: list of list of floats
        The lists to compare

    Returns
    -------
    True:
        If within one order of magnitude
    False:
        If not
    """
    orders = [numpy.log10(max(v)) for v in vals]
    if abs(orders[0] - orders[1]) > 1:
        return False
    return True
