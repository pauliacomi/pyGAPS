"""
Hashing isotherms
"""

import hashlib
import json

import pygaps


def isotherm_to_hash(isotherm):
    """
    Converts an isotherm object to a unique hash.

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
    raw_dict = {a: getattr(isotherm, a) for a in isotherm._id_params}

    # Isotherm data
    if isinstance(isotherm, pygaps.PointIsotherm):
        isotherm_data_dict = isotherm.data().to_dict(orient='index')
        raw_dict["isotherm_data"] = [{p: str(t) for p, t in v.items()}
                                     for k, v in isotherm_data_dict.items()]
    elif isinstance(isotherm, pygaps.ModelIsotherm):
        raw_dict["isotherm_model"] = {
            'model': isotherm.model.name,
            'parameters': isotherm.model.params,
        }

    md_hasher = hashlib.md5(json.dumps(raw_dict, sort_keys=True).encode('utf-8'))

    return md_hasher.hexdigest()
