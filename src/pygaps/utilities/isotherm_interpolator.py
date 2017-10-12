
from scipy.interpolate import interp1d


class isotherm_interpolator(object):
    """


    Parameters
    ----------
    isotherm_data : DataFrame
        pure-component adsorption isotherm data
    loading_key : str
        column of the pandas DataFrame where the loading is stored
    pressure_key : str
        column of the pandas DataFrame where the pressure is stored
    other_keys : iterable
        other pandas DataFrame columns with data
    basis_adsorbent : str, optional
        whether the adsorption is read in terms of either 'per volume'
        or 'per mass'
    mode_pressure : str, optional
        the pressure mode, either absolute pressures or relative in
        the form of p/p0
    unit_loading : str, optional
        unit of loading
    unit_pressure : str, optional
        unit of pressure

    Notes
    -----

    """

    def __init__(self, interp_type, known_data, interp_data,
                 interp_branch='ads',
                 interp_kind='linear',
                 interp_fill=None,
                 ):
        """
        Instatiation function
        """
        #: The kind of variable the interpolator will process
        self.output_var = interp_type
        #: the branch the internal interpolator is on
        self.interp_branch = interp_branch
        #: the kind of interpolator in the internal interpolator
        self.interp_kind = interp_kind
        #: value of loading to assume beyond highest pressure in the data
        self.interp_fill = interp_fill

        #: The internal interpolator function. This is generated
        #: the first time it is needed to make calculations faster

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
