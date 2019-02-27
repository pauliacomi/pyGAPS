"""
A b-spline fitting function

Adapted from:
https://stackoverflow.com/questions/24612626/b-spline-interpolation-with-python
"""

import numpy
import scipy.interpolate as interp

from .exceptions import ParameterError


def bspline(xs, ys, n=100, degree=2, periodic=False):
    """
    Calculate n samples on a b-spline

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
        factor, fraction = divmod(count+degree+1, count)
        cv = numpy.concatenate((cv,) * factor + (cv[:fraction],))
        count = len(cv)
        degree = numpy.clip(degree, 1, degree)

    # If opened, prevent degree from exceeding count-1
    else:
        degree = numpy.clip(degree, 1, count-1)

    # Calculate knot vector
    kv = None
    if periodic:
        kv = numpy.arange(0-degree, count+degree+degree-1, dtype='int')
    else:
        kv = numpy.concatenate(([0]*degree, numpy.arange(count-degree+1), [count-degree]*degree))

    # Calculate query range
    u = numpy.linspace(periodic, (count-degree), n)

    # Calculate result
    res = numpy.array(interp.splev(u, (kv, cv.T, degree))).T

    return (numpy.array([x[0] for x in res]),
            numpy.array([y[1] for y in res]))
