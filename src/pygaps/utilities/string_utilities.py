"""General functions for string transformations."""
import pygaps


def _to_latex(string):
    """Latex-decorate a string."""
    return ('$' + string + '$')


def convert_chemformula(string):
    """
    Convert a chemical formula string to a matplotlib parsable format (latex).

    Parameters
    ----------
    string or Isotherm: str
        String to process.

    Returns
    -------
    str
        Processed string.
    """
    result = result = getattr(string, 'adsorbate', False)
    if not result:
        inner = []
        # Iterate through the string, adding non-numbers to the no_digits list
        number_processing = False
        for i in string:
            if i.isdigit() and number_processing:
                number_processing = True
            elif i.isdigit() and not number_processing:
                inner.append('_{')
                number_processing = True
            else:
                if number_processing:
                    inner.append('}')
                    number_processing = False
            inner.append(i)

        if inner[-1].isdigit():
            inner.append('}')

        # which put all characters together.
        result = ''.join(inner)
    else:
        try:
            result = pygaps.Adsorbate.find(result).formula
        except pygaps.ParameterError:
            pass
    return _to_latex(result)
