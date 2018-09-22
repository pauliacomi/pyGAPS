# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa

"""
This file has all the isotherm models which are available

If adding a custom model, it should be also added below.
"""

from ...utilities.exceptions import ParameterError
from .bet import BET
from .dslangmuir import DSLangmuir
from .fhvst import FHVST
from .henry import Henry
from .jensenseaton import JensenSeaton
from .langmuir import Langmuir
from .model import IsothermModel
from .quadratic import Quadratic
from .temkinapprox import TemkinApprox
from .toth import Toth
from .tslangmuir import TSLangmuir
from .virial import Virial
from .wvst import WVST

# This list has all the available models
_MODELS = [Henry, Langmuir, DSLangmuir, TSLangmuir,
           Quadratic, BET, TemkinApprox, Virial,
           Toth, JensenSeaton, FHVST, WVST]

# This list has all the models which will be used when attempting to
# guess an isotherm model. They are the ones where the fitting
# is fast enough to be acceptable
_GUESS_MODELS = [Henry, Langmuir, DSLangmuir, TSLangmuir,
                 Quadratic, BET, TemkinApprox, Toth, JensenSeaton]

# This list has all the models which work with IAST.
# This is required as some models (such as Freundlich)
# are not thermodynamically consistent.
_IAST_MODELS = [Henry, Langmuir, DSLangmuir, TSLangmuir,
                Quadratic, BET, TemkinApprox, Toth, JensenSeaton]


def get_isotherm_model(model_name):
    """
    Checks whether specified model name exists
    and returns an instance of that model class.

    Parameters
    ----------
    model_name : str
        The name of the requested model

    Returns
    -------
    ModelIsotherm
        A specific model

    Raises
    ------
    ParameterError
        When the model does not exist
    """

    if model_name not in [model.name for model in _MODELS]:
        raise ParameterError("Model {0} not an option. Viable models "
                             "are {1}".format(model_name, [model.name for model in _MODELS]))

    for _model in _MODELS:
        if model_name == _model.name:
            return _model()


def is_iast_model(model_name):
    """
    Checks whether specified model can be used
    with IAST.

    Parameters
    ----------
    model_name : str
        The name of the model

    Returns
    -------
    bool
        Whether it is applicable or not.

    """

    return model_name in [model.name for model in _IAST_MODELS]


def is_base_model(model):
    """
    Checks whether it is a model.

    Parameters
    ----------
    model : Model
        A derived IsothermModel class

    Returns
    -------
    bool
        True or false.

    """

    return isinstance(model, IsothermModel)
