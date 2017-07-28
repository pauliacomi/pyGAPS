# %%
def convert_chemformula(string):
    "converts a string to a matplotlib parsable chemical formula"

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
    # Now join all elements of the list with '',
    # which puts all of the characters together.
    result = "$"
    result += ''.join(inner)
    result += "$"

    return result
