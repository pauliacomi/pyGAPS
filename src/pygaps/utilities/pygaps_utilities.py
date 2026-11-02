"""Helper functions used internally across pyGAPS."""

import numpy

from pygaps.utilities.exceptions import ParameterError


def get_pressure_limit_indices(
    pressure: list[float] | numpy.ndarray,
    p_limits: tuple[float, float] | list[float],
) -> tuple[int, int]:
    """Return inclusive pressure-limit indices for an ascending pressure array."""
    try:
        limits = numpy.asarray(p_limits, dtype=float)
    except (OverflowError, TypeError, ValueError) as err:
        raise ParameterError("Pressure limits must contain two finite numbers.") from err

    if limits.shape != (2,) or not numpy.isfinite(limits).all():
        raise ParameterError("Pressure limits must contain two finite numbers.")
    if limits[0] > limits[1]:
        raise ParameterError("The lower pressure limit must not exceed the upper limit.")

    minimum = numpy.searchsorted(pressure, limits[0], side='left')
    maximum = numpy.searchsorted(pressure, limits[1], side='right') - 1
    return int(minimum), int(maximum)


def get_iso_loading_and_pressure_ordered(
    isotherm,
    branch: str,
    loading_units: dict,
    pressure_units: dict,
):
    """Return loading and pressure given branch and units."""
    # Read data in
    loading = isotherm.loading(
        branch=branch,
        **loading_units,
    )
    if loading is None:
        raise ParameterError("The isotherm does not have the required branch for this calculation.")
    pressure = isotherm.pressure(
        branch=branch,
        **pressure_units,
    )

    # If on an desorption branch, data will be reversed
    if branch == 'des':
        loading = loading[::-1]
        pressure = pressure[::-1]

    return pressure, loading
