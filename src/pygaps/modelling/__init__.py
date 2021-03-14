# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa
"""
Scaffolding and convenience functions for isotherm fitting.

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


def model_iso(
    isotherm,
    branch='ads',
    model=None,
    param_guess=None,
    optimization_params=None,
    verbose=False
):
    """
    Fits a PointIsotherm with a model.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm to model.
    branch : [None, 'ads', 'des'], optional
        Branch of isotherm to model. Defaults to adsorption branch.
    model : str, list, 'guess'
        The model to be used to describe the isotherm. Give a single model
        name (`"Langmuir"`) to fit it. Give a list of many model names to
        try them all and return the best fit (`[`Henry`, `Langmuir`]`).
        Specify `"guess"` to try all available models.
    param_guess : dict, optional
        Starting guess for model parameters in the data fitting routine.
    optimization_params : dict, optional
        Dictionary to be passed to the minimization function to use in fitting model to data.
        See `here
        <https://docs.scipy.org/doc/scipy/reference/optimize.html#module-scipy.optimize>`__.
    verbose : bool
        Prints out extra information about steps taken.
    """
    from ..core.modelisotherm import ModelIsotherm
    return ModelIsotherm.from_pointisotherm(
        isotherm,
        branch=branch,
        model=model,
        param_guess=param_guess,
        optimization_params=optimization_params,
        verbose=verbose,
    )
