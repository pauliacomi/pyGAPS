"""
This module contains 'classical' methods of calculating a pore size distribution for
pores in the micropore range (<2 nm). These are derived from the Horvath-Kawazoe models.
"""

import math
import typing as t

import numpy

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..core.baseisotherm import BaseIsotherm
from ..graphing.calc_graphs import psd_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.exceptions import pgError
from .models_hk import HK_KEYS
from .models_hk import get_hk_model

_MICRO_PSD_MODELS = ['HK', 'HK-CY', 'RY', 'RY-CY']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def psd_microporous(
    isotherm: BaseIsotherm,
    psd_model: str = 'HK',
    pore_geometry: str = 'slit',
    branch: str = 'ads',
    material_model: str = 'Carbon(HK)',
    adsorbate_model: str = None,
    p_limits: t.List[float] = None,
    verbose: bool = False
) -> t.Mapping:
    r"""
    Calculate the microporous size distribution using a Horvath-Kawazoe type model.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm for which the pore size distribution will be calculated.
    psd_model : str
        Pore size distribution model to use. Available are 'HK' (original Horvath-Kawazoe),
        'RY' (Rege-Yang correction) or the Cheng-Yang modification to the two models ('HK-CY', 'RY-CY').
    pore_geometry : str
        The geometry of the adsorbent pores.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    material_model : str or dict
        The material model to use for PSD, It defaults to 'Carbon(HK)', the original
        Horvath-Kawazoe activated carbon parameters.
    adsorbate_model : dict or `None`
        The adsorbate properties to use for PSD, If empty, properties are
        automatically searched from internal database for the Adsorbate.
    p_limits : [float, float]
        Pressure range in which to calculate PSD, defaults to [0, 0.2].
    verbose : bool
        Print out extra information on the calculation and graphs the results.

    Returns
    -------
    dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths`` (array) : the widths of the pores
            - ``pore_distribution`` (array) : contribution of each pore width to the
              overall pore distribution

    Notes
    -----

    Calculates the pore size distribution using a "classical" model, which
    describes adsorption in micropores as a sequential instant filling of
    increasingly wider pores. The pressure of filling for each pore is
    determined by relating the global adsorption potential,
    :math:`RT \ln(p/p_0)`, with the energetic potential of individual adsorbate
    molecules in a pore of a particular geometry :math:`\Phi`. Calculation of
    the latter is based on the Lennard-Jones 6-12 intermolecular potential,
    incorporating both guest-host and guest-guest dispersion contributions
    through the Kirkwood-Muller formalism. The function is then solved
    numerically. These methods are necessarily approximations, as besides using
    a semi-empirical mathematical model, they are also heavily dependent on the
    material and adsorbate properties (polarizability and susceptibility) used
    to derive dispersion coefficients.

    There are two main approaches which pyGAPS implements, chosen by passing
    the ``psd_model`` parameter:

        - The "HK", or the original Horvath-Kawazoe method [#hk1]_.
        - The "RY", or the modified Rege-Yang method [#ry1]_.

    Detailed explanations for both methods can be found in
    :py:func:`~pygaps.characterisation.psd_microporous.psd_horvath_kawazoe` and
    :py:func:`~pygaps.characterisation.psd_microporous.psd_horvath_kawazoe_ry`,
    respectively. Additionally for both models, the Cheng-Yang correction
    [#cy1]_ can be applied by appending *"-CY"*, such as ``psd_model="HK-CY"``
    or ``"RY-CY"``. This correction attempts to change the expression for the
    thermodynamic potential from a Henry-type to a Langmuir-type isotherm. While
    this new expression does not remain consistent at high pressures, it may
    better represent the isotherm curvature at low pressure [#ry1]_.

    .. math::

        \Phi = RT\ln(p/p_0) + RT (1 + \frac{\ln(1-\theta)}{\theta})

    Currently, three geometries are supported for each model: slit-like pores,
    cylindrical pores and spherical pores, as described in the related papers
    [#hk1]_ [#sf1]_ [#cy1]_ [#ry1]_.

    .. caution::

        A common mantra of data processing is: **garbage in = garbage out**. Only use
        methods when you are aware of their limitations and shortcomings.

    References
    ----------
    .. [#hk1] G. Horvath and K. Kawazoe, "Method for Calculation of Effective Pore
       Size Distribution in Molecular Sieve Carbon", J. Chem. Eng. Japan, 16, 470
       1983.
    .. [#sf1] A. Saito and H. C. Foley, "Curvature and Parametric Sensitivity in
       Models for Adsorption in Micropores", AIChE J., 37, 429, 1991.
    .. [#cy1] L. S. Cheng and R. T. Yang, "Improved Horvath-Kawazoe Equations
       Including Spherical Pore Models for Calculating Micropore Size
       Distribution", Chem. Eng. Sci., 49, 2599, 1994.
    .. [#ry1] S. U. Rege and R. T. Yang, "Corrected Horváth-Kawazoe equations for
       pore-size distribution", AIChE Journal, vol. 46, no. 4, pp. 734–750, Apr.
       2000.

    See Also
    --------
    pygaps.characterisation.psd_microporous.psd_horvath_kawazoe : low level HK (Horvath-Kawazoe) method
    pygaps.characterisation.psd_microporous.psd_horvath_kawazoe_ry : low level RY (Rege-Yang) method

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

    # Get material properties
    material_properties = get_hk_model(material_model)

    # Read data in
    loading = isotherm.loading(
        branch=branch, loading_basis='molar', loading_unit='mmol'
    )
    if loading is None:
        raise ParameterError(
            "The isotherm does not have the required branch "
            "for this calculation"
        )
    try:
        pressure = isotherm.pressure(branch=branch, pressure_mode='relative')
    except pgError:
        raise CalculationError(
            "The isotherm cannot be converted to a relative basis. "
            "Is your isotherm supercritical?"
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
    if psd_model in ['HK', 'HK-CY']:
        pore_widths, pore_dist, pore_vol_cum = psd_horvath_kawazoe(
            pressure,
            loading,
            isotherm.temperature,
            pore_geometry,
            adsorbate_model,
            material_properties,
            use_cy=False if psd_model == 'HK' else True,
        )
    elif psd_model in ['RY', 'RY-CY']:
        pore_widths, pore_dist, pore_vol_cum = psd_horvath_kawazoe_ry(
            pressure,
            loading,
            isotherm.temperature,
            pore_geometry,
            adsorbate_model,
            material_properties,
            use_cy=False if psd_model == 'RY' else True,
        )

    if verbose:
        psd_plot(
            pore_widths,
            pore_dist,
            pore_vol_cum=pore_vol_cum,
            log=False,
            right=5,
            method=psd_model
        )

    return {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
        'pore_volume_cumulative': pore_vol_cum,
    }


def psd_horvath_kawazoe(
    pressure: t.List[float],
    loading: t.List[float],
    temperature: float,
    pore_geometry: str,
    adsorbate_properties: t.Mapping[str, float],
    material_properties: t.Mapping[str, float],
    use_cy: bool = False,
):
    r"""
    Calculate the pore size distribution using the Horvath-Kawazoe method.

    Parameters
    ----------
    pressure : array
        Relative pressure.
    loading : array
        Adsorbed amount in mmol/g.
    temperature : float
        Temperature of the experiment, in K.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    adsorbate_properties : dict
        Properties for the adsorbate in the form of::

            adsorbate_properties = dict(
                'molecular_diameter': 0,           # nm
                'polarizability': 0,               # nm3
                'magnetic_susceptibility': 0,      # nm3
                'surface_density': 0,              # molecules/m2
                'liquid_density': 0,               # g/cm3
                'adsorbate_molar_mass': 0,         # g/mol
            )

    material_properties : dict
        Properties for the adsorbate in the same form
        as 'adsorbate_properties'. A list of common models
        can be found in .characterisation.models_hk.
    use_cy : bool:
        Whether to use the Cheng-Yang nonlinear Langmuir term.

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

    The H-K method [#hk2]_ attempts to describe adsorption within pores by
    calculation of the average potential energy for a pore and equating it to
    the change in free energy upon adsorption. The method starts by assuming the
    following relationship between the two:

    .. math::

        \Phi = RT \ln(p/p_0) = U_0 + P_a

    Here :math:`U_0` is the potential describing the surface to adsorbent
    interactions and :math:`P_a` is the potential describing the
    adsorbate-adsorbate interactions. This relationship is derived from the
    equation of the free energy of adsorption at constant temperature where the
    adsorption entropy term :math:`T \Delta S^{tr}(\theta)` is assumed to be
    negligible. :math:`R`, :math:`T`, and :math:`p` are the gas constant,
    temperature and pressure, respectively. The expression for the guest-host
    and host-host interaction in the pore is then modelled on the basis of the
    Lennard-Jones 12-6 potential. For two molecules 1 and 2:

    .. math::

        \epsilon_{12}(z) = 4 \epsilon^{*}_{12} \Big[(\frac{\sigma}{z})^{12} - (\frac{\sigma}{z})^{6}\Big]

    Where :math:`z` is intermolecular distance, :math:`\epsilon^{*}` is the
    depth of the potential well and :math:`\sigma` is the zero-interaction
    energy distance. The two molecules can be identical, or different species.

    The distance at zero-interaction energy, commonly defined as the "rest
    internuclear distance", is a function of the diameter of the molecules
    involved, and is calculated as :math:`\sigma = (2/5)^{1/6} d_0`. If the two
    molecules are different, :math:`d_0` is the average of the diameter of the
    two, :math:`d_0=(d_g + d_h)/2` such as between the guest and host molecules.
    In the case of multiple surface atom types (as for zeolites), representative
    averages are used.

    The depth of the potential well is obtained using the Kirkwood-Muller
    formalism, which relates molecular polarizability :math:`\alpha` and
    magnetic susceptibility :math:`\varkappa` to the specific dispersion
    constant. For guest-host (:math:`A_{gh}`) and guest-guest (:math:`A_{gg}`)
    interactions they are calculated through:

    .. math::

        A_{gh} = \frac{6mc^2\alpha_g\alpha_h}{\alpha_g/\varkappa_g + \alpha_h/\varkappa_h} \\
        A_{gg} = \frac{3}{2} m_e c ^2 \alpha_g\varkappa_g

    In the above formulas, :math:`m_e` is the mass of an electron and :math:`c`
    is the speed of light in a vacuum. This potential equation
    (:math:`\epsilon`) is then applied to the specific geometry of the pore
    (e.g. potential of an adsorbate molecule between two infinite surface
    slits). Individual molecular contributions as obtained through these
    expressions are multiplied by average surface densities for the guest
    (:math:`n_g`) and the host (:math:`n_h`) and then scaled to moles by using
    Avogadro's number :math:`N_A`. By integrating over the specific pore
    dimension (width, radius) an average potential for a specific pore size is
    obtained.

    *Slit pore*

    The original model was derived for a slit-like pore, with each pore modelled
    as two parallel infinite planes between which adsorption took place.
    [#hk2]_ The effective width of the pore is related to the characterisic
    length by, :math:`W = L - d_h` and the following relationship is derived:

    .. math::

        RT\ln(p/p_0) =  & N_A\frac{n_h A_{gh} + n_g A_{gh} }{\sigma^{4}(L-2d_0)} \\
                        & \times
                            \Big[
                              \Big(\frac{\sigma^{10}}{9 d_0^9}\Big)
                            - \Big(\frac{\sigma^{4}}{3 d_0^3}\Big)
                            - \Big(\frac{\sigma^{10}}{9(L-d_0)^{9}}\Big)
                            + \Big(\frac{\sigma^{4}}{3(L - d_0)^{3}}\Big)
                            \Big]

    *Cylindrical pore*

    Using the same procedure, a cylindrical model was proposed by Saito and
    Foley [#sf2]_ using pore radius :math:`L` as the representative length
    (therefore pore width :math:`W = 2L - d_h`), and involves a summation of
    probe-wall interactions for sequential axial rings of the cylinder up to
    infinity.

    .. math::

        RT\ln(p/p_0) =  & \frac{3}{4}\pi N_A \frac{n_h A_{gh} + n_g A_{gg} }{d_0^{4}} \\
                        & \times
                            \sum^{\infty}_{k = 0} \frac{1}{k+1} \Big( 1 - \frac{d_0}{L} \Big)^{2k}
                            \Big[
                             \frac{21}{32} \alpha_k \Big(\frac{d_0}{L}\Big)^{10}
                             - \beta_k \Big(\frac{d_0}{L}\Big)^{4}
                            \Big]

    Where the constants :math:`\alpha_k` and :math:`\beta` are recursively
    calculated from :math:`\alpha_0 = \beta_0 = 1`:

    .. math::

        \alpha_k = \Big( \frac{-4.5-k}{k} \Big)^2 \alpha_{k-1} \ \text{and}
        \ \beta_k = \Big( \frac{-1.5-k}{k} \Big)^2 \beta_{k-1}

    *Spherical pore*

    Similarly, Cheng and Yang [#cy2]_ introduced an extension for spherical
    pores by considering the interactions with a spherical cavity. This model
    similarly uses the sphere radius :math:`L` as the representative length
    (therefore effective pore width :math:`W = 2L - d_h`) It should be noted
    that realistic spherical pores would not have any communication with the
    adsorbent exterior.

    .. math::

        RT\ln(p/p_0) =  & N_A 6 \Big( n_1 \frac{A_{gh}}{4 d_0^6} + n_2 \frac{A_{gg}}{4 d_g^6} \Big)
                          \frac{L^3}{(L-d_0)^{3}} \\
                        & \times
                            \Big[
                              \Big( \frac{d_0}{L} \Big)^{12} \Big( \frac{T_9}{90} - \frac{T_8}{80} \Big)
                            - \Big( \frac{d_0}{L} \Big)^{6} \Big( \frac{T_3}{12} - \frac{T_2}{8} \Big)
                            \Big]

    Here, :math:`T_x` stands for a function of the type:

    .. math::

        T_x = \Big[1 + (-1)^{x} \frac{L-d_0}{L} \Big]^{-x} -
              \Big[1 - (-1)^{x} \frac{L-d_0}{L} \Big]^{-x}

    While the population densities for guest and host :math:`n_1` and
    :math:`n_2` are calculated from the plane values as
    :math:`n_0 = 4\pi L^2 n_h` and :math:`n_i = 4\pi (L - d_0)^2 n_g`.\

    *Limitations*

    The main assumptions made by using the H-K method are:

        - It does not have a description of capillary condensation. This means
          that the pore size distribution can only be considered accurate up to
          a maximum of 5 nm.

        - The surface is made up of a single layer of atoms. Furthermore, since
          the HK method is reliant on knowing the properties of the surface
          atoms as well as the adsorbate molecules the material should ideally
          be homogenous.

        - Only dispersive forces are accounted for. If the adsorbate-adsorbent
          interactions have other contributions, such as charged interactions,
          the Lennard-Jones potential function will not be an accurate
          description of pore environment.

        - Each pore is uniform and of infinite length. Materials with varying
          pore shapes or highly interconnected networks may not give realistic
          results.

    References
    ----------
    .. [#hk2] G. Horvath and K. Kawazoe, Method for Calculation of Effective Pore
       Size Distribution in Molecular Sieve Carbon, J. Chem. Eng. Japan, 16, 470 1983.
    .. [#sf2] A. Saito and H. C. Foley, Curvature and Parametric Sensitivity in
       Models for Adsorption in Micropores, AIChE J., 37, 429, 1991.
    .. [#cy2] L. S. Cheng and R. T. Yang, ‘‘Improved Horvath-Kawazoe Equations
       Including Spherical Pore Models for Calculating Micropore Size
       Distribution,’’ Chem. Eng. Sci., 49, 2599, 1994.


    """
    # Parameter checks
    missing = [x for x in HK_KEYS if x not in material_properties]
    if missing:
        raise ParameterError(
            f"Adsorbent properties dictionary is missing parameters: {missing}."
        )

    missing = [
        x for x in list(HK_KEYS.keys()) +
        ['liquid_density', 'adsorbate_molar_mass']
        if x not in adsorbate_properties
    ]
    if missing:
        raise ParameterError(
            f"Adsorbate properties dictionary is missing parameters: {missing}."
        )

    # ensure numpy arrays
    pressure = numpy.asarray(pressure)
    loading = numpy.asarray(loading)
    pore_widths = []

    # Constants unpacking and calculation
    d_ads = adsorbate_properties['molecular_diameter']
    d_mat = material_properties['molecular_diameter']
    n_ads = adsorbate_properties['surface_density']
    n_mat = material_properties['surface_density']

    a_ads, a_mat = _dispersion_from_dict(
        adsorbate_properties, material_properties
    )  # dispersion constants

    d_eff = (d_ads + d_mat) / 2  # effective diameter
    N_over_RT = _N_over_RT(temperature)  # N_av / RT

    ###################################################################
    if pore_geometry == 'slit':

        sigma = 0.8583742 * d_eff  # (2/5)**(1/6)*d_eff, internuclear distance at 0 energy
        sigma_p4_o3 = sigma**4 / 3  # pre-calculated constant
        sigma_p10_o9 = sigma**10 / 9  # pre-calculated constant

        const_coeff = (
            N_over_RT * (n_ads * a_ads + n_mat * a_mat) / (sigma * 1e-9)**4
        )  # sigma must be in SI here

        const_term = (
            sigma_p10_o9 / (d_eff**9) - sigma_p4_o3 / (d_eff**3)
        )  # nm

        def potential(l_pore):
            return (
                const_coeff / (l_pore - 2 * d_eff) *
                ((sigma_p4_o3 / (l_pore - d_eff)**3) -
                 (sigma_p10_o9 / (l_pore - d_eff)**9) + const_term)
            )

        if use_cy:
            pore_widths = _solve_hk_cy(
                pressure, loading, potential, 2 * d_eff, 1
            )
        else:
            pore_widths = _solve_hk(pressure, potential, 2 * d_eff, 1)

        # width = distance between infinite slabs - 2 * surface molecule radius (=d_mat)
        pore_widths = numpy.asarray(pore_widths) - d_mat

    ###################################################################
    elif pore_geometry == 'cylinder':

        const_coeff = 0.75 * scipy.const.pi * N_over_RT * \
            (n_ads * a_ads + n_mat * a_mat) / (d_eff * 1e-9)**4  # d_eff must be in SI

        # to avoid unnecessary recalculations, we cache a_k and b_k values
        a_ks, b_ks = [1], [1]
        for k in range(1, 2000):
            a_ks.append(((-4.5 - k) / k)**2 * a_ks[k - 1])
            b_ks.append(((-1.5 - k) / k)**2 * b_ks[k - 1])

        def potential(l_pore):

            d_over_r = d_eff / l_pore  # dimensionless
            d_over_r_p4 = d_over_r**4  # d/L ^ 4
            d_over_r_p10_k = 0.65625 * d_over_r**10  # 21/32 * d/L ^ 4

            k_sum = d_over_r_p10_k - d_over_r_p4  # first value at K=0

            # 25 * pore radius ensures that layer convergence is achieved
            for k in range(1, int(l_pore * 25)):
                k_sum = k_sum + (
                    (1 / (k + 1) * (1 - d_over_r)**(2 * k)) *
                    (a_ks[k] * d_over_r_p10_k - b_ks[k] * d_over_r_p4)
                )

            return const_coeff * k_sum

        if use_cy:
            pore_widths = _solve_hk_cy(pressure, loading, potential, d_eff, 2)
        else:
            pore_widths = _solve_hk(pressure, potential, d_eff, 2)

        # width = 2 * cylinder radius - 2 * surface molecule radius (=d_mat)
        pore_widths = 2 * numpy.asarray(pore_widths) - d_mat

    ###################################################################
    elif pore_geometry == 'sphere':

        p_12 = 0.25 * a_mat / (d_eff * 1e-9)**6  # ads-surface potential depth
        p_22 = 0.25 * a_ads / (d_ads * 1e-9)**6  # ads-ads potential depth

        def potential(l_pore):

            l_minus_d = l_pore - d_eff
            d_over_l = d_eff / l_pore

            n_1 = 4 * scipy.const.pi * (l_pore * 1e-9)**2 * n_mat
            n_2 = 4 * scipy.const.pi * (l_minus_d * 1e-9)**2 * n_ads

            def t_term(x):
                return (1 + (-1)**x * l_minus_d / l_pore)**(-x) -\
                    (1 - (-1)**x * l_minus_d / l_pore)**(-x)

            return N_over_RT * (
                6 * (n_1 * p_12 + n_2 * p_22) * (l_pore / l_minus_d)**3
            ) * (
                -(d_over_l**6) * (t_term(3) / 12 + t_term(2) / 8) +
                (d_over_l**12) * (t_term(9) / 90 + t_term(8) / 80)
            )

        if use_cy:
            pore_widths = _solve_hk_cy(pressure, loading, potential, d_eff, 2)
        else:
            pore_widths = _solve_hk(pressure, potential, d_eff, 2)

        # width = 2 * sphere radius - 2 * surface molecule radius (=d_mat)
        pore_widths = 2 * numpy.asarray(pore_widths) - d_mat

    # finally calculate pore distribution
    liquid_density = adsorbate_properties['liquid_density']
    adsorbate_molar_mass = adsorbate_properties['adsorbate_molar_mass']

    # Cut unneeded values
    selected = slice(0, len(pore_widths))
    pore_widths = pore_widths[selected]
    pressure = pressure[selected]
    loading = loading[selected]

    avg_pore_widths = numpy.add(pore_widths[:-1], pore_widths[1:]) / 2  # nm
    volume_adsorbed = loading * adsorbate_molar_mass / liquid_density / 1000  # cm3/g
    pore_dist = numpy.diff(volume_adsorbed) / numpy.diff(pore_widths)

    return avg_pore_widths, pore_dist, volume_adsorbed[1:]


def psd_horvath_kawazoe_ry(
    pressure: t.List[float],
    loading: t.List[float],
    temperature: float,
    pore_geometry: str,
    adsorbate_properties: t.Mapping[str, float],
    material_properties: t.Mapping[str, float],
    use_cy: bool = False,
):
    r"""
    Calculate the microporous size distribution using a Rege-Yang (R-Y) type model.

    Parameters
    ----------
    pressure : array
        Relative pressure.
    loading : array
        Adsorbed amount in mmol/g.
    temperature : float
        Temperature of the experiment, in K.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    adsorbate_properties : dict
        Properties for the adsorbate in the form of::

            adsorbate_properties = dict(
                'molecular_diameter': 0,           # nm
                'polarizability': 0,               # nm3
                'magnetic_susceptibility': 0,      # nm3
                'surface_density': 0,              # molecules/m2
                'liquid_density': 0,               # g/cm3
                'adsorbate_molar_mass': 0,         # g/mol
            )

    material_properties : dict
        Properties for the adsorbate in the same form
        as 'adsorbate_properties'. A list of common models
        can be found in .characterisation.models_hk.
    use_cy : bool:
        Whether to use the Cheng-Yang nonlinear Langmuir term.

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
    This approach attempts to address two main shortcomings of the H-K method,
    (see details here
    :py:func:`~pygaps.characterisation.psd_microporous.psd_horvath_kawazoe_ry`)
    namely its odd summation of contributions from the adsorbate-surface and
    adsorbate-adsorbate contributions and the assumption of a continuous
    distributions of guest molecules inside a pore.

    Rege and Yang [#ry2]_ propose a more granular model, where molecules occupy
    fixed positions according to a minimum energy potential. Depending on the
    size of the pore in relation to the guest, pores are categorised based on
    the number of adsorbed layers :math:`M`, with molecules adsorbed inside
    described on a layer-by-layer basis. In a similar assumption to the BET
    theory, a molecule would experience a surface-guest potential only if
    adjacent to the pore wall, with subsequent layers interacting through pure
    guest-guest interactions. While they do not assign a weighted distribution
    to the guest position (i.e. according to Boltzmann's law) and thus disregard
    thermal motion, this model is theoretically a more accurate representation
    of how spherical molecules would pack in the pore. The potential equations
    were derived for slit, cylindrical and spherical pores.

    *Slit pore*

    For a slit geometry, the number of layers in a pore of width :math:`L` is
    calculated as a function of guest molecule and host surface atom diameter as
    :math:`M = (L - d_h)/d_g`. If the number of adsorbed layers is between 1 and
    2, the guest molecule will see only the two pore walls, and its potential
    will be:

    .. math::

        \epsilon_{hgh} = \frac{n_h A_{gh}}{2\sigma^{4}}
                            \Big[
                                  \Big(\frac{\sigma}{d_0}\Big)^{10}
                                - \Big(\frac{\sigma}{d_0}\Big)^{4}
                                - \Big(\frac{\sigma}{L - d_0}\Big)^{10}
                                + \Big(\frac{\sigma}{L - d_0}\Big)^{4}
                            \Big]

    If the number of layers is larger than two, there will be two types of guest
    molecular potentials, namely (i) the first layer which interacts on one side
    with the host surface and a layer of guests on the other and (ii) a
    middle-type layer which interacts with two other guest layers. Internuclear
    distance at zero energy for two guest molecules is introduced as
    :math:`\sigma_g = (2/5)^{1/6} d_g`. The functions describing the potentials
    of the two types of potential :math:`\epsilon_{hgg}` and
    :math:`\epsilon_{ggg}` are then:

    .. math::

        \epsilon_{hgg} = \frac{n_h A_{gh}}{2\sigma^{4}}
                            \Big[
                                  \Big(\frac{\sigma}{d_0}\Big)^{10}
                                - \Big(\frac{\sigma}{d_0}\Big)^{4}
                            \Big] +
                            \frac{n_g A_{gg}}{2\sigma_g^{4}}
                            \Big[
                                  \Big(\frac{\sigma_g}{d_g}\Big)^{10}
                                - \Big(\frac{\sigma_g}{d_g}\Big)^{4}
                            \Big]

    .. math::

        \epsilon_{ggg} = 2 \times \frac{n_g A_{gg}}{2\sigma_g^{4}}
                            \Big[
                                  \Big(\frac{\sigma_g}{d_g}\Big)^{10}
                                - \Big(\frac{\sigma_g}{d_g}\Big)^{4}
                            \Big]

    The average potential for a pore with more than two layers is a weighted
    combination of the two types of layers
    :math:`\bar{\epsilon} = [2 \epsilon_{hgg} + (M-2)\epsilon_{ggg}] / M`, while
    while for a single layer it is equal to
    :math:`\bar{\epsilon} = \epsilon_{hgh}`. With a potential formula for both
    types of pores, the change in free energy can be calculated similarly to the
    original H-K method: :math:`RT\ln(p/p_0) = N_A \bar{\epsilon}`.

    *Cylindrical pore*

    In a cylindrical pore, the number of concentric layers of guest molecules
    which can be arranged in a cross-section of radius :math:`L` is
    mathematically represented as:

    .. math::

        M = \text{int}\Big[ \frac{(2L - d_h)/d_g - 1}{2} \Big] + 1

    Here, :math:`int` truncates to an integer number rounded down. Molecules can
    then either be part of the first layer, interacting with the surface, or in
    subsequent layers, interacting with adsorbate layers, with their number for
    each layer estimated using its diameter. In this particular geometry, an
    assumption is made that *only outer-facing layers contribute to the
    interaction energy*. The potentials corresponding to the two situations are
    then determined as:

    .. math::

        \epsilon_{hg} =   \frac{3}{4}\pi \frac{n_h A_{gh}}{d_0^{4}}
                           \times
                             \Big[
                              \frac{21}{32} a_1^{10} \sum^{\infty}_{k = 0} \alpha_k b_1^{2k}
                              - a_1^{4} \sum^{\infty}_{k = 0} \beta_k b_1^{2k}
                             \Big] \\

    .. math::

        \epsilon_{gg} =   \frac{3}{4}\pi \frac{n_g A_{gg}}{d_g^{4}}
                           \times
                             \Big[
                              \frac{21}{32} a_i^{10} \sum^{\infty}_{k = 0} \alpha_k b_i^{2k}
                              - a_i^{4} \sum^{\infty}_{k = 0} \beta_k b_i^{2k}
                             \Big]

    Where:

    .. math::

            a_1 = d_0 / L \ \text{and} \ b_1 = (L - d_0) / L

    .. math::

            a_i = \frac{d_g}{L - d_0 - (i - 2) d_g} \ \text{and} \ b_i = \frac{L - d_0 - (i - 1) d_g}{L - d_0 - (i - 2) d_g}

    With the symbols having the same connotation as those in the original H-K
    cylindrical model. The number of molecules accommodated in each concentric
    layer is calculated as:

    .. math::

            n_i = \frac{\pi}{\sin^{-1} \Big[\frac{d_g}{2(L - d_0 - (i - 1) d_g)}\Big]}

    The average potential for a pore is then a weighted average defined as
    :math:`\bar{\epsilon} = \sum^{M}_{i = 1} n_i \epsilon_i / \sum^{M}_{i = 1} n_i`
    and then equated to change in free energy by multiplication with Avogadro's
    number.

    *Spherical pore*

    In a spherical pore of radius :math:`L`, the number of layers that can be
    accommodated :math:`M` is assumed identical to that in a cylindrical pore of
    similar radius. The equations describing the potential for the initial and
    subsequent layers are then given as:

    .. math::

        \epsilon_1 = 2 \frac{n_0 A_{gh}}{4 d_0^6}
                        \Big[
                          \frac{a_1^{12}}{10 b_1} \Big( \frac{1}{(1-b_1)^{10}} - \frac{1}{(1+b_1)^{10}} \Big)
                        - \frac{a_1^{6}}{4 b_1} \Big( \frac{1}{(1-b_1)^{4}} - \frac{1}{(1+b_1)^{4}} \Big)
                        \Big]

    .. math::

        \epsilon_i = 2 \frac{n_{i-1} A_{gg}}{4 d_g^6}
                        \Big[
                          \frac{a_i^{12}}{10 b_i} \Big( \frac{1}{(1-b_i)^{10}} - \frac{1}{(1+b_i)^{10}} \Big)
                        - \frac{a_i^{6}}{4 b_i} \Big( \frac{1}{(1-b_i)^{4}} - \frac{1}{(1+b_i)^{4}} \Big)
                        \Big]

    The number of molecules each layer interacts with (:math:`n`) is calculated
    based on known surface density and a spherical geometry correction. For the
    first layer :math:`n_0 = 4\pi L^2 n_h` and for subsequent layers
    :math:`n_i = 4\pi (L - d_0 - (i-1) d_g)^2 n_g`. The constants :math:`a` and
    :math:`b` are calculated as for a cylindrical geometry, as in the case with
    the average potential :math:`\bar{\epsilon}`.


    References
    ----------
    .. [#ry2] S. U. Rege and R. T. Yang, "Corrected Horváth-Kawazoe equations for
       pore-size distribution", AIChE Journal, vol. 46, no. 4, pp. 734–750, Apr.
       2000.

    """
    # Parameter checks
    missing = [x for x in HK_KEYS if x not in material_properties]
    if missing:
        raise ParameterError(
            f"Adsorbent properties dictionary is missing parameters: {missing}."
        )

    missing = [
        x for x in list(HK_KEYS.keys()) +
        ['liquid_density', 'adsorbate_molar_mass']
        if x not in adsorbate_properties
    ]
    if missing:
        raise ParameterError(
            f"Adsorbate properties dictionary is missing parameters: {missing}."
        )

    # ensure numpy arrays
    pressure = numpy.asarray(pressure)
    loading = numpy.asarray(loading)
    pore_widths = []

    # Constants unpacking and calculation
    d_ads = adsorbate_properties['molecular_diameter']
    d_mat = material_properties['molecular_diameter']
    n_ads = adsorbate_properties['surface_density']
    n_mat = material_properties['surface_density']

    a_ads, a_mat = _dispersion_from_dict(
        adsorbate_properties, material_properties
    )  # dispersion constants

    d_eff = (d_ads + d_mat) / 2  # effective diameter
    N_over_RT = _N_over_RT(temperature)  # N_av / RT

    ###################################################################
    if pore_geometry == 'slit':

        sigma = 0.8583742 * d_eff  # (2/5)**(1/6) * d_eff,
        sigma_ads = 0.8583742 * d_ads  # (2/5)**(1/6) * d_ads,
        s_over_d0 = sigma / d_eff  # pre-calculated constant
        sa_over_da = sigma_ads / d_ads  # pre-calculated constant

        # Potential with one sorbate layer.
        potential_adsorbate = (
            n_ads * a_ads / 2 / (sigma_ads * 1e-9)**4 *
            (-sa_over_da**4 + sa_over_da**10)
        )

        # Potential with one surface layer and one sorbate layer.
        potential_onesurface = (
            n_mat * a_mat / 2 / (sigma * 1e-9)**4 *
            (-s_over_d0**4 + s_over_d0**10)
        ) + potential_adsorbate

        def potential_twosurface(l_pore):
            """Potential with two surface layers."""
            return (
                n_mat * a_mat / 2 / (sigma * 1e-9)**4 * (
                    s_over_d0**10 - s_over_d0**4 + (sigma /
                                                    (l_pore - d_eff))**10 -
                    (sigma / (l_pore - d_eff))**4
                )
            )

        def potential_average(n_layer):
            return ((
                2 * potential_onesurface +
                (n_layer - 2) * 2 * potential_adsorbate  # NOTE 2 * is correct
            ) / n_layer)

        def potential(l_pore):
            n_layer = (l_pore - d_mat) / d_ads
            if n_layer < 2:
                return N_over_RT * potential_twosurface(l_pore)
            else:
                return N_over_RT * potential_average(n_layer)

        if use_cy:
            pore_widths = _solve_hk_cy(
                pressure, loading, potential, 2 * d_eff, 1
            )
        else:
            pore_widths = _solve_hk(pressure, potential, 2 * d_eff, 1)

        # width = distance between infinite slabs - 2 * surface molecule radius (=d_mat)
        pore_widths = numpy.asarray(pore_widths) - d_mat

    ###################################################################
    elif pore_geometry == 'cylinder':

        max_k = 25  # Maximum K summed
        cached_k = 2000  # Maximum K's cached
        # to avoid unnecessary recalculations, we cache a_k and b_k values
        a_ks, b_ks = [1], [1]
        for k in range(1, cached_k):
            a_ks.append(((-4.5 - k) / k)**2 * a_ks[k - 1])
            b_ks.append(((-1.5 - k) / k)**2 * b_ks[k - 1])

        def a_k_sum(r2, max_k_pore):
            k_sum_t = 1
            for k in range(1, max_k_pore):
                k_sum_t = k_sum_t + (a_ks[k] * r2**(2 * k))
            return k_sum_t

        def b_k_sum(r2, max_k_pore):
            k_sum_t = 1
            for k in range(1, max_k_pore):
                k_sum_t = k_sum_t + (b_ks[k] * r2**(2 * k))
            return k_sum_t

        def potential_general(l_pore, d_x, n_x, a_x, r1):
            # determine maximum summation as a function of pore length
            max_k_pore = int(l_pore * max_k)
            max_k_pore = max_k_pore if max_k_pore < 2000 else 2000
            # the b constant is 1-a
            r2 = 1 - r1
            # 0.65625 is (21 / 32), constant
            return (
                0.75 * scipy.const.pi * n_x * a_x / ((d_x * 1e-9)**4) * (
                    0.65625 * r1**10 * a_k_sum(r2, max_k_pore) -
                    r1**4 * b_k_sum(r2, max_k_pore)
                )
            )

        def potential(l_pore):
            n_layers = int(((2 * l_pore - d_mat) / d_ads - 1) / 2) + 1
            layer_populations = []
            layer_potentials = []

            for layer in range(1, n_layers + 1):
                width = 2 * (l_pore - d_eff - (layer - 1) * d_ads)
                if d_ads <= width:
                    layer_population = scipy.const.pi / math.asin(d_ads / width)
                else:
                    layer_population = 1

                if layer == 1:  # potential with surface (first layer)
                    r1 = d_eff / l_pore
                    layer_potential = potential_general(
                        l_pore, d_eff, n_mat, a_mat, r1
                    )
                else:  # inter-adsorbate potential (subsequent layers)
                    r1 = d_ads / (l_pore - d_eff - (layer - 2) * d_ads)
                    layer_potential = potential_general(
                        l_pore, d_ads, n_ads, a_ads, r1
                    )

                layer_populations.append(layer_population)
                layer_potentials.append(layer_potential)

            layer_populations = numpy.asarray(layer_populations)
            layer_potentials = numpy.asarray(layer_potentials)

            return (
                N_over_RT * numpy.sum(layer_populations * layer_potentials) /
                numpy.sum(layer_populations)
            )

        if use_cy:
            pore_widths = _solve_hk_cy(pressure, loading, potential, d_eff, 1)
        else:
            pore_widths = _solve_hk(pressure, potential, d_eff, 1)

        # width = 2 * cylinder radius - 2 * surface molecule radius (=d_mat)
        pore_widths = 2 * numpy.asarray(pore_widths) - d_mat

    ###################################################################
    elif pore_geometry == 'sphere':

        p_12 = a_mat / (4 * (d_eff * 1e-9)**6)  # ads-surface potential depth
        p_22 = a_ads / (4 * (d_ads * 1e-9)**6)  # ads-ads potential depth

        def potential_general(n_m, p_xx, r1):
            """General RY layer potential in a spherical regime."""
            r2 = 1 - r1  # the b constant is 1-a
            return (
                2 * n_m * p_xx *
                ((-r1**6 / (4 * r2) * ((1 - r2)**(-4) - (1 + r2)**(-4))) +
                 (r1**12 / (10 * r2) * ((1 - r2)**(-10) - (1 + r2)**(-10))))
            )

        def potential(l_pore):
            n_layers = int(((2 * l_pore - d_mat) / d_ads - 1) / 2) + 1
            layer_populations = []
            layer_potentials = []

            # potential with surface (first layer)
            layer_population = 4 * scipy.const.pi * (l_pore * 1e-9)**2 * n_mat
            r1 = d_eff / l_pore
            layer_potential = potential_general(layer_population, p_12, r1)
            layer_potentials.append(layer_potential)  # add E1

            # inter-adsorbate potential (subsequent layers)
            layer_populations = [(
                4 * scipy.const.pi * ((l_pore - d_eff -
                                 (layer - 1) * d_ads) * 1e-9)**2 * n_ads
            ) for layer in range(1, n_layers + 1)]  # [N1...Nm]

            for layer, layer_population in zip(
                range(2, n_layers + 1), layer_populations
            ):
                r1 = d_ads / (l_pore - d_eff - (layer - 2) * d_ads)
                layer_potential = potential_general(layer_population, p_22, r1)
                layer_potentials.append(layer_potential)  # add [E2...Em]

            layer_populations = numpy.asarray(layer_populations)
            layer_potentials = numpy.asarray(layer_potentials)

            return (
                N_over_RT * numpy.sum(layer_populations * layer_potentials) /
                numpy.sum(layer_populations)
            )

        if use_cy:
            pore_widths = _solve_hk_cy(pressure, loading, potential, d_eff, 1)
        else:
            pore_widths = _solve_hk(pressure, potential, d_eff, 1)

        # width = 2 * sphere radius - 2 * surface molecule radius (=d_mat)
        pore_widths = 2 * numpy.asarray(pore_widths) - d_mat

    # finally calculate pore distribution
    liquid_density = adsorbate_properties['liquid_density']
    adsorbate_molar_mass = adsorbate_properties['adsorbate_molar_mass']

    # Cut unneeded values
    selected = slice(0, len(pore_widths))
    pore_widths = pore_widths[selected]
    pressure = pressure[selected]
    loading = loading[selected]

    avg_pore_widths = numpy.add(pore_widths[:-1], pore_widths[1:]) / 2  # nm
    volume_adsorbed = loading * adsorbate_molar_mass / liquid_density / 1000  # cm3/g
    pore_dist = numpy.diff(volume_adsorbed) / numpy.diff(pore_widths)

    return avg_pore_widths, pore_dist, volume_adsorbed[1:]


def _solve_hk(pressure, hk_fun, bound, geo):
    """
    I personally found that simple Brent minimization
    gives good results. There may be other, more efficient
    algorithms, like conjugate gradient, but optimization is a moot point
    as long as average total runtime is short.
    The minimisation runs with bounds of [d_eff < x < 50].
    Maximum determinable pore size is limited at ~2.5 nm anyway.
    """

    p_w = []
    p_w_max = 10 / geo

    for p_point in pressure:

        def fun(l_pore):
            return (numpy.exp(hk_fun(l_pore)) - p_point)**2

        res = scipy.optimize.minimize_scalar(
            fun, method='bounded', bounds=(bound, 50)
        )
        p_w.append(res.x)

        # we will stop if reaching unrealistic pore sizes
        if res.x > p_w_max:
            break

    return p_w


def _solve_hk_cy(pressure, loading, hk_fun, bound, geo):
    """
    In this case, the SF correction factor is subtracted
    from the original function.
    """

    p_w = []
    p_w_max = 10 / geo
    coverage = loading / (max(loading) * 1.01)

    for p_point, c_point in zip(pressure, coverage):

        sf_corr = 1 + 1 / c_point * numpy.log(1 - c_point)

        def fun(l_pore):
            return (numpy.exp(hk_fun(l_pore) - sf_corr) - p_point)**2

        res = scipy.optimize.minimize_scalar(
            fun, method='bounded', bounds=(bound, 50)
        )
        p_w.append(res.x)

        # we will stop if reaching unrealistic pore sizes
        if res.x > p_w_max:
            break

    return p_w


def _dispersion_from_dict(ads_dict, mat_dict):

    p_ads = ads_dict['polarizability'] * 1e-27  # to m3
    p_mat = mat_dict['polarizability'] * 1e-27  # to m3
    m_ads = ads_dict['magnetic_susceptibility'] * 1e-27  # to m3
    m_mat = mat_dict['magnetic_susceptibility'] * 1e-27  # to m3

    return (
        _kirkwood_muller_dispersion_ads(p_ads, m_ads),
        _kirkwood_muller_dispersion_mat(p_mat, m_mat, p_ads, m_ads),
    )


def _kirkwood_muller_dispersion_ads(p_ads, m_ads):
    """Calculate the dispersion constant for the adsorbate.

    p and m stand for polarizability and magnetic susceptibility
    """
    return (
        1.5 * scipy.const.electron_mass * scipy.const.speed_of_light**2 * p_ads * m_ads
    )


def _kirkwood_muller_dispersion_mat(p_mat, m_mat, p_ads, m_ads):
    """Calculate the dispersion constant for the material.

    p and m stand for polarizability and magnetic susceptibility
    """
    return (
        6 * scipy.const.electron_mass * scipy.const.speed_of_light**2 * p_ads * p_mat /
        (p_ads / m_ads + p_mat / m_mat)
    )


def _N_over_RT(temp):
    """Calculate (N_a / RT)."""
    return (scipy.const.Avogadro / scipy.const.gas_constant / temp)
