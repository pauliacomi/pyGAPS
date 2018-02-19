"""
A class used for isotherm interpolation.
"""
from scipy.interpolate import interp1d


class isotherm_interpolator(object):
    """
    Class used to interpolate between isotherm points.
    Call directly to use.

    It is mainly a wrapper around scipi.interpolate.interp1d.

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

    def __init__(self, interp_type, known_data, interp_data,
                 interp_branch='ads',
                 interp_kind='linear',
                 interp_fill=None,
                 ):
        """
        Instantiation function.
        """
        #: The kind of variable the interpolator will process.
        self.output_var = interp_type
        #: The branch the internal interpolator is on.
        self.interp_branch = interp_branch
        #: The kind of interpolator in the internal interpolator.
        self.interp_kind = interp_kind
        #: Value of loading to assume beyond highest pressure in the data.
        self.interp_fill = interp_fill

        #: The internal interpolator function. This is generated
        #: the first time it is needed to make calculations faster.

        if known_data is None:
            return

        if interp_fill is None:
            self.interp_fun = interp1d(known_data, interp_data,
                                       kind=interp_kind)
        else:
            self.interp_fun = interp1d(known_data, interp_data,
                                       kind=interp_kind,
                                       fill_value=interp_fill,
                                       bounds_error=False)

        return

    def __call__(self, data):

        return self.interp_fun(data)
