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
        latexd = []
        number_processing = False
        for i in string:
            if i.isdigit():
                if not number_processing:
                    latexd.append('_{')
                    number_processing = True
            else:
                if number_processing:
                    latexd.append('}')
                    number_processing = False
            latexd.append(i)

        if number_processing:
            latexd.append('}')

        result = ''.join(latexd)
    return f'${result}$'
