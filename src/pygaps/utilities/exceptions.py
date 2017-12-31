"""
Custom errors thrown by the program.
"""


class Error(Exception):
    """Error raised by this program."""


class ParameterError(Error):
    """Raised when one of the parameters is unsuitable."""


class CalculationError(Error):
    """Raised when a calculation fails."""


class ParsingError(Error):
    """Raised when parsing fails."""


class GraphingError(Error):
    """Raised when graphing fails."""
