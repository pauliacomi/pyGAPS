"""General functions for string transformations."""

import ast


def convert_chemformula(string: str) -> str:
    """
    Convert a chemical formula string to a matplotlib parsable format (latex).

    Parameters
    ----------
    string or Adsorbate: str
        String to process.

    Returns
    -------
    str
        Processed string.
    """
    result = getattr(string, 'formula', None)
    if result is None:
        result = ""
        number_processing = False
        for i in string:
            if i.isdigit():
                if not number_processing:
                    result += '_{'
                    number_processing = True
            else:
                if number_processing:
                    result += '}'
                    number_processing = False
            result += i

        if number_processing:
            result += '}'

    return f'${result}$'


def convert_unit_ltx(string: str, negative: bool = False) -> str:
    """
    Convert a unit string to a nice matplotlib parsable format (latex).

    Parameters
    ----------
    string: str
        String to process.
    negative: bool
        Whether the power is negative instead.

    Returns
    -------
    str
        Processed string.
    """
    result = ""
    number_processing = False
    for i in string:
        if i.isdigit():
            if not number_processing:
                result += '^{'
                if negative:
                    result += '-'
                    negative = False
                number_processing = True
        else:
            if number_processing:
                result += '}'
                number_processing = False
            if i == "(":
                result += '_{'
                continue
            if i == ")":
                result += '}'
                continue
        result += (i)

    if number_processing:
        result += '}'

    if negative:
        result += '^{-1}'

    return result


def _is_none(s: str) -> bool:
    """Check if a value is a text None."""
    if s == 'None':
        return True
    return False


def _is_float(s: str) -> bool:
    """Check if a value is a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_bool(s: str) -> bool:
    """Check a value is a text bool."""
    if s.lower() in ['true', 'false']:
        return True
    else:
        return False


def _from_bool(s: str) -> bool:
    """Convert a string into a boolean."""
    if s.lower() == 'true':
        return True
    if s.lower() == 'false':
        return False
    raise ValueError('String cannot be converted to bool')


def _is_list(s: str) -> bool:
    """Check a value is a simple list."""
    if s.startswith('[') and s.endswith(']'):
        return True
    return False


def _from_list(s: str):
    """Convert a value into a list/tuple/dict."""
    # note that the function will fail if the list has other spaces
    return ast.literal_eval(s.replace(' ', ","))


def _to_string(s):
    """Convert a value into a CSV-safe string."""
    if isinstance(s, list):
        return '[' + ' '.join([str(x) for x in s]) + "]"
    if isinstance(s, tuple):
        return '(' + ' '.join([str(x) for x in s]) + ")"
    return str(s)
