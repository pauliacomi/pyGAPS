# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa

from ...utilities.exceptions import ParameterError
from .bet import BET
from .dslangmuir import DSLangmuir
from .henry import Henry
from .langmuir import Langmuir
from .quadratic import Quadratic
from .temkinapprox import TemkinApprox
from .tslangmuir import TSLangmuir
from .virial import Virial
from .jensenseaton import JensenSeaton
from .toth import Toth
from .fhvst import FHVST
from .wvst import WVST

_MODELS = [Henry, Langmuir, DSLangmuir, TSLangmuir,
           Quadratic, BET, TemkinApprox, Virial,
           Toth, JensenSeaton, FHVST, WVST]

_GUESS_MODELS = [Henry, Langmuir, DSLangmuir, TSLangmuir,
                 Quadratic, BET, TemkinApprox, Toth, JensenSeaton]

_IAST_MODELS = [Henry, Langmuir, DSLangmuir, TSLangmuir,
                Quadratic, BET, TemkinApprox]


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
