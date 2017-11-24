"""
Base class for all models
"""


class IsothermModel(object):
    """
    Base class for all models
    """

    #: Name of the class as static
    name = None

    # def __init__(self):
    #     """
    #     Instantiation function
    #     """

    def loading(self, pressure):
        """
        Function that calculates loading

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """
        return None

    def pressure(self, loading):
        """
        Function that calculates pressure

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return None

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        return None

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting

        Parameters
        ----------
        saturation_loading : float
            Loading at the saturation plateau.
        langmuir_k : float
            Langmuir calculated constant.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        return None
        """
