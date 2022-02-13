"""Interaction with the NIST ISODB."""

from pygaps import logger
from pygaps.parsing.json import isotherm_from_json

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
    import requests

    url = fr"{_ISODB_API}/isotherm/{filename}.json"

    try:
        resp = requests.get(url, timeout=5)

    except requests.exceptions.Timeout:
        logger.warning('Connection timeout')
        return None

    except requests.exceptions.ConnectionError:
        logger.warning('Connection error')
        return None

    return isotherm_from_json(resp.text, fmt="NIST")
