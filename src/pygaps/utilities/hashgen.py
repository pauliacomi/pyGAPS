"""Isotherm hashing function."""

import hashlib
import json

from pandas.util import hash_pandas_object

import pygaps


def isotherm_to_hash(isotherm):
    """
    Convert an isotherm object to a unique hash.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to be hashed.

    Returns
    -------
    str
        A string with the Isotherm hash.
    """
    # Isotherm properties
    raw_dict = isotherm.to_dict()

    # Isotherm data or model
    if isinstance(isotherm, pygaps.PointIsotherm):
        raw_dict["data_hash"] = str(
            hash_pandas_object(isotherm.data_raw.round(8)).sum()
        )
    elif isinstance(isotherm, pygaps.ModelIsotherm):
        raw_dict["data_hash"] = isotherm.model.to_dict()

    md_hasher = hashlib.md5(
        json.dumps(raw_dict, sort_keys=True).encode('utf-8')
    )

    return md_hasher.hexdigest()
