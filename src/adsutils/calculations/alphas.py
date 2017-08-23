"""
This module calculates the alpha-s based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

import warnings

import matplotlib.pyplot as plt

from ..classes.gas import Gas
from .bet import area_BET
from .tplot import find_linear_sections
from .tplot import plot_tp
from .tplot import t_plot_parameters


def alpha_s(isotherm, reference_isotherm, reference_area=None, reducing_pressure=0.4, limits=None, verbose=False):
    """
    Calculates the external surface area and adsorbed volume using the alpha s method
    """

    # Function parameter checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        isotherm.convert_pressure_mode('relative')

    if reference_isotherm.mode_pressure != "relative":
        reference_isotherm.convert_pressure_mode('relative')

    # Check to see if reference isotherm is given
    if reference_isotherm is None:
        raise Exception("No reference isotherm for alpha s calculation "
                        "is provided. Please supply one ")
    if reference_isotherm.gas != isotherm.gas:
        raise Exception("The reference isotherm adsorbate is different than the "
                        "calculated isotherm adsorbate. ")
    if reducing_pressure < 0 or reducing_pressure > 1:
        raise Exception("The reducing pressure is outside the bounds of 0-1"
                        "First convert it using implicit functions")
    if reference_area is None:
        reference_area = area_BET(reference_isotherm).get('bet_area')

    # Get adsorbate properties
    ads_gas = Gas.from_list(isotherm.gas)
    molar_mass = ads_gas.molar_mass()
    liquid_density = ads_gas.liquid_density(isotherm.t_exp)

    # Read data in
    loading = isotherm.loading_ads(unit='mol')
    reference_loading = reference_isotherm.loading_ads(unit='mol')
    alpha_s_point = reference_isotherm.loading_at(0.4)
    alpha_curve = reference_loading / alpha_s_point

    # Call alpha s function
    results = alpha_s_raw(
        loading, alpha_curve, alpha_s_point, reference_area,
        liquid_density, molar_mass, limits=limits)

    result_dict = {
        'alpha_curve': alpha_curve,
        'results': results,
    }

    if verbose:
        if len(results) == 0:
            print('Could not find linear regions, attempt a manual limit')
        else:
            for index, result in enumerate(results):
                print("For linear region {0}".format(index))
                print("The slope is {0} and the intercept is {1}"
                      " With a correlation coefficient of {2}".format(
                          round(result.get('slope'), 4),
                          round(result.get('intercept'), 4),
                          round(result.get('corr_coef'), 4)
                      ))
                print(
                    "The alpha-s area is {0}".format(
                        round(result.get('alpha_s_area'), 4)))
                print("The adsorbed volume is {0} and the area is {1}".format(
                    round(result.get('adsorbed_volume'), 4),
                    round(result.get('area'), 4)
                ))
            fig = plt.figure()
            plot_tp(fig, alpha_curve, loading, results, alpha_s=True)

    return result_dict


def alpha_s_raw(loading, alpha_curve, alpha_s_point, reference_area, liquid_density, molar_mass, limits=None):
    """
    Calculates the alpha-s method
    """

    if len(loading) != len(alpha_curve):
        raise Exception("The length of the parameter arrays"
                        " do not match")

    # The alpha-s method is a generalisation of the t-plot method
    # As such, we can just call the t-plot method with the required parameters
    results = []

    if limits is not None:
        section = (alpha_curve > limits[0]) & (alpha_curve < limits[1])
        results.append(alpha_s_plot_parameters(alpha_curve,
                                               section, loading,
                                               alpha_s_point,
                                               reference_area,
                                               molar_mass, liquid_density))
    else:
        # Now we need to find the linear regions in the alpha-s for the
        # assesment of surface area.
        linear_sections = find_linear_sections(loading)

        # For each section we compute the linear fit
        for section in linear_sections:
            params = alpha_s_plot_parameters(alpha_curve,
                                             section, loading,
                                             alpha_s_point,
                                             reference_area,
                                             molar_mass, liquid_density)
            if params is not None:
                results.append(params)

        if len(results) == 0:
            warnings.warn(
                'Could not find linear regions, attempt a manual limit')

    return results


def alpha_s_plot_parameters(alpha_curve, section, loading,
                            alpha_s_point,
                            reference_area, molar_mass, liquid_density):
    """Gets the parameters for the linear region of the alpha-s plot"""

    result_dict = t_plot_parameters(alpha_curve,
                                    section, loading,
                                    molar_mass, liquid_density)

    alpha_s_area = reference_area / alpha_s_point * result_dict.get('slope')

    result_dict.update({'alpha_s_area': alpha_s_area})

    return result_dict
