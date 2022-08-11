from pygaps.utilities.exceptions import ParameterError


def get_iso_loading_and_pressure_ordered(
    isotherm,
    branch: str,
    loading_units: dict,
    pressure_units: dict,
):
    """
    Return loading and pressure given branch and units.
    """

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
