"""General functions for string transformations."""


def convert_chemformula(string):
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


def convert_unitstr(string: str, negative: bool = False):
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
