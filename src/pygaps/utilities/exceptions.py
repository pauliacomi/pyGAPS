"""
Custom errors thrown by the program
"""


class PygapsError(Exception):
    """Error raised by the program"""


class ParameterError(PygapsError):
    """Raised when one of the parameters is unsuitable"""


class CalculationError(PygapsError):
    """Raised when a calculation fails"""
