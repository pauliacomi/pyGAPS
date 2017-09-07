"""
This module calculates the isosteric heat for isotherms at different temperatures
"""


def isosteric_heat(isotherms):
    """
    Calculation of the isosteric heat of adsorption using several isotherms
    taken at different temperatures on the same material.

    Parameters
    ----------
    isotherms : iterable of Isotherms
        The isotherms to use in calculation of the isosteric heat. They should all
        be measured on the same material.

    Returns
    -------
    result_dict : dict
        A dictionary with the isosteric heats per loading, with the form:

            - ``isosteric_heat(array)`` : the isosteric heat of adsorption
            - ``loading(array)`` : the loading for each point of the isosteric heat

    Notes
    -----

    *Desription*

    The isosteric heats are calculated from experimental data using the Clausius-Clapeyron
    equation as the starting point:

    .. math::

        \\Big( \\frac{\\partial \\ln P}{\\partial T} \\Big)_{n_a} = -\\frac{\\Delta H_{ads}}{R T^2}

    Where :math:`\\Delta H_{ads}` is the enthalpy of adsorption. In order to approximate the
    partial differential, two or more isotherms are measured at different temperatures. The
    assumption made is that the heat of asdsorption does not vary in the temperature range
    chosen. Therefore, the isosteric heat of adsorption can be calculated by using the pressures
    at which the loading is identical using the following equation for each point:

    .. math::

        \\Delta H_{ads} = - R \\frac{\\partial \\ln P}{\\partial 1 / T}

    and plotting the values of :math:`\\ln P` against :math:`1 / T` we should obtain a straight
    line with a slope of :math:`- \\Delta H_{ads} / R.`

    *Limitations*

    The isosteric heat is sensitive to the differences in pressure between the two isotherms. If
    the isotherms measured are too close together, the error margin will increase.

    The method also assumes that enthalpy of adsorption does not vary with temperature. If the
    variation is large for the system in question, the isosteric heat calculation will give
    unrealistic values.

    """

    return
