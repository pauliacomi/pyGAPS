# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa
"""
Lists all isotherm models which are available.

If adding a custom model, it should be also added below as a string.
"""

import importlib

from ..utilities.exceptions import ParameterError
from .base_model import IsothermBaseModel

# This list has all the available models
_MODELS = [
    "Henry",
    "Langmuir",
    "DSLangmuir",
    "TSLangmuir",
    "BET",
    "GAB",
    "Freundlich",
    "DA",
    "DR",
    "Quadratic",
    "TemkinApprox",
    "Virial",
    "Toth",
    "JensenSeaton",
    "FHVST",
    "WVST",
]

# This list has all the models which will be used when attempting to
# guess an isotherm model. They are the ones where the fitting
# is fast enough to be acceptable
_GUESS_MODELS = [
    "Henry",
    "Langmuir",
    "DSLangmuir",
    "DR",
    "Freundlich",
    "Quadratic",
    "BET",
    "TemkinApprox",
    "Toth",
    "JensenSeaton",
]

# This list has all the models which work with IAST.
# This is required as some models (such as Freundlich)
# are not physically consistent.
_IAST_MODELS = [
    "Henry",
    "Langmuir",
    "DSLangmuir",
    "TSLangmuir",
    "Quadratic",
    "BET",
    "TemkinApprox",
    "Toth",
    "JensenSeaton",
]


def get_isotherm_model(model_name: str, params: dict = None):
    """
    Check whether specified model name exists and return an instance of that model class.

    Parameters
    ----------
    model_name : str
        The name of the requested model.
    params : dict
        Parameters to instantiate the model with.

    Returns
    -------
    ModelIsotherm
        A specific model.

    Raises
    ------
    ParameterError
        When the model does not exist
    """
    for _model in _MODELS:
        if model_name.lower() == _model.lower():
            module = importlib.import_module(
                f"pygaps.modelling.{_model.lower()}"
            )
            model = getattr(module, _model)
            return model(params)

    raise ParameterError(
        f"Model {model_name} not an option. Viable models "
        f"are {[model for model in _MODELS]}"
    )


def is_iast_model(model_name: dict):
    """
    Check whether specified model can be used with IAST.

    Parameters
    ----------
    model_name : str
        The name of the model

    Returns
    -------
    bool
        Whether it is applicable or not.

    """
    return model_name.lower() in [model.lower() for model in _IAST_MODELS]


def is_base_model(model):
    """
    Check whether the input is derived from the base model.

    Parameters
    ----------
    model : Model
        A derived IsothermBaseModel class

    Returns
    -------
    bool
        True or false.

    """
    return isinstance(model, IsothermBaseModel)


def model_from_dict(model_dict):
    """Obtain a model from a dictionary."""
    return get_isotherm_model(model_dict.pop('name'), model_dict)
