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
            elif i == ")":
                result += '}'
                continue
        result += (i)

    if number_processing:
        result += '}'

    if negative:
        result += '^{-1}'

    return result


def convert_loadingstr(string: str) -> str:
    pass


def _is_none(s):
    """Check if a value is a text None."""
    if s == 'None':
        return True
    return False


def _is_float(s):
    """Check if a value is a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_bool(s):
    """Check a value is a text bool."""
    if s.lower() in ['true', 'false']:
        return True
    else:
        return False


def _from_bool(s):
    """Convert a boolean into a string."""
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        raise ValueError('String cannot be converted to bool')


def _is_list(s):
    """Check a value is a simple list."""
    if s.startswith('[') and s.endswith(']'):
        return True
    else:
        return False


def _from_list(s):
    """Convert a value into a string list."""
    # note that the function will fail if the list has other spaces
    return ast.literal_eval(s.replace(' ', ","))


def _to_string(s):
    """Convert a value into a CSV-safe string."""
    if isinstance(s, list):
        return '[' + ' '.join([str(x) for x in s]) + "]"
    return str(s)
