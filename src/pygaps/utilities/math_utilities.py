"""
Utilities for different function-independent mathematical calculations.
"""

from itertools import groupby

import numpy


def find_linear_sections(xdata, ydata):
    """Finds all sections of a plot which are linear."""
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
