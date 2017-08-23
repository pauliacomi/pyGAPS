"""
This module calculates the t-plot based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

import warnings
from itertools import groupby

import matplotlib.pyplot as plt
import numpy
import scipy

from ..classes.gas import Gas
from .thickness_curves import _THICKNESS_MODELS
from .thickness_curves import thickness_halsey
from .thickness_curves import thickness_harkins_jura


def t_plot(isotherm, thickness_model, limits=None, verbose=False):
    """
    Calculates the external surface area and adsorbed volume using the t-plot method
    """

    # Function parameter checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")
    if thickness_model is None:
        raise Exception("Specify a model to generate the thickness curve"
                        " e.g. thickness_model=\"Halsey\"")
    if thickness_model not in _THICKNESS_MODELS:
        raise Exception("Model {} not an option for t-plot.".format(thickness_model),
                        "Available models are {}".format(_THICKNESS_MODELS))

    # Get adsorbate properties
    ads_gas = Gas.from_list(isotherm.gas)
    molar_mass = ads_gas.molar_mass()
    liquid_density = ads_gas.liquid_density(isotherm.t_exp)

    # Read data in
    loading = isotherm.loading_ads(unit='mol')
    pressure = isotherm.pressure_ads()

    # Thickness model definitions
    if thickness_model == "Halsey":
        t_model = thickness_halsey
    elif thickness_model == "Harkins/Jura":
        t_model = thickness_harkins_jura

    # Call t-plot function
    results, t_curve = t_plot_raw(
        loading, pressure, t_model, liquid_density, molar_mass, limits)

    result_dict = {
        't_curve': t_curve,
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
                print("The adsorbed volume is {0} and the area is {1}".format(
                    round(result.get('adsorbed_volume'), 4),
                    round(result.get('area'), 4)
                ))
            fig = plt.figure()
            plot_tp(fig, t_curve, loading, results)

    return result_dict


def t_plot_raw(loading, pressure, thickness_model, liquid_density, molar_mass, limits=None):
    """
    Calculates the external surface area and adsorbed volume using the t-plot method

    loading: in mol/g
    pressure: relative
    thickness_model: a callable which returns the thickenss of the adsorbed layer at a pressure p
    liquid_density: density of the adsorbate in the adsorbed state, in g/cm3
    gas_molar_mass: in g/mol
    """

    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # Generate the thickness curve for the pressure points
    thickness_curve = numpy.array(list(map(thickness_model, pressure)))

    results = []

    # If limits are not None, then the user requested specific limits
    if limits is not None:
        section = (thickness_curve > limits[0]) & (thickness_curve < limits[1])
        results.append(t_plot_parameters(thickness_curve,
                                         section, loading,
                                         molar_mass, liquid_density))

    # If not, attempt to find limits manually
    else:
        # Now we need to find the linear regions in the t-plot for the
        # assesment of surface area.
        linear_sections = find_linear_sections(loading)

        # For each section we compute the linear fit
        for section in linear_sections:
            params = t_plot_parameters(thickness_curve,
                                       section, loading,
                                       molar_mass, liquid_density)
            if params is not None:
                results.append(params)

        if len(results) == 0:
            warnings.warn(
                'Could not find linear regions, attempt a manual limit')

    return results, thickness_curve


def find_linear_sections(loading):

    linear_sections = []

    # To do this we calculate the second
    # derivative of the thickness plot
    second_deriv = numpy.gradient(numpy.gradient(loading))

    # We then find the points close to zero in the second derivative
    # These are the points where the graph is linear
    margin = 0.00001 / (len(loading) * max(loading))
    close_zero = numpy.abs(second_deriv) < margin

    # This snippet divides the the points in linear sections
    # where linearity holds at least for a number of measurements
    continuous_p = 3

    for k, g in groupby(enumerate(close_zero), lambda x: x[1]):
        group = list(g)
        if len(group) > continuous_p and k:
            linear_sections.append(list(map(lambda x: x[0], group)))

    return linear_sections


def t_plot_parameters(thickness_curve, section, loading, molar_mass, liquid_density):
    """Calculates the parameters from a linear section of the t-plot"""

    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        thickness_curve[section],
        loading[section])

    # Check if slope is good

    if slope * (max(thickness_curve) / max(loading)) < 3:
        adsorbed_volume = intercept * molar_mass / liquid_density
        area = slope * molar_mass / liquid_density * 1000

        result_dict = {
            'section': section,
            'slope': slope,
            'intercept': intercept,
            'corr_coef': corr_coef,
            'adsorbed_volume': adsorbed_volume,
            'area': area,
        }

        return result_dict
    return


def plot_tp(fig, thickness_curve, loading, results, alpha_s=False):
    """Draws the t-plot"""
    ax1 = fig.add_subplot(111)
    if alpha_s:
        label1 = 'alpha s'
        label2 = 'alpha s (V/V_0.4)'
    else:
        label1 = 't transform'
        label2 = 'layer thickness (nm)'
    ax1.plot(thickness_curve, loading,
             marker='', color='g', label=label1)

    for result in results:
        # plot chosen points
        ax1.plot(thickness_curve[result.get('section')], loading[result.get('section')],
                 marker='.', linestyle='')

        # plot line
        min_lim = 0
        max_lim = max(thickness_curve[result.get('section')]) * 1.2
        x_lim = [min_lim, max_lim]
        y_lim = [result.get('slope') * min_lim + result.get('intercept'),
                 result.get('slope') * max_lim + result.get('intercept')]

        ax1.plot(x_lim, y_lim, linestyle='--', color='black')

    ax1.set_title("t-plot")
    ax1.set_xlim(xmin=0)
    ax1.set_ylim(ymin=0)
    ax1.set_xlabel(label2)
    ax1.set_ylabel('amount adsorbed (mmol/g)')
    ax1.legend(loc='best')
    plt.show()
