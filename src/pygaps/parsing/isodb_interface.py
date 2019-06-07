"""Interaction with the NIST ISODB."""
import warnings

import requests

from .jsoninterface import isotherm_from_json

_ISODB_API = "https://adsorption.nist.gov/isodb/api"


def isotherm_from_isodb(filename):
    """
    Load an isotherm from the NIST ISODB.

    Parameters
    ----------
    filename : str
        ISODB filename to retrieve using the API.

    Returns
    -------
    Isotherm
        The isotherm from ISODB.

    """
    url = r"{0}/isotherm/{1}.json".format(_ISODB_API, filename)

    try:
        resp = requests.get(url, timeout=0.5)

    except requests.exceptions.Timeout:
        warnings.warn('Connection timeout')
        return None

    except requests.exceptions.ConnectionError:
        warnings.warn('Connection error')
        return None

    return isotherm_from_json(resp.text, fmt="NIST")
