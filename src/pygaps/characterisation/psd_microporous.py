"""
Module contains 'classical' methods of calculating
a pore size distribution for pores in
the micropore range (<2 nm).
"""

import numpy
import scipy.constants as const
import scipy.optimize as opt

from ..core.adsorbate import Adsorbate
from ..graphing.calcgraph import psd_plot
from ..utilities.exceptions import ParameterError
from .models_hk import get_hk_model

_MICRO_PSD_MODELS = ['HK']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def psd_microporous(isotherm,
                    psd_model='HK',
                    pore_geometry='slit',
                    branch='ads',
                    adsorbent_model='Carbon(HK)',
                    adsorbate_model=None,
                    verbose=False):
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

    A common mantra of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    See Also
    --------
    pygaps.characterisation.psd_microporous.psd_horvath_kawazoe : low level HK (Horvath-Kawazoe) method

    """
    # Function parameter checks
    if psd_model is None:
        raise ParameterError("Specify a model to generate the pore size"
                             " distribution e.g. psd_model=\"HK\"")
    if psd_model not in _MICRO_PSD_MODELS:
        raise ParameterError("Model {} not an option for psd.".format(psd_model),
                             "Available models are {}".format(_MICRO_PSD_MODELS))
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError(
            "Geometry {} not an option for pore size distribution.".format(
                pore_geometry),
            "Available geometries are {}".format(_PORE_GEOMETRIES))
    if not isinstance(isotherm.adsorbate, Adsorbate):
        raise ParameterError("Isotherm adsorbate is not known, cannot calculate PSD.")

    # Get adsorbate properties
    if adsorbate_model is None:
        adsorbate_model = {
            'molecular_diameter': isotherm.adsorbate.get_prop('molecular_diameter'),
            'polarizability': isotherm.adsorbate.get_prop('polarizability'),
            'magnetic_susceptibility': isotherm.adsorbate.get_prop('magnetic_susceptibility'),
            'surface_density': isotherm.adsorbate.get_prop('surface_density'),
            'liquid_density': isotherm.adsorbate.liquid_density(isotherm.temperature),
            'adsorbate_molar_mass': isotherm.adsorbate.molar_mass(),
        }

    # Get adsorbent properties
    adsorbent_properties = get_hk_model(adsorbent_model)

    # Read data in
    loading = isotherm.loading(branch=branch,
                               loading_basis='molar',
                               loading_unit='mmol')
    pressure = isotherm.pressure(branch=branch,
                                 pressure_mode='relative')

    # Call specified pore size distribution function
    if psd_model == 'HK':
        pore_widths, pore_dist, pore_vol_cum = psd_horvath_kawazoe(
            loading, pressure, isotherm.temperature, pore_geometry,
            adsorbate_model, adsorbent_properties)

    if verbose:
        psd_plot(pore_widths, pore_dist,
                 pore_vol_cum=pore_vol_cum, log=False, right=2.5, method=psd_model)

    return {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
        'pore_volume_cumulative': pore_vol_cum,
    }


def psd_horvath_kawazoe(loading, pressure, temperature, pore_geometry,
                        adsorbate_properties,
                        adsorbent_properties=None):
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
    if pore_geometry == 'slit':
        pass
    elif pore_geometry == 'cylinder':
        raise NotImplementedError('Currently only slit pores supported.')
    elif pore_geometry == 'sphere':
        raise NotImplementedError('Currently only slit pores supported.')

    if adsorbent_properties is None:
        raise ParameterError(
            "A dictionary of adsorbent properties must be provided"
            " for the HK method. The properties required are:"
            "molecular_diameter, polarizability,"
            "magnetic_susceptibility and surface_density"
            "Some standard models can be found in "
            " .characterisation.models_hk")
    missing = [x for x in adsorbent_properties if x not in ['molecular_diameter',
                                                            'polarizability',
                                                            'magnetic_susceptibility',
                                                            'surface_density']]
    if len(missing) != 0:
        raise ParameterError(
            "Adsorbent properties dictionary is missing parameters: "
            "{}".format(' '.join(missing)))

    if adsorbate_properties is None:
        raise ParameterError(
            "A dictionary of adsorbate properties must be provided"
            " for the HK method. The properties required are:"
            " molecular_diameter, liquid_density, polarizability,"
            " magnetic_susceptibility, surface_density, adsorbate_molar_mass")
    missing = [x for x in ['molecular_diameter',
                           'liquid_density',
                           'polarizability',
                           'magnetic_susceptibility',
                           'surface_density',
                           'adsorbate_molar_mass'] if x not in adsorbate_properties]
    if len(missing) != 0:
        raise ParameterError(
            "Adsorbate properties dictionary is missing parameters: "
            "{}".format(' '.join(missing)))

    # dictionary unpacking
    d_gas = adsorbate_properties.get('molecular_diameter')
    d_mat = adsorbent_properties.get('molecular_diameter')
    p_gas = adsorbate_properties.get('polarizability') * 1e-27            # to m3
    p_mat = adsorbent_properties.get('polarizability') * 1e-27            # to m3
    m_gas = adsorbate_properties.get('magnetic_susceptibility') * 1e-27   # to m3
    m_mat = adsorbent_properties.get('magnetic_susceptibility') * 1e-27   # to m3
    n_gas = adsorbate_properties.get('surface_density')
    n_mat = adsorbent_properties.get('surface_density')
    liquid_density = adsorbate_properties.get('liquid_density')
    adsorbate_molar_mass = adsorbate_properties.get('adsorbate_molar_mass')

    # calculation of constants and terms
    e_m = const.electron_mass
    c_l = const.speed_of_light
    effective_diameter = d_gas + d_mat
    sigma = (2 / 5)**(1 / 6) * effective_diameter / 2
    sigma_si = sigma * 1e-9

    a_mat = 6 * e_m * c_l ** 2 * p_gas * p_mat / (p_gas / m_gas + p_mat / m_mat)
    a_gas = 3 * e_m * c_l**2 * p_gas * m_gas / 2

    constant_coefficient = const.Avogadro / (const.gas_constant * temperature) * \
        (n_gas * a_gas + n_mat * a_mat) / (sigma_si**4)

    constant_interaction_term = - ((sigma**4) / (3 * (effective_diameter / 2)**3) -
                                   (sigma**10) / (9 * (effective_diameter / 2)**9))

    def h_k_pressure(l_pore):
        pressure = numpy.exp(constant_coefficient / (l_pore - effective_diameter) *
                             ((sigma**4) / (3 * (l_pore - effective_diameter / 2)**3) -
                              (sigma**10) / (9 * (l_pore - effective_diameter / 2)**9) +
                              constant_interaction_term))

        return pressure

    p_w = []

    for p_point in pressure:
        # minimise to find pore length
        def h_k_minimization(l_pore):
            return numpy.abs(h_k_pressure(l_pore) - p_point)
        res = opt.minimize_scalar(h_k_minimization)
        p_w.append(res.x - d_mat)

    # finally calculate pore distribution
    pore_widths = numpy.array(p_w)
    avg_pore_widths = numpy.add(pore_widths[:-1], pore_widths[1:]) / 2          # nm
    volume_adsorbed = loading * adsorbate_molar_mass / liquid_density / 1000    # cm3/g
    pore_dist = numpy.diff(volume_adsorbed) / numpy.diff(pore_widths)

    return avg_pore_widths, pore_dist, volume_adsorbed[1:]
