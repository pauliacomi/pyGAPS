"""
Module contains 'classical' methods of calculating
a pore size distribution for pores in
the micropore range (<2 nm).
"""

from typing import List
from typing import Mapping

import numpy
import scipy.constants as const
import scipy.optimize as opt

from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import psd_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from .models_hk import HK_KEYS
from .models_hk import get_hk_model

_MICRO_PSD_MODELS = ['HK', 'CY']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def psd_microporous(
    isotherm,
    psd_model='HK',
    pore_geometry='slit',
    branch='ads',
    adsorbent_model='Carbon(HK)',
    adsorbate_model=None,
    p_limits=None,
    verbose=False
):
    """
    Calculate the microporous size distribution using a 'classical' model.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm for which the pore size distribution will be calculated.
    psd_model : str
        The pore size distribution model to use.
    pore_geometry : str
        The geometry of the adsorbent pores.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    adsorbent_model : str or dict
        The adsorbent model to use for PSD, It defaults to Carbon(HK).
    adsorbate_model : dict or `None`
        The adsorbate properties to use for PSD, If null, properties are
        automatically searched from the Adsorbent.
    p_limits : [float, float]
        Pressure range in which to calculate PSD, defaults to [0, 0.2].
    verbose : bool
        Prints out extra information on the calculation and graphs the results.

    Returns
    -------
    dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths`` (array) : the widths of the pores
            - ``pore_distribution`` (array) : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore of specific width w at a relative pressure p/p0
    as a single function :math:`p/p0 = f(w)`. This function uses properties of the
    adsorbent and adsorbate as a way of determining the pore size distribution.

    Currently, the methods provided are:

        - the HK, or Horvath-Kawazoe method
        - the CY, or Cheng-Yang nonlinear corrected HK method

    A common mantra of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    See Also
    --------
    pygaps.characterisation.psd_microporous.psd_horvath_kawazoe : low level HK (Horvath-Kawazoe) method

    """
    # Function parameter checks
    if psd_model is None:
        raise ParameterError(
            "Specify a model to generate the pore size"
            " distribution e.g. psd_model=\"HK\""
        )
    if psd_model not in _MICRO_PSD_MODELS:
        raise ParameterError(
            f"Model {psd_model} not an option for psd. "
            f"Available models are {_MICRO_PSD_MODELS}"
        )
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError(
            f"Geometry {pore_geometry} not an option for pore size distribution. "
            f"Available geometries are {_PORE_GEOMETRIES}"
        )
    if branch not in ['ads', 'des']:
        raise ParameterError(
            f"Branch '{branch}' not an option for PSD.",
            "Select either 'ads' or 'des'"
        )

    # Get adsorbate properties
    if adsorbate_model is None:
        if not isinstance(isotherm.adsorbate, Adsorbate):
            raise ParameterError(
                "Isotherm adsorbate is not known, cannot calculate PSD."
                "Either use a recognised adsorbate (i.e. nitrogen) or "
                "pass a dictionary with your adsorbate parameters."
            )
        adsorbate_model = {
            'molecular_diameter':
            isotherm.adsorbate.get_prop('molecular_diameter'),
            'polarizability':
            isotherm.adsorbate.get_prop('polarizability'),
            'magnetic_susceptibility':
            isotherm.adsorbate.get_prop('magnetic_susceptibility'),
            'surface_density':
            isotherm.adsorbate.get_prop('surface_density'),
            'liquid_density':
            isotherm.adsorbate.liquid_density(isotherm.temperature),
            'adsorbate_molar_mass':
            isotherm.adsorbate.molar_mass(),
        }

    # Get adsorbent properties
    adsorbent_properties = get_hk_model(adsorbent_model)

    # Read data in
    loading = isotherm.loading(
        branch=branch, loading_basis='molar', loading_unit='mmol'
    )
    pressure = isotherm.pressure(branch=branch, pressure_mode='relative')
    if loading is None:
        raise ParameterError(
            "The isotherm does not have the required branch "
            "for this calculation"
        )
    # If on an desorption branch, data will be reversed
    if branch == 'des':
        loading = loading[::-1]
        pressure = pressure[::-1]

    # Determine the limits
    if not p_limits:
        p_limits = (None, 0.2)
    minimum = 0
    maximum = len(pressure)
    if p_limits[0]:
        minimum = numpy.searchsorted(pressure, p_limits[0])
    if p_limits[1]:
        maximum = numpy.searchsorted(pressure, p_limits[1])
    if maximum - minimum < 3:  # (for 3 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 3) "
            "in the selected region."
        )
    pressure = pressure[minimum:maximum]
    loading = loading[minimum:maximum]

    # Call specified pore size distribution function
    if psd_model == 'HK':
        pore_widths, pore_dist, pore_vol_cum = psd_horvath_kawazoe(
            pressure,
            loading,
            isotherm.temperature,
            pore_geometry,
            adsorbate_model,
            adsorbent_properties,
        )
    elif psd_model == 'CY':
        pass

    if verbose:
        psd_plot(
            pore_widths,
            pore_dist,
            pore_vol_cum=pore_vol_cum,
            log=False,
            right=2.5,
            method=psd_model
        )

    return {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
        'pore_volume_cumulative': pore_vol_cum,
    }


def psd_horvath_kawazoe(
    pressure: List[float],
    loading: List[float],
    temperature: float,
    pore_geometry: str,
    adsorbate_properties: Mapping[str, float],
    adsorbent_properties: Mapping[str, float],
):
    r"""
    Calculate the pore size distribution using the Horvath-Kawazoe method.

    Parameters
    ----------
    loading : array
        Adsorbed amount in mmol/g.
    pressure : array
        Relative pressure.
    temperature : float
        Temperature of the experiment, in K.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    adsorbate_properties : dict
        Properties for the adsorbate in the form of::

            adsorbate_properties = dict(
                'molecular_diameter'=0,           # nm
                'polarizability'=0,               # nm3
                'magnetic_susceptibility'=0,      # nm3
                'surface_density'=0,              # molecules/m2
                'liquid_density'=0,               # g/cm3
                'adsorbate_molar_mass'=0,         # g/mol
            )

    adsorbent_properties : dict
        Properties for the adsorbate in the same form
        as 'adsorbate_properties'. A list of common models
        can be found in .characterisation.models_hk.

    Returns
    -------
    pore widths : array
        The widths of the pores.
    pore_dist : array
        The distributions for each width.
    pore_vol_cum : array
        Cumulative pore volume.

    Notes
    -----

    *Description*

    The H-K method [#]_ attempts to describe the adsorption within pores by calculation
    of the average potential energy for a pore. The method starts by assuming the
    relationship between the gas phase as being:

    .. math::

        R_g T \ln(\frac{p}{p_0}) = U_0 + P_a

    Here :math:`U_0` is the potential function describing the surface to adsorbent
    interactions and :math:`P_a` is the potential function describing the adsorbate-
    adsorbate interactions. This equation is derived from the equation of the free energy
    of adsorption at constant temperature where term :math:`T \Delta S^{tr}(w/w_{\infty})`
    is assumed to be negligible.

    If a Lennard-Jones-type potential function describes the interactions between the
    adsorbate molecules and the adsorbent molecules then the two contributions to the
    total potential can be replaced by the extended function. The resulting equation becomes:

    .. math::

        RT\ln(p/p_0) =   & N_A\frac{n_a A_a + n_A A_A}{2 \sigma^{4}(l-d)} \\
                        & \times \int_{d/_2}^{1-d/_2}
                            \Big[
                            - \Big(\frac{\sigma}{r}\Big)^{4}
                            + \Big(\frac{\sigma}{r}\Big)^{10}
                            - \Big(\frac{\sigma}{l-r}\Big)^{4}
                            + \Big(\frac{\sigma}{l-r}\Big)^{4}
                            \Big] \mathrm{d}x

    Where:

    * :math:`R` -- gas constant
    * :math:`T` -- temperature
    * :math:`l` -- width of pore
    * :math:`d` -- defined as :math:`d=d_a+d_A` the sum of the diameters of the adsorbate and
      adsorbent molecules
    * :math:`N_A` -- Avogadro's number
    * :math:`n_a` -- number of molecules of adsorbent
    * :math:`A_a` -- the Lennard-Jones potential constant of the adsorbent molecule defined as

        .. math::
            A_a = \frac{6mc^2\alpha_a\alpha_A}{\alpha_a/\varkappa_a + \alpha_A/\varkappa_A}

    * :math:`A_A` -- the Lennard-Jones potential constant of the adsorbate molecule defined as

        .. math::
            A_a = \frac{3 m_e c_l ^2\alpha_A\varkappa_A}{2}

    * :math:`m_e` -- mass of an electron
    * :math:`c_l` -- speed of light in vacuum
    * :math:`\alpha_a` -- polarizability of the adsorbate molecule
    * :math:`\alpha_A` -- polarizability of the adsorbent molecule
    * :math:`\varkappa_a` -- magnetic susceptibility of the adsorbate molecule
    * :math:`\varkappa_A` -- magnetic susceptibility of the adsorbent molecule


    *Limitations*

    The assumptions made by using the H-K method are:

        - It does not have a description of capillary condensation. This means that the
          pore size distribution can only be considered accurate up to a maximum of 5 nm.

        - Each pore is uniform and of infinite length. Materials with varying pore
          shapes or highly interconnected networks may not give realistic results.

        - The wall is made up of single layer atoms. Furthermore, since the HK method
          is reliant on knowing the properties of the surface atoms as well as the
          adsorbent molecules the material should ideally be homogenous.

        - Only dispersive forces are accounted for. If the adsorbate-adsorbent interactions
          have other contributions, the Lennard-Jones potential function will not be
          an accurate description of pore environment.

    References
    ----------
    .. [#] K. Kutics, G. Horvath, Determination of Pore size distribution in MSC from
       Carbon-dioxide Adsorption Isotherms, 86

    """
    # Parameter checks
    missing = [x for x in adsorbent_properties if x not in HK_KEYS]
    if missing:
        raise ParameterError(
            f"Adsorbent properties dictionary is missing parameters: {missing}."
        )

    missing = [
        x for x in adsorbate_properties if x not in list(HK_KEYS.keys()) +
        ['liquid_density', 'adsorbate_molar_mass']
    ]
    if missing:
        raise ParameterError(
            f"Adsorbate properties dictionary is missing parameters: {missing}."
        )

    # ensure numpy arrays
    pressure = numpy.asarray(pressure)
    loading = numpy.asarray(loading)

    if pore_geometry == 'slit':
        pore_widths = _hk_slit_raw(
            pressure, temperature, adsorbate_properties, adsorbent_properties
        )
    elif pore_geometry == 'cylinder':
        pore_widths = _hk_cylinder_raw(
            pressure, temperature, adsorbate_properties, adsorbent_properties
        )
    elif pore_geometry == 'sphere':
        pore_widths = _hk_sphere_raw(
            pressure, temperature, adsorbate_properties, adsorbent_properties
        )

    # finally calculate pore distribution
    liquid_density = adsorbate_properties['liquid_density']
    adsorbate_molar_mass = adsorbate_properties['adsorbate_molar_mass']

    avg_pore_widths = numpy.add(pore_widths[:-1], pore_widths[1:]) / 2  # nm
    volume_adsorbed = loading * adsorbate_molar_mass / liquid_density / 1000  # cm3/g
    pore_dist = numpy.diff(volume_adsorbed) / numpy.diff(pore_widths)

    return avg_pore_widths, pore_dist, volume_adsorbed[1:]


def _hk_slit_raw(pressure, temp, adsorbate_properties, adsorbent_properties):

    # dictionary unpacking
    d_gas = adsorbate_properties['molecular_diameter']
    d_mat = adsorbent_properties['molecular_diameter']
    p_gas = adsorbate_properties['polarizability'] * 1e-27  # to m3
    p_mat = adsorbent_properties['polarizability'] * 1e-27  # to m3
    m_gas = adsorbate_properties['magnetic_susceptibility'] * 1e-27  # to m3
    m_mat = adsorbent_properties['magnetic_susceptibility'] * 1e-27  # to m3
    n_gas = adsorbate_properties['surface_density']
    n_mat = adsorbent_properties['surface_density']

    # HK starts
    # NOTE: ~30 ms
    # constants and constant term calculation
    d_eff = (d_gas + d_mat) / 2  # effective diameter
    sigma = (2 / 5)**(1 / 6) * d_eff  # distance from atom at 0 potential
    sigma_p4_o3 = sigma**4 / 3  # sigma^4 / 3
    sigma_p10_o9 = sigma**10 / 9  # sigma^10 / 9

    a_mat = 6 * const.electron_mass * const.speed_of_light**2 * \
        p_gas * p_mat / (p_gas / m_gas + p_mat / m_mat)
    a_gas = 1.5 * const.electron_mass * const.speed_of_light**2 * p_gas * m_gas

    const_coeff = const.Avogadro / (const.gas_constant * temp) * \
        (n_gas * a_gas + n_mat * a_mat) / (sigma * 1e-9)**4  # sigma must be in SI

    const_term = (sigma_p10_o9 / (d_eff**9) - sigma_p4_o3 / (d_eff**3))  # nm

    def h_k_pressure(l_pore):
        return numpy.exp(
            const_coeff / (l_pore - 2 * d_eff) *
            ((sigma_p4_o3 / (l_pore - d_eff)**3) -
             (sigma_p10_o9 / (l_pore - d_eff)**9) + const_term)
        )

    p_w = []

    # I personally found that simple Brent minimization
    # gives good results. There may be other, more efficient
    # algorithms, like conjugate gradient, but speed is a moot point
    # as long as average total runtime is <50 ms.
    # The minimisation runs with bounds of effective diameter < x < 50.
    # Maximum determinable pore size is limited at 2.5 nm anyway.
    for p_point in pressure:

        def fun(l_pore):
            return (h_k_pressure(l_pore) - p_point)**2

        res = opt.minimize_scalar(fun, method='bounded', bounds=(d_eff, 50))
        p_w.append(res.x - d_mat)  # Effective pore size

    return numpy.asarray(p_w)


def _hk_cylinder_raw(
    pressure, temp, adsorbate_properties, adsorbent_properties
):
    # dictionary unpacking
    d_gas = adsorbate_properties['molecular_diameter']  # nm
    d_mat = adsorbent_properties['molecular_diameter']  # nm
    p_gas = adsorbate_properties['polarizability'] * 1e-27  # to m3
    p_mat = adsorbent_properties['polarizability'] * 1e-27  # to m3
    m_gas = adsorbate_properties['magnetic_susceptibility'] * 1e-27  # to m3
    m_mat = adsorbent_properties['magnetic_susceptibility'] * 1e-27  # to m3
    n_gas = adsorbate_properties['surface_density']
    n_mat = adsorbent_properties['surface_density']

    # SF starts
    # constants and constant term calculation
    d_eff = (d_gas + d_mat) / 2  # effective diameter
    a_mat = 6 * const.electron_mass * const.speed_of_light**2 * \
        p_gas * p_mat / (p_gas / m_gas + p_mat / m_mat)
    a_gas = 1.5 * const.electron_mass * const.speed_of_light**2 * p_gas * m_gas

    const_coeff = (3 / 4) * const.pi * const.Avogadro / (const.gas_constant * temp) * \
        (n_gas * a_gas + n_mat * a_mat) / (d_eff * 1e-9)**4  # d_eff must be in SI

    def s_f_pressure(r_pore):

        a_k = 1
        b_k = 1
        n = 21 / 32
        d_over_r = d_eff / r_pore  # dimensionless
        k_sum = n * d_over_r**10 - d_over_r**4  # first value at K=0

        # 30 * pore radius ensures that layer convergence is achieved
        for k in range(1, int(r_pore * 30)):
            a_k = ((-4.5 - k) / k)**2 * a_k
            b_k = ((-1.5 - k) / k)**2 * b_k
            k_sum = k_sum + ((1 / (2 * k + 1) * (1 - d_over_r)**(2 * k)) *
                             (n * a_k * (d_over_r)**10 - b_k * (d_over_r)**4))

        return numpy.exp(const_coeff * k_sum)

    p_w = []

    # I personally found that simple Brent minimization
    # gives good results. There may be other, more efficient
    # algorithms, like conjugate gradient, but speed is a moot point
    # as long as average total runtime is <50 ms.
    # The minimisation runs with bounds of effective diameter < x < 100.
    # Maximum determinable pore size is limited at 2.5 nm anyway.
    for p_point in pressure:

        def fun(r_pore):
            return (s_f_pressure(r_pore) - p_point)**2

        res = opt.minimize_scalar(fun, method='bounded', bounds=(d_eff, 100))
        p_w.append(2 * res.x - d_mat)  # Effective pore size

    return numpy.asarray(p_w)


def _hk_sphere_raw(pressure, temp, adsorbate_properties, adsorbent_properties):

    # dictionary unpacking
    d_gas = adsorbate_properties['molecular_diameter']
    d_mat = adsorbent_properties['molecular_diameter']
    p_gas = adsorbate_properties['polarizability'] * 1e-27  # to m3
    p_mat = adsorbent_properties['polarizability'] * 1e-27  # to m3
    m_gas = adsorbate_properties['magnetic_susceptibility'] * 1e-27  # to m3
    m_mat = adsorbent_properties['magnetic_susceptibility'] * 1e-27  # to m3
    n_gas = adsorbate_properties['surface_density']
    n_mat = adsorbent_properties['surface_density']

    # CY starts
    # constants and constant term calculation
    d_eff = (d_gas + d_mat) / 2  # effective diameter

    a_mat = 6 * const.electron_mass * const.speed_of_light**2 * \
        p_gas * p_mat / (p_gas / m_gas + p_mat / m_mat)
    a_gas = 1.5 * const.electron_mass * const.speed_of_light**2 * p_gas * m_gas

    p_12 = a_mat / (4 * (d_eff * 1e-9)**6)  # 1-2 potential
    p_22 = a_gas / (4 * (d_gas * 1e-9)**6)  # 2-2 potential
    c1 = const.Avogadro / (const.gas_constant * temp)

    def c_y_pressure(l_pore):

        l_minus_d = l_pore - d_eff
        d_over_l = d_eff / l_pore

        n_1 = 4 * const.pi * (l_pore * 1e-9)**2 * n_mat
        n_2 = 4 * const.pi * (l_minus_d * 1e-9)**2 * n_gas

        def t_term(x):
            return (1 / (1 + (-1)**x * l_minus_d / l_pore)**x) -\
                   (1 / (1 - (-1)**x * l_minus_d / l_pore)**x)

        c2 = 6 * (n_1 * p_12 + n_2 * p_22) * l_pore**3 / l_minus_d**3
        coef = (
            -(d_over_l**6) * (1 / 12 * t_term(3) - 1 / 8 * t_term(2)) +
            (d_over_l**12) * (1 / 90 * t_term(9) - 1 / 80 * t_term(8))
        )

        return numpy.exp(c1 * c2 * coef)

    p_w = []

    # I personally found that simple Brent minimization
    # gives good results. There may be other, more efficient
    # algorithms, like conjugate gradient, but speed is a moot point
    # as long as average total runtime is <50 ms.
    # The minimisation runs with bounds of effective diameter < x < 50.
    # Maximum determinable pore size is limited at 2.5 nm anyway.
    for p_point in pressure:

        def fun(l_pore):
            return (c_y_pressure(l_pore) - p_point)**2

        res = opt.minimize_scalar(fun, method='bounded', bounds=(d_eff, 50))
        p_w.append(res.x - d_mat)  # Effective pore size

    return numpy.asarray(p_w)
