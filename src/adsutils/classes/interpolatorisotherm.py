"""
This module contains objects to characterize the pure-component adsorption
isotherms from experimental or simulated data. These will be fed into the
IAST functions in pyiast.py.
"""
__author__ = 'Cory M. Simon'

import numpy
import pandas
from scipy.interpolate import interp1d

from .isotherm import Isotherm


class InterpolatorIsotherm(Isotherm):
    """
    Interpolator isotherm object to store pure-component adsorption isotherm.

    Here, the isotherm is characterized by linear interpolation of data.

    Loading = 0.0 at pressure = 0.0 is enforced here automatically for
    interpolation at low pressures.

    Default for extrapolating isotherm beyond highest pressure in available data
    is to throw an exception. Pass a value for `fill_value` in instantiation to
    extrapolate loading as `fill_value`.
    """

    def __init__(self, data,
                 loading_key=None,
                 pressure_key=None,
                 fill_value=None,
                 mode_adsorbent="mass",
                 mode_pressure="absolute",
                 unit_loading="mmol",
                 unit_pressure="bar",
                 **isotherm_parameters):
        """
        Instantiation. InterpolatorIsotherm is instantiated by passing it the
        pure-component adsorption isotherm data in the form of a Pandas
        DataFrame.

        Linear interpolation done with `interp1d` function in Scipy.

        e.g. to extrapolate loading beyond highest pressure point as 100.0,
        pass `fill_value=100.0`.

        :param data: DataFrame adsorption isotherm data
        :param loading_key: String key for loading column in data
        :param pressure_key: String key for pressure column in data
        :param fill_value: Float value of loading to assume when an attempt is
            made to interpolate at a pressure greater than the largest pressure
            observed in the data

        :return: self
        :rtype: InterpolatorIsotherm
        """
        # Checks
        # if pressure = 0 not in data frame, add it for interpolation between
        #   p = 0 and the lowest, nonzero pressure point.
        if 0.0 not in data[pressure_key].values:
            data = pandas.concat([pandas.DataFrame({pressure_key: 0.0, loading_key: 0.0},
                                                   index=[0]), data])

        # Run base class constructor
        Isotherm.__init__(self,
                          loading_key,
                          pressure_key,
                          mode_adsorbent,
                          mode_pressure,
                          unit_loading,
                          unit_pressure,
                          **isotherm_parameters)

        # store isotherm data in self
        #: Pandas DataFrame on which isotherm was fit
        self.data = data.sort_values(pressure_key, ascending=True)

        if fill_value is None:
            self.interp1d = interp1d(self.data[pressure_key],
                                     self.data[loading_key])
        else:
            self.interp1d = interp1d(self.data[pressure_key],
                                     self.data[loading_key],
                                     fill_value=fill_value, bounds_error=False)
        #: value of loading to assume beyond highest pressure in the data
        self.fill_value = fill_value

        return

    #: Construction from a parent class with the extra data needed
    @classmethod
    def from_isotherm(cls, isotherm, isotherm_data, fill_value=None):
        return cls(isotherm_data,
                   loading_key=isotherm.loading_key,
                   pressure_key=isotherm.pressure_key,
                   fill_value=fill_value,
                   mode_adsorbent=isotherm.mode_adsorbent,
                   mode_pressure=isotherm.mode_pressure,
                   unit_loading=isotherm.unit_loading,
                   unit_pressure=isotherm.unit_pressure,
                   **isotherm.get_parameters())

    def loading(self, pressure):
        """
        Linearly interpolate isotherm to compute loading at pressure P.

        :param pressure: float pressure (in corresponding units as data in
            instantiation)
        :return: predicted loading at pressure P (in corresponding units as data
            in instantiation)
        :rtype: Float or Array
        """
        return self.interp1d(pressure)

    def spreading_pressure(self, pressure):
        """
        Calculate reduced spreading pressure at a bulk gas pressure P.
        (see Tarafder eqn 4)

        Use numerical quadrature on isotherm data points to compute the reduced
        spreading pressure via the integral:

        .. math::

            \\Pi(p) = \\int_0^p \\frac{q(\\hat{p})}{ \\hat{p}} d\\hat{p}.

        In this integral, the isotherm :math:`q(\\hat{p})` is represented by a
        linear interpolation of the data.

        See C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution
        Theory (IAST) Python Package. Computer Physics Communications.

        :param pressure: float pressure (in corresponding units as data in
            instantiation)
        :return: spreading pressure, :math:`\\Pi`
        :rtype: Float
        """
        # throw exception if interpolating outside the range.
        if (self.fill_value is None) & \
                (pressure > self.data[self.pressure_key].max()):
            raise Exception("""To compute the spreading pressure at this bulk
            gas pressure, we would need to extrapolate the isotherm since this
            pressure is outside the range of the highest pressure in your
            pure-component isotherm data, %f.

            At present, your InterpolatorIsotherm object is set to throw an
            exception when this occurs, as we do not have data outside this
            pressure range to characterize the isotherm at higher pressures.

            Option 1: fit an analytical model to extrapolate the isotherm
            Option 2: pass a `fill_value` to the construction of the
                InterpolatorIsotherm object. Then, InterpolatorIsotherm will
                assume that the uptake beyond pressure %f is equal to
                `fill_value`. This is reasonable if your isotherm data exhibits
                a plateau at the highest pressures.
            Option 3: Go back to the lab or computer to collect isotherm data
                at higher pressures. (Extrapolation can be dangerous!)"""
                            % (self.data[self.pressure_key].max(),
                               self.data[self.pressure_key].max()))

        # Get all data points that are at nonzero pressures
        pressures = self.data[self.pressure_key].values[
            self.data[self.pressure_key].values != 0.0]
        loadings = self.data[self.loading_key].values[
            self.data[self.pressure_key].values != 0.0]

        # approximate loading up to first pressure point with Henry's law
        # loading = henry_const * P
        # henry_const is the initial slope in the adsorption isotherm
        henry_const = loadings[0] / pressures[0]

        # get how many of the points are less than pressure P
        n_points = numpy.sum(pressures < pressure)

        if n_points == 0:
            # if this pressure is between 0 and first pressure point...
            # \int_0^P henry_const P /P dP = henry_const * P ...
            return henry_const * pressure
        else:
            # P > first pressure point
            area = loadings[0]  # area of first segment \int_0^P_1 n(P)/P dP

            # get area between P_1 and P_k, where P_k < P < P_{k+1}
            for i in range(n_points - 1):
                # linear interpolation of isotherm data
                slope = (loadings[i + 1] - loadings[i]) / (pressures[i + 1] -
                                                           pressures[i])
                intercept = loadings[i] - slope * pressures[i]
                # add area of this segment
                area += slope * (pressures[i + 1] - pressures[i]) + intercept * \
                    numpy.log(pressures[i + 1] / pressures[i])

            # finally, area of last segment
            slope = (self.loading(pressure) - loadings[n_points - 1]) / (
                pressure - pressures[n_points - 1])
            intercept = loadings[n_points - 1] - \
                slope * pressures[n_points - 1]
            area += slope * (pressure - pressures[n_points - 1]) + intercept * \
                numpy.log(pressure / pressures[n_points - 1])

            return area
