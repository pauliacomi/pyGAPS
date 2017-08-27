"""
Calculation of the pore size distribution based on an isotherm
"""

from functools import partial


from ..classes.gas import Gas
from ..graphing.psdgraph import psd_plot
from .kelvin_models import meniscus_geometry
from .kelvin_models import kelvin_radius_std
from .thickness_models import _THICKNESS_MODELS
from .thickness_models import thickness_halsey
from .thickness_models import thickness_harkins_jura
from .adsorbent_models import _ADSORBENT_MODELS
from .adsorbent_models import PROPERTIES_CARBON
from .adsorbent_models import PROPERTIES_OXIDE_ION
from .psd_mesoporous import psd_bjh
from .psd_mesoporous import psd_dollimore_heal
from .psd_microporous import psd_horvath_kawazoe
from .psd_dft import psd_dft_kernel_fit


_MESO_PSD_MODELS = ['BJH', 'DH', 'HK']
_MICRO_PSD_MODELS = ['HK']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def mesopore_size_distribution(isotherm, psd_model, pore_geometry='cylinder', verbose=False, **model_parameters):
    """
    Calculates the pore size distribution using a 'classical' model, applicable to mesopores

    :param isotherm: the isotherm of which the pore size distribution will be calculated
    :param psd_model: the pore size distribution model to use
    :param pore_geometry: the geometry of the adsorbent pores
    :param verbose: prints out extra information on the calculation and graphs the results
    :param **model_parameters: use this to override specific settings for each model

    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore as a combination of a statistical thickness and
    a condensation/evaporation behaviour described by surface tension

    Currently, the methods provided are:

        - the BJH or Barrett, Joyner and Halenda method
        - the DH or Dollimore-Heal method, an extension of the BJH method

    A common gotcha of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    """

    # Function parameter checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")

    if psd_model is None:
        raise Exception("Specify a model to generate the pore size"
                        " distribution e.g. psd_model=\"BJH\"")
    if psd_model not in _MESO_PSD_MODELS:
        raise Exception("Model {} not an option for psd.".format(psd_model),
                        "Available models are {}".format(_MESO_PSD_MODELS))
    if pore_geometry not in _PORE_GEOMETRIES:
        raise Exception("Geometry {} not an option for pore size distribution.".format(pore_geometry),
                        "Available geometries are {}".format(_PORE_GEOMETRIES))

    branch = model_parameters.get('branch')
    if branch is None:
        raise Exception("Specify the isotherm part to select for the calculation"
                        "'branch'= either 'adsorption' or 'desorption'")
    if branch not in ['adsorption', 'desorption']:
        raise Exception("Branch {} not an option for psd.".format(branch),
                        "Select either 'adsorption' or 'desorption'")

    if 'thickness_model' in model_parameters:
        thickness_model = model_parameters.get('thickness_model')
    else:
        thickness_model = 'Harkins/Jura'
    if thickness_model not in _THICKNESS_MODELS:
        raise Exception("Model {} not an option for pore size distribution.".format(thickness_model),
                        "Available models are {}".format(_THICKNESS_MODELS))

    # Get required adsorbate properties
    adsorbate = Gas.from_list(isotherm.gas)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.t_exp)
    surface_tension = adsorbate.surface_tension(isotherm.t_exp)

    # Read data in, depending on branch requested
    if branch == 'adsorption':
        loading = isotherm.loading_ads(unit='mmol')[::-1]
        pressure = isotherm.pressure_ads()[::-1]
    # If on desorption branch, data will be reversed
    elif branch == 'desorption':
        loading = isotherm.loading_des(unit='mmol')
        pressure = isotherm.pressure_des()
    if loading is None:
        raise Exception("The isotherm does not have the required branch for"
                        " this calculation")

    # Thickness model definitions
    if thickness_model == 'Halsey':
        t_model = thickness_halsey
    elif thickness_model == 'Harkins/Jura':
        t_model = thickness_harkins_jura

    # Kelvin model definitions
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

    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist)

    return result_dict


def micropore_size_distribution(isotherm, psd_model, pore_geometry='cylinder', verbose=False, **model_parameters):
    """
    Calculates the microporous size distribution using a 'classical' model

    :param isotherm: the isotherm of which the pore size distribution will be calculated
    :param psd_model: the pore size distribution model to use
    :param pore_geometry: the geometry of the adsorbent pores
    :param verbose: prints out extra information on the calculation and graphs the results
    :param **model_parameters: use this to override specific settings for each model

    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore of specific width w at a relative pressure p/p0
    as a single function :math:`p/p0 = f(w)`. This function uses properties of the
    adsorbent and adsorbate as a way of determining the pore size distribution.

    Currently, the methods provided are:

        - the HL, of Horvath-Kawazoe method

    A common gotcha of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    """

    # Function parameter checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")

    if psd_model is None:
        raise Exception("Specify a model to generate the pore size"
                        " distribution e.g. psd_model=\"BJH\"")
    if psd_model not in _MICRO_PSD_MODELS:
        raise Exception("Model {} not an option for psd.".format(psd_model),
                        "Available models are {}".format(_MICRO_PSD_MODELS))
    if pore_geometry not in _PORE_GEOMETRIES:
        raise Exception("Geometry {} not an option for pore size distribution.".format(pore_geometry),
                        "Available geometries are {}".format(_PORE_GEOMETRIES))

    if 'adsorbent_model' in model_parameters:
        adsorbent_model = model_parameters.get('adsorbent_model')
    else:
        adsorbent_model = 'Carbon(HK)'
    if adsorbent_model not in _ADSORBENT_MODELS:
        raise Exception("Model {} not an option for pore size distribution.".format(adsorbent_model),
                        "Available models are {}".format(_ADSORBENT_MODELS))

    # Get adsorbate properties
    ads_gas = Gas.from_list(isotherm.gas)
    adsorbate_properties = dict(
        molecular_diameter=ads_gas.get_prop('molecular_diameter'),
        polarizability=ads_gas.get_prop('polarizability'),
        magnetic_susceptibility=ads_gas.get_prop('magnetic_susceptibility'),
        surface_density=ads_gas.get_prop('surface_density'),
    )

    # Read data in
    loading = isotherm.loading_ads(unit='mmol')
    pressure = isotherm.pressure_ads()
    maximum_adsorbed = isotherm.loading_at(0.9)

    # Adsorbent model definitions
    if adsorbent_model == 'Carbon(HK)':
        adsorbent_properties = PROPERTIES_CARBON
    elif adsorbent_model == 'OxideIon(SF)':
        adsorbent_properties = PROPERTIES_OXIDE_ION

    # Call specified pore size distribution function
    if psd_model == 'HK':
        pore_widths, pore_dist = psd_horvath_kawazoe(
            loading, pressure, isotherm.t_exp, pore_geometry,
            maximum_adsorbed, adsorbate_properties, adsorbent_properties)

    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist, log=False, xmax=2)

    return result_dict


def dft_size_distribution(isotherm, kernel_path, verbose=False, **model_parameters):

    # Read data in
    loading = isotherm.loading_ads(unit='mmol')
    pressure = isotherm.pressure_ads()

    pore_widths, pore_dist = psd_dft_kernel_fit(pressure, loading, kernel_path)

    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist)

    return result_dict
