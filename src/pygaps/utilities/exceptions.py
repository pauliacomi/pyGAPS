"""Custom errors thrown by the program."""


class pgError(Exception):
    """Base error raised by pyGAPS."""


class ParameterError(pgError):
    """Raised when one of the parameters is unsuitable."""


class CalculationError(pgError):
    """Raised when a calculation fails."""


class ParsingError(pgError):
    """Raised when parsing fails."""


class GraphingError(pgError):
    """Raised when graphing fails."""
