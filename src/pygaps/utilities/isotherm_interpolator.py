"""A class used for isotherm interpolation."""

from scipy.interpolate import interp1d


class IsothermInterpolator():
    """
    Class used to interpolate between isotherm points.

    Call directly to use.

    It is mainly a wrapper around scipy.interpolate.interp1d.

    Parameters
    ----------
    interp_type : str
        What variable the interpolator works on (pressure, loading etc).
    known_data : str
        The values corresponding to the input variable.
    interp_data : str
        The values corresponding to the variable to be interpolated.

    interp_branch : str, optional
        Stores which isotherm branch the interpolator is based on.
    interp_kind : str, optional
        Determine which kind of interpolation is done between the
        datapoints.
    interp_fill : str, optional
        The parameter passed to the scipy.interpolate.interp1d function
        to determine what to do outside data bounds.

    """
    def __init__(
        self,
        known_data,
        interp_data,
        interp_branch='ads',
        interp_kind='linear',
        interp_fill=None,
    ):
        """Instantiate."""
        # The branch the internal interpolator is on.
        self.interp_branch = interp_branch
        # The kind of interpolator in the internal interpolator.
        self.interp_kind = interp_kind
        # Value of loading to assume beyond highest pressure in the data.
        self.interp_fill = interp_fill

        # The actual interpolator. This is generated
        # the first time it is needed to make calculations faster.
        if known_data is None:
            return

        if interp_fill is None:
            self.interp_fun = interp1d(
                known_data, interp_data, kind=interp_kind
            )
        else:
            self.interp_fun = interp1d(
                known_data,
                interp_data,
                kind=interp_kind,
                fill_value=interp_fill,
                bounds_error=False
            )

    def __call__(self, data):
        """Override direct call."""
        return self.interp_fun(data)
