"""
Calculation of the pore size distribution based on an isotherm.
"""

from functools import partial

from ..classes.adsorbate import Adsorbate
from ..graphing.calcgraph import psd_plot
from ..utilities.exceptions import ParameterError
from .models_hk import get_hk_model
from .models_kelvin import kelvin_radius_std
from .models_kelvin import meniscus_geometry
from .models_thickness import get_thickness_model
from .psd_dft import psd_dft_kernel_fit
from .psd_mesoporous import psd_bjh
from .psd_mesoporous import psd_dollimore_heal
from .psd_microporous import psd_horvath_kawazoe

_MESO_PSD_MODELS = ['BJH', 'DH']
_MICRO_PSD_MODELS = ['HK']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def mesopore_size_distribution(isotherm, psd_model, pore_geometry='cylinder',
                               verbose=False, **model_parameters):
    """
    Calculates the pore size distribution using a 'classical' model, applicable to mesopores.

    To use, specify the psd model in the function argument, then pass the parameters
    for each model.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm which the pore size distribution will be calculated.
    psd_model : str
        The pore size distribution model to use.
    pore_geometry : str
        The geometry of the adsorbent pores.
    verbose : bool
        Prints out extra information on the calculation and graphs the results.
    model_parameters : dict
        A dictionary to override specific settings for each model.

    Other Parameters
    ----------------
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to desorption.
    kelvin_model : callable, optional
        A custom user kelvin model. It should be a callable that only takes
        relative pressure as an argument.
    thickness_model : str or callable, optional
        The thickness model to use for PSD, It defaults to Harkins and Jura.

    Returns
    -------
    result_dict : dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths(array)`` : the widths of the pores
            - ``pore_distribution(array)`` : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore as a combination of a statistical thickness and
    a condensation/evaporation behaviour described by surface tension

    Currently, the methods provided are:

        - the BJH or Barrett, Joyner and Halenda method
        - the DH or Dollimore-Heal method, an extension of the BJH method

    A common mantra of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    According to Rouquerol [#]_, in adopting this approach, it is assumed that:

        - The Kelvin equation is applicable over the pore range (mesopores). Therefore
          in pores which are below a certain size (around 2.5 nm), the granularity
          of the liquid-vapour interface becomes too large for classical bulk methods
          to be applied.
        - The meniscus curvature is controlled be the pore size and shape. Ideal shapes
          for the curvature are assumed.
        - The pores are rigid and of well defined shape. They are considered
          open-ended and non-intersecting
        - The filling/emptying of each pore does not depend on its location.
        - The adsorption on the pore walls is not different from surface adsorption.

    See Also
    --------
    pygaps.calculations.psd_mesoporous.psd_bjh : the BJH or Barrett, Joyner and Halenda method
    pygaps.calculations.psd_mesoporous.psd_dollimore_heal : the DH or Dollimore-Heal method

    """

    # Function parameter checks
    if psd_model is None:
        raise ParameterError("Specify a model to generate the pore size"
                             " distribution e.g. psd_model=\"BJH\"")
    if psd_model not in _MESO_PSD_MODELS:
        raise ParameterError("Model {} not an option for psd.".format(psd_model),
                             "Available models are {}".format(_MESO_PSD_MODELS))
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError("Geometry {} not an option for pore size"
                             "distribution.".format(pore_geometry),
                             "Available geometries are {}".format(_PORE_GEOMETRIES))

    branch = model_parameters.get('branch')
    if branch is None:
        branch = 'des'
    if branch not in ['ads', 'des']:
        raise ParameterError("Branch {} not an option for psd.".format(branch),
                             "Select either 'ads' or 'des'")

    # Default thickness model
    thickness_model = model_parameters.get('thickness_model')
    if thickness_model is None:
        thickness_model = 'Harkins/Jura'

    # Get required adsorbate properties
    adsorbate = Adsorbate.from_list(isotherm.adsorbate)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.t_exp)
    surface_tension = adsorbate.surface_tension(isotherm.t_exp)

    # Read data in, depending on branch requested
    # If on an adsorption branch, data will be reversed
    if branch == 'ads':
        loading = isotherm.loading(branch='ads',
                                   loading_basis='molar',
                                   loading_unit='mmol')[::-1]
        pressure = isotherm.pressure(branch='ads',
                                     pressure_mode='relative')[::-1]
    elif branch == 'des':
        loading = isotherm.loading(branch='des',
                                   loading_basis='molar',
                                   loading_unit='mmol')
        pressure = isotherm.pressure(branch='des',
                                     pressure_mode='relative')
    if loading is None:
        raise ParameterError("The isotherm does not have the required branch for"
                             " this calculation")

    # Thickness model definitions
    t_model = get_thickness_model(thickness_model)

    # Kelvin model definitions
    kelvin_model = model_parameters.get('kelvin_model')
    if kelvin_model:
        k_model = kelvin_model
    else:
        m_geometry = meniscus_geometry(branch, pore_geometry)
        k_model = partial(kelvin_radius_std,
                          meniscus_geometry=m_geometry,
                          temperature=isotherm.t_exp,
                          liquid_density=liquid_density,
                          adsorbate_molar_mass=molar_mass,
                          adsorbate_surface_tension=surface_tension)

    # Call specified pore size distribution function
    if psd_model == 'BJH':
        pore_widths, pore_dist = psd_bjh(
            loading, pressure, pore_geometry,
            t_model, k_model,
            liquid_density, molar_mass)
    elif psd_model == 'DH':
        pore_widths, pore_dist = psd_dollimore_heal(
            loading, pressure, pore_geometry,
            t_model, k_model,
            liquid_density, molar_mass)

    # Package the results
    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist, method=psd_model, left=1.5)

    return result_dict


def micropore_size_distribution(isotherm, psd_model, pore_geometry='slit',
                                verbose=False, **model_parameters):
    """
    Calculates the microporous size distribution using a 'classical' model.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm which the pore size distribution will be calculated.
    psd_model : str
        The pore size distribution model to use.
    pore_geometry : str
        The geometry of the adsorbent pores.
    verbose : bool
        Prints out extra information on the calculation and graphs the results.
    model_parameters : dict
        A dictionary to override specific settings for each model.

    Other Parameters
    ----------------
    adsorbate_model : obj('dict')
        The adsorbate model to use for PSD, If null, properties are taken
        from the adsorbate in the list.
    adsorbent_model : obj('str') or obj('dict')
        The adsorbent model to use for PSD, It defaults to Carbon(HK).

    Returns
    -------
    result_dict : dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths(array)`` : the widths of the pores
            - ``pore_distribution(array)`` : contribution of each pore width to the
              overall pore distribution

    Notes
    -----

    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore of specific width w at a relative pressure p/p0
    as a single function :math:`p/p0 = f(w)`. This function uses properties of the
    adsorbent and adsorbate as a way of determining the pore size distribution.

    Currently, the methods provided are:

        - the HK, or Horvath-Kawazoe method

    A common gotcha of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    See Also
    --------
    pygaps.calculations.psd_microporous.psd_horvath_kawazoe : the HK, of Horvath-Kawazoe method

    """

    # Function parameter checks
    if psd_model is None:
        raise ParameterError("Specify a model to generate the pore size"
                             " distribution e.g. psd_model=\"BJH\"")
    if psd_model not in _MICRO_PSD_MODELS:
        raise ParameterError("Model {} not an option for psd.".format(psd_model),
                             "Available models are {}".format(_MICRO_PSD_MODELS))
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError(
            "Geometry {} not an option for pore size distribution.".format(
                pore_geometry),
            "Available geometries are {}".format(_PORE_GEOMETRIES))

    adsorbent_model = model_parameters.get('adsorbent_model')
    if adsorbent_model is None:
        adsorbent_model = 'Carbon(HK)'

    # Get adsorbate properties
    adsorbate_properties = model_parameters.get('adsorbate_model')
    if adsorbate_properties is None:
        adsorbate = Adsorbate.from_list(isotherm.adsorbate)
        adsorbate_properties = dict(
            molecular_diameter=adsorbate.get_prop('molecular_diameter'),
            polarizability=adsorbate.get_prop('polarizability') / 1e31,
            magnetic_susceptibility=adsorbate.get_prop(
                'magnetic_susceptibility'),
            surface_density=adsorbate.get_prop('surface_density'),
        )

    # Read data in
    loading = isotherm.loading(branch='ads',
                               loading_basis='molar',
                               loading_unit='mmol')
    pressure = isotherm.pressure(branch='ads',
                                 pressure_mode='relative')
    maximum_adsorbed = model_parameters.get('max_adsorbed')
    if maximum_adsorbed is None:
        maximum_adsorbed = isotherm.loading_at(0.9)

    # Adsorbent model definitions
    adsorbent_properties = get_hk_model(adsorbent_model)

    # Call specified pore size distribution function
    if psd_model == 'HK':
        pore_widths, pore_dist = psd_horvath_kawazoe(
            loading, pressure, isotherm.t_exp, pore_geometry,
            maximum_adsorbed, adsorbate_properties, adsorbent_properties)

    # Package the results
    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist, log=False, right=2.5, method=psd_model)

    return result_dict


def dft_size_distribution(isotherm, kernel_path, verbose=False, **model_parameters):
    """
    Calculates the pore size distribution using a DFT kernel from a PointIsotherm.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm to calculate the pore size distribution.
    kernel_path : str
        The path to the kernel used.

    Returns
    -------
    result_dict : dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths(array)`` : the widths of the pores
            - ``pore_distribution(array)`` : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
    *Description*

    Density Functional Theory (DFT) along with its extensions (NLDFT, QSDFT, etc)
    have emerged as the most powerful methods of describing adsorption on surfaces
    and in pores [#]_, [#]_. The theory allows the prediction of molecular behaviour solely
    on the basis of quantum mechanical considerations, and does not require other
    properties besides the electron structure and positions of the atoms involved.
    Calculations of large systems of atoms, such as those involved in adsorption
    in pores is a computationally intensive task, with modern computing power
    significantly improving the scales on which the modelling can be applied.

    The theory can be used to model adsorption in a simplified pore of a particular
    width which yields the the adsorption isotherm on a material comprised solely
    on pores of that width. The calculation is then repeated on pores of different
    sizes, to obtain a 'DFT kernel' or a collection of ideal isotherms on a
    distribution of pores. The generation of this kernel should be judicious, as
    both the adsorbent and the adsorbate must be modelled accurately. As it is a
    field in of in itself, the DFT calculations themselves are outside the scope
    of this program.

    Using the kernel, the isotherm obtained through experimental means can be
    modelled. The contributions of each kernel isotherm to the overall data is
    determined through a minimisation function. The contributions and their
    corresponding pore size form the pore size distribution of the material.

    The program accepts kernel files in a CSV format with the following structure:

    .. csv-table::
       :header: Pressure(bar), Pore size 1(nm), Pore size 2(nm), ..., Pore size y(nm)

        p1,l11,l21,...,ly1
        p2,l12,l22,...,ly2
        p3,l13,l23,...,ly3
        ...,...,...,...,...
        px,l1x,l2x,...,lyz

    The kernel should have sufficient points for a good interpolation as well as
    have a range of pressures that is wide enough to cover possible experimental
    values.

    *Limitations*

    The accuracy of predicting pore size through DFT kernels is only as good as
    the kernel itself, which should be tailored to the adsorbate, adsorbent and
    experimental conditions used.

    The isotherm used to calculate the pore size distribution should have enough
    datapoints and pressure range in order to cover adsorption in the entire range
    of pores the material has.

    See Also
    --------
    pygaps.calculations.psd_dft.psd_dft_kernel_fit : fitting of isotherm data with a DFT kernel

    References
    ----------
    .. [#] A New Analysis Method for the Determination of the Pore Size Distribution of Porous
       Carbons from Nitrogen Adsorption Measurements; Seaton, Walton, and Quirke; Carbon,
       Vol. 27, No. 6, pp. 853-861, 1989
    .. [#] Pore Size Distribution Analysis of Microporous Carbons: A Density Functional
       Theory Approach; Lastoskie, Gubbins, and Quirke; J. Phys. Chem. 1993, 97, 4786-4796

    """
    # Check kernel
    if kernel_path is None:
        raise ParameterError(
            "A path to the kernel to be used must be specified."
            "Use 'internal' to use the internal kernel (USE JUDICIOUSLY).")

    # Read data in
    loading = isotherm.loading(branch='ads',
                               loading_basis='molar',
                               loading_unit='mmol')
    pressure = isotherm.pressure(branch='ads',
                                 pressure_mode='relative')

    # Call the DFT function
    pore_widths, pore_dist = psd_dft_kernel_fit(pressure, loading, kernel_path)

    # Package the results
    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist, method='DFT')

    return result_dict
