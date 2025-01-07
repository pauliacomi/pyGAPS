"""Module implementing the Whittaker method for isosteric enthalpy calculations."""

# TODO Remove after this program no longer support Python 3.8.*
from __future__ import annotations

import numpy as np
import scipy.constants

import pygaps.modelling as pgm
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.graphing.calc_graphs import isosteric_enthalpy_plot
from pygaps.units.converter_mode import c_temperature
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError


def enthalpy_sorption_whittaker(
    isotherm: BaseIsotherm,
    branch: str = 'ads',
    model: str = 'Toth',
    loading: list = None,
    verbose: bool = False,
    **kwargs,
):
    r"""

    Calculate the isosteric heat of adsorption, `\Delta H_{st}` using a single
    isotherm via the Whittaker method. Pass either a ModelIsotherm of a suitable
    model (Toth or Langmuir) or the model itself. Parameters of the model fit
    are then used to determine :math:`\Delta H_{st}`.

    Parameters
    ----------
    isotherm : BaseIsotherm
        The PointIsotherm or ModelIsotherm to be used. If ModelIsotherm, units must be in Pascal
    model : str
        The model to use to fit the PointIsotherm, must be either one of
        _WHITTAKER_MODELS.
    loading : list[float]
        The loadings for which to calculate the isosteric heat of adsorption.
    verbose : bool
        Whether to print out extra information and generate a graph.

    Returns
    -------
    result_dict : dict
        A dictionary with the isosteric enthalpies per loading, with the form:

        - ``enthalpy_sorption`` (array) : the isosteric enthalpy of adsorption in kJ/mol
        - ``loading`` (array) : the loading for each point of the isosteric enthalpy, in mmol/g
        - ``model_isotherm`` (ModelIsotherm): the model isotherm used to calculate the enthalpies.

    Raises
    ------
    ParameterError
        When incorrect type of model isotherm is used.

    Notes
    -----

    The Whittaker method, [#]_ sometimes known as a modified Tóth potential uses
    variables derived from fitting of a Toth-like model isotherm to derive the
    isosteric enthalpy of adsorption :math:`\Delta H_{st}`. Toth-like isotherms
    take the general form;

    n(P) = \sum_{i} n_{m_i} \frac{K_i P}{\sqrt[t_i]{1+(K_i P)^{t_i}}}

    And apart from Toth, include the multi- and single site Langmuir model
    (where all t_i are 1), and the chemiphysisorption model.

    The general form of the Whittaker potential is;

    .. math::

        \Delta H_{st} = \Delta \lambda + \Delta H_{vap} + RT

    Where :math:`\Delta \lambda` is the adsorption potential, and
    :math:`\Delta H_{vap}` is the latent heat of the liquid-vapour change at
    equilibrium pressure.

    For loadings below the triple point pressure, :math:`\Delta H_{vap}` is
    meaningless. In this case, :math:`\Delta H_{vap}` is estimated as that at
    the triple point.

    :math:`\Delta \lambda` is determined from the model isotherm parameters as :

    .. math::

        \Delta \lambda = R T \sum_{i} \ln{\left[ P_o K_i \left( \frac{\theta_i^{t_i}}
            {1 - \theta_i^{t_i}} \right )^{\frac{1-t_i}{t_i}} \right ]}

    Where :math:`P_0` is the saturation pressure, :math:`\theta` is the
    fractional coverage, and :math:`K` is the equilibrium constant. In the case
    that the adsorptive is supercritical, the Dubinin pseudo-saturation pressure
    is used;

    ..math::
        `p^0 = p_c \left(\frac{T}{T_c}\right)^2`.

    The exponent :math:`t` is not relevant for Langmuir models it reduces to 1.
    Thus, :math:`\Delta \lambda` becomes

    .. math::

        \Delta \lambda = RT \sum_{i} \ln{ \left( \frac{P_0}{K_i} \right) }

    As such, the Whittaker method predicts constant isosteric enthalpies of
    adsorption when Langmuir models are used.

    References
    ----------
    .. [#] "Predicting isosteric heats for gas adsorption.", Peter B.
      Whittaker, Xiaolin Wang, Klaus Regenauer-Lieb and Hui Tong Chua,
      Phys. Chem. Chem. Phys., 15.2, 473-482, (2013)

    """

    # Check if isotherm is correct
    if not isinstance(isotherm, (PointIsotherm, ModelIsotherm)):
        raise ParameterError(
            f'''
            Isotherm must be ModelIsotherm or PointIsotherm.
            You have input a {type(isotherm)}.
            '''
        )

    # Checks for ModelIsotherms provided
    if isinstance(isotherm, ModelIsotherm):
        if isotherm.units['pressure_unit'] != 'Pa':
            raise ParameterError(
                f'''
                Model isotherms should use pressure in Pascal.
                Current pressure unit is {isotherm.units['pressure_unit']}.
                '''
            )

        if not pgm.is_model_whittaker(isotherm.model.name):
            raise ParameterError(
                rf'''
                Whittaker method requires modelling with a T\'oth-type model, i.e.
                {*pgm._WHITTAKER_MODELS,}
                '''
            )

    # Checks for PointIsotherms provided
    if isinstance(isotherm, PointIsotherm):
        if model == 'guess':
            model = pgm._WHITTAKER_MODELS

        isotherm = copy_convert_isotherm(isotherm)
        max_nfev = kwargs.get('max_nfev', None)
        isotherm = pgm.model_iso(
            isotherm,
            branch=branch,
            model=model,
            verbose=verbose,
            optimization_params={'max_nfev': max_nfev},
        )

    if loading is None:
        loading = np.linspace(isotherm.model.loading_range[0], isotherm.model.loading_range[1], 100)

    #  Define constants
    adsorbate = isotherm.adsorbate
    T = isotherm.temperature
    p_c = adsorbate.p_critical()
    p_t = adsorbate.p_triple()
    p_sat = adsorbate.saturation_pressure(isotherm.temperature, pseudo='Dubinin')

    enthalpy = enthalpy_sorption_whittaker_raw(
        isotherm,
        loading,
        p_sat,
        p_c,
        p_t,
        T,
    )

    stderr = stderr_estimate(len(isotherm.model.params), isotherm.model.rmse, enthalpy)

    if verbose:
        isosteric_enthalpy_plot(
            loading,
            enthalpy,
            stderr,
            isotherm.units,
        )

    return {
        'loading': loading,
        'enthalpy_sorption': enthalpy,
        'model_isotherm': isotherm,
        'std_errs': stderr,
    }


def copy_convert_isotherm(isotherm: PointIsotherm):
    """
    Makes a copy of the isotherm, but with pressure converted to
    absolute mode and units in Pa, and temperature converted to K.
    For use in `enthalpy_sorption_whittaker`, so as not to modify the original
    input.

    Parameters
    ---------
    isotherm: PointIsotherm
        The isotherm to convert

    Returns
    ------
    converted isotherm: PointIsotherm
        New isotherm with all parameters the same as `isotherm` except with
        pressure converted to absolute and Pa, and temperature converted to K.
    """
    temperature = c_temperature(
        value=isotherm.temperature,
        unit_from=isotherm.units['temperature_unit'],
        unit_to='K',
    )

    return PointIsotherm(
        pressure=isotherm.pressure(pressure_unit='Pa', pressure_mode='absolute'),
        loading=isotherm.loading(),
        material=isotherm.material,
        adsorbate=str(isotherm.adsorbate),
        temperature=temperature,
        temperature_unit='K',
        pressure_mode='absolute',
        pressure_unit='Pa',
        loading_basis=isotherm.units['loading_basis'],
        loading_unit=isotherm.units['loading_unit'],
        material_basis=isotherm.units['material_basis'],
        material_unit='g',
    )


def pressure_at(
    isotherm: BaseIsotherm,
    n: float,
):
    """
    Wrapper for `isotherm.pressure_at()` which returns NAN on a
    `CalculationError`.

    Parameters
    ----------
    isotherm: BaseIsotherm
        isotherm to use
    n: float
        Loading from which to derive pressure

    Returns
    ------
    pressure at `n` if possible
    or `np.nan` if not.
    """
    try:
        return float(isotherm.pressure_at(n))
    except CalculationError as e:
        print(e)
        return np.nan


def vaporisation_enthalpy(
    adsorbate: Adsorbate,
    pressure: float,
    p_c: float,
    p_sat: float,
):
    """
    Wrapper for `adsorbate.enthalpy_vaporisation()` which returns NAN on a
    if it is impossible to calculate vaporisation enthalpy.

    Parameters
    ----------
    adsorbate: Adsorbate,
        Adsorbate for which to determine the vaporisiation enthalpy
    pressure: float,
        Pressure, in Pa at which to determine vaporisation enthalpy
    p_c: float,
        Critical pressure of the adsorbate, in Pa.
    p_sat: float,
        Saturation pressure of the adsorbate at the isotherm temperature.

    Returns
    ------
    adsorbate.enthalpy_vaporisation() in J/mol if possible, np.nan if not
    """
    if np.isnan(pressure) or pressure <= 0 or pressure > p_c or pressure > p_sat:
        return np.nan
    # return in J/mol
    return adsorbate.enthalpy_vaporisation(press=pressure) * 1000


def compressibility(
    adsorbate: Adsorbate,
    pressure: float,
    temperature: float,
    p_c: float,
    p_sat: float,
):
    """
    Wrapper for `adsorbate.compressibility()` which returns NAN on a
    if it is impossible to calculate compressibility.

    Parameters
    ----------
    adsorbate: Adsorbate,
        Adsorbate for which to determine the compressibility.
    pressure: float,
        Pressure, in Pa at which to determine compressibility.
    temperature: float,
        Isotherm temperature in K.
    p_c: float,
        Critical pressure of the adsorbate, in Pa.
    p_sat: float,
        Saturation pressure of the adsorbate at the isotherm temperature.

    Returns
    ------
    `adsorbate.compressibility()` if possible, np.nan if not
    """
    if np.isnan(pressure) or pressure <= 0 or pressure > p_c or pressure > p_sat:
        return np.nan
    return adsorbate.compressibility(temp=temperature, pressure=pressure)


def stderr_estimate(
    n_terms: int,
    rmse: float,
    enthalpy: list[float],
):
    r"""
    An estimation of the standard error of the isosteric enthalpy of adsorption
    calculation, based on the RMSE of the model fitting and the number of terms
    in the model.

    ..math::
        \sigma = 0.434 * \sqrt{n cdot RMSE^2}

    Parameters
    ----------
    n_terms: int,
        Number of terms in the model used to fit the isotherm
    rmse: float,
        root mean square error of model fit
    enthalpy: list[float],
        Isosteric enthalpy of adsorption

    Returns
    ------
    An estimate of standard error for each enthalpy, as a list[float]
    """
    absolute_uncertainty = 0.434 * (np.sqrt(n_terms * (rmse**2)))
    return [abs(absolute_uncertainty * h) for h in enthalpy]


def toth_adsorption_potential(
    model_isotherm: ModelIsotherm,
    pressure: float,
    p_sat: float,
    RT: float,
):
    r"""
    Calculates the T\'oth-corrected Polanyi adsorption potential,
    $\varepsilon_{ads}$
    ..math::
        \Psi = RT \ln{\Psi \frac{P_{sat}}{P}}

    Parameters
    ---------
    model_isotherm: ModelIsotherm,
        Model isotherm containing the parameters for calculation of $\Psi$.
    pressure: float,
        Pressure at which to calculate the adsorption potential, in Pa.
    p_sat: float,
        Saturation pressure of the adsorbate at the isotherm temperature, in Pa.
    RT: float,
        The product of the gas constant, $R$ and the isotherm temperature, $T$

    Returns
    -------
    The Adsorption potential, $\varepsilon_{ads}$ in J/mol

    """
    Psi = model_isotherm.model.toth_correction(pressure)
    return RT * np.log(Psi * (p_sat / pressure))


def enthalpy_sorption_whittaker_raw(
    model_isotherm: ModelIsotherm,
    loading: list[float],
    p_sat: float,
    p_c: float,
    p_t: float,
    T: float,
):
    RT = scipy.constants.R * T
    adsorbate = model_isotherm.adsorbate

    pressure = [pressure_at(model_isotherm, n) for n in loading]

    epsilon = [toth_adsorption_potential(model_isotherm, p, p_sat, RT) for p in pressure]
    hvap = [vaporisation_enthalpy(adsorbate, max(p, p_t), p_c, p_sat) for p in pressure]
    Zfactor = [compressibility(adsorbate, p, T, p_c, p_sat) for p in pressure]

    # Sum adsorption potential, vaporisation enthalpy, ZRT
    return [
        (e + h + (Z * RT)) / 1000  # return in kJ/mol
        for e, h, Z in zip(epsilon, hvap, Zfactor)
    ]
