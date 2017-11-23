"""
Base class for all models
"""


class IsothermModel(object):
    """
    Base class for all models
    """

    #: Name of the class as static
    name = None

    def __init__(self):
        """
        Instantiation function
        """

    def loading(self, pressure):
        """
        Function that calculates loading
        """
        return None

    def pressure(self, loading):
        """
        Function that calculates pressure
        """
        return None

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure
        """
        return None

    def default_guess(self, saturation_loading, langmuir_k):
        """
        Returns initial guess for fitting
        """
        return None
