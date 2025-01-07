"""
Functions calculating the thickness of an adsorbed layer
as a function of pressure.
"""
import typing as t

import numpy
from scipy.interpolate import interp1d

from pygaps.data import STANDARD_ISOTHERMS
from pygaps.parsing.csv import isotherm_from_csv
from pygaps.utilities.exceptions import ParameterError

# Below go thickness models defined by equations


def thickness_halsey(pressure: float) -> float:
    """
    Halsey thickness curve.

    Applicable for nitrogen at 77K on materials with weakly interacting surfaces.

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.
    """
    return 0.354 * ((-5) / numpy.log(pressure))**0.333


def thickness_harkins_jura(pressure: float) -> float:
    """
    Harkins and Jura thickness curve.

    Applicable for nitrogen at 77K on materials with weakly interacting surfaces.

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.
    """
    return (0.1399 / (0.034 - numpy.log10(pressure)))**0.5


def thickness_zero(pressure: float) -> float:
    """
    A zero-thickness curve applicable for non-wetting adsorbates.

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.
    """
    return numpy.zeros_like(pressure)


# Below go thickness models defined by standard isotherms

_LOADED = {}  # we keep loaded interpolators here


def convert_to_thickness(loading, monolayer):
    r"""
    Conversion to a thickness is done by obtaining the number of adsorbed layers
    through dividing amount adsorbed by the amount adsorbed in a monolayer (as
    obtained by BET), then multiplying by the average thickness of a single
    layer. Mathematically:

    .. math::

        t [nm] = \frac{n}{n_m} * 0.354

    """
    return loading / monolayer * 0.354  # mmol/g -> t


def load_std_isotherm(name: str) -> t.Callable:
    """
    Load a standard isotherm, convert the loading to thickness,
    then fit an interpolator and then store it in memory.

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.

    Notes
    -----


    """
    if name in _LOADED:
        return _LOADED[name]

    iso = isotherm_from_csv(STANDARD_ISOTHERMS[name])
    pressure = iso.pressure()
    loading = iso.loading()
    thickness = convert_to_thickness(loading, iso.properties["monolayer uptake [mmol/g]"])

    interp = interp1d(
        pressure,
        thickness,
        kind="slinear",
        fill_value=(0, thickness[-1]),
        bounds_error=False,
    )
    _LOADED[name] = interp

    return interp


def SiO2_JKO(pressure: float) -> float:
    """
    Applicable for nitrogen at 77K on silica surfaces down to low pressures. [#]_

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.

    References
    ----------
    .. [#] Jaroniec, Mietek, Michal Kruk, and James P. Olivier. “Standard Nitrogen
       Adsorption Data for Characterization of Nanoporous Silicas.” Langmuir 15,
       no. 16 (August 1, 1999): 5410–13. https://doi.org/10.1021/la990136e.

    """
    interp = load_std_isotherm("SiO2_JKO")
    return interp(pressure)


def CB_KJG(pressure: float) -> float:
    """
    Applicable for nitrogen at 77K on non-graphitized
    carbon materials down to low pressures. [#]_

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.

    References
    ----------
    .. [#] Kruk, Michal, Mietek Jaroniec, and Kishor P. Gadkaree. “Nitrogen
       Adsorption Studies of Novel Synthetic Active Carbons.” Journal of Colloid
       and Interface Science 192, no. 1 (August 1997): 250–56.
       https://doi.org/10.1006/jcis.1997.5009. .

    """
    interp = load_std_isotherm("CB_KJG")
    return interp(pressure)


def aerosil_MCM(pressure: float) -> float:
    """
    Hybrid curve using aerosil data at low pressure and MCM data at higher pressure
    Taken from: https://doi.org/10.1021/la5026679, based on
    https://doi.org/10.1016/j.micromeso.2010.10.006 and https://doi.org/10.1021/la0105477


    Applicable for nitrogen at 77K, used for mesoporous zeolites.
    Be aware that this method still needs an additional empirical correction to get a more accurate micro/mosopore volume.

    Parameters
    ----------
    pressure : float
        Relative pressure.

    Returns
    -------
    float
        Thickness of layer in nm.
    """
    pm = {
        "A1": 0.1887299, "A2": 481.3 * -1, "A3": 0.182099, "A4": -1 * 23.78,
        "B1": 0.5675647, "B2": 0.199735, "B3": 0.4116168, "B4": 2.00834,
        "C1": 0.1423566, "C2": 0.1078, "C3": 0.4888,
        "D1": 0.08309076, "D2": 0.02995, "D3": 0.369,
        "E1": 1.268066, "E2": 1.931, "E3": 0.76934, "E4": 51.09,
    }

    def calc_t(p, pm):
        if p < 0.03:
            t = pm['A1'] * (1 - numpy.exp(pm['A2'] * p)) + pm["A3"] * (1 - numpy.exp(pm['A4'] * p))
        elif p >= 0.03 and p < 0.25:
            t = pm['B1'] * p**pm['B2'] + pm['B3'] * p**pm['B4']
        elif p >= 0.25 and p < 0.6:
            t = (pm["C1"] / (pm['C2'] - numpy.log10(p)))**pm['C3']
        elif p >= 0.6 and p < 0.9:
            t = (pm["D1"] / (pm['D2'] - numpy.log10(p)))**pm['D3']
        else:
            t = pm['E1'] * p**pm['E2'] + pm['E3'] * p**pm['E4']
        return t
    calc_t_v = numpy.vectorize(calc_t)
    thickness_array = calc_t_v(pressure, pm)
    return thickness_array


_THICKNESS_MODELS = {
    "Halsey": thickness_halsey,
    "Harkins/Jura": thickness_harkins_jura,
    "SiO2 Jaroniec/Kruk/Olivier": SiO2_JKO,
    "carbon black Kruk/Jaroniec/Gadkaree": CB_KJG,
    "zero thickness": thickness_zero,
    "aerosil_MCM": aerosil_MCM,
}


def get_thickness_model(model: t.Union[str, t.Callable]) -> t.Callable:
    """
    Return a function calculating an adsorbate thickness.

    The ``model`` parameter is a string which names the thickness equation which
    should be used. Alternatively, a user can implement their own thickness model, either
    as an experimental isotherm or a function which describes the adsorbed layer. In that
    case, instead of a string, pass the Isotherm object or the callable function as the
    ``model`` parameter.

    Parameters
    ----------
    model : str or callable
        Name of the thickness model to use.

    Returns
    -------
    callable
        A callable that takes a pressure in and returns a thickness
        at that point.

    Raises
    ------
    ParameterError
        When string is not in the dictionary of models.
    """
    # If the model is a string, get a model from the _THICKNESS_MODELS
    if isinstance(model, str):
        if model not in _THICKNESS_MODELS:
            raise ParameterError(
                f"Model \"{model}\" not an implemented thickness function. ",
                f"Available models are {_THICKNESS_MODELS.keys()}"
            )

        return _THICKNESS_MODELS[model]

    # If the model is an callable, return it instead
    return model
