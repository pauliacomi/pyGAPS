"""Function-independent mathematical calculations."""

from itertools import groupby

import numpy

from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


def split_ads_data(data, pressure_key):
    """Find the inflection in an adsorption dataset with adsorption/desorption."""

    # Generate array
    split = numpy.zeros(data.shape[0], dtype=numpy.int8)

    # Get the maximum pressure point (assume where desorption starts)
    inflexion = data.index.get_loc(data[pressure_key].idxmax()) + 1

    # If the maximum is not the last point
    if inflexion != len(split):

        # If the first point is the maximum, then it is purely desorption
        if inflexion == data.index[0]:
            inflexion = 0

        # Set all instances after the inflexion point to 1
        split[inflexion:] = 1

    # Return the new array with the branch column
    return split


def find_limit_indices(
    array: list,
    limits: "tuple[float, float]" = None,
    smallest_selection: int = 3,
):
    """Find the indices of an array limits"""
    # select the maximum and minimum of the points
    index_min = 0
    index_max = len(array) - 1  # As we want absolute position

    # Set default values
    if limits is None:
        limits = (None, None)

    # Search
    if limits[0]:
        index_min = numpy.searchsorted(array, limits[0])
    if limits[1]:
        index_max = numpy.searchsorted(array, limits[1]) - 1
    if index_max - index_min < smallest_selection:
        raise CalculationError(
            f"Not enough points (at least {smallest_selection}) in the selected region."
        )
    # TODO figure out which is more efficient
    #     if limits:
    # ret = ret.loc[ret.between(
    #     -numpy.inf if limits[0] is None else limits[0],
    #     numpy.inf if limits[1] is None else limits[1]
    # )]
    return index_min, index_max


def find_linear_sections(xdata, ydata):
    """Find all sections of a curve which are linear."""
    linear_sections = []

    # To do this we calculate the second
    # derivative of the thickness plot
    second_deriv = numpy.gradient(numpy.gradient(ydata, xdata), xdata)

    # We then find the points close to zero in the second derivative
    # These are the points where the graph is linear
    margin = 0.01 / (len(ydata) * max(ydata))
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
        Curve degree
    periodic : bool
        True - Curve is closed
        False - Curve is open
    """

    # Check if arrays are equal in size
    count = len(xs)
    if len(ys) != count:
        raise ParameterError("Arrays passed are not equal")

    # Do nothing if order is 0
    if degree == 0:
        return xs, ys

    cv = numpy.stack((xs, ys), axis=-1)

    # If periodic, extend the point array by count+degree+1
    if periodic:
        factor, fraction = divmod(count + degree + 1, count)
        cv = numpy.concatenate((cv, ) * factor + (cv[:fraction], ))
        count = len(cv)
        degree = numpy.clip(degree, 1, degree)

    # If opened, prevent degree from exceeding count-1
    else:
        degree = numpy.clip(degree, 1, count - 1)

    # Calculate knot vector
    kv = None
    if periodic:
        kv = numpy.arange(
            0 - degree,
            count + degree + degree - 1,
            dtype='int',
        )
    else:
        kv = numpy.concatenate((
            [0] * degree,
            numpy.arange(count - degree + 1),
            [count - degree] * degree,
        ))

    # Calculate query range
    rng = numpy.linspace(periodic, (count - degree), n)

    # Calculate result
    from scipy import interpolate
    res = numpy.array(interpolate.splev(rng, (kv, cv.T, degree))).T

    return (
        numpy.array([x[0] for x in res]),
        numpy.array([y[1] for y in res]),
    )
