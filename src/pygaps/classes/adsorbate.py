"""
This module contains the adsorbate class.
"""

import warnings

import CoolProp

import pygaps

from ..utilities.exceptions import ParameterError
from ..utilities.unit_converter import _PRESSURE_UNITS
from ..utilities.unit_converter import c_unit


class Adsorbate(object):
    """
    This class acts as a unified descriptor for an adsorbate.

    Its purpose is to expose properties such as adsorbate name,
    and formula, as well as physical properties, such as molar mass
    vapour pressure, etc.

    The properties can be either calculated through a wrapper over
    CoolProp or supplied in the initial sample creation.
    All parameters passed are saved in a self.parameters
    dictionary.

    Parameters
    ----------
    nick : str
        The name which should be used for this adsorbate.
    formula : str
        A chemical formula for the adsorbate.

    Other Parameters
    ----------------

    common_name : str
        Used for integration with CoolProp. For a list of names
        look at the CoolProp `list of fluids
        <http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids>`_
    molar_mass : float
        A user-provided value for the molar mass.
    saturation_pressure : float
        A user-provided value for the saturation pressure.
    surface_tension : float
        A user-provided value for the surface tension.
    liquid_density : float
        A user-provided value for the liquid density.
    gas_density : float
        A user-provided value for the gas density.
    enthalpy_liquefaction : float
        A user-provided value for the enthalpy of liquefaction.

    Notes
    -----

    The members of the properties dictionary are left at the discretion
    of the user, to keep the class extensible. There are, however, some
    unique properties which are used by calculations in other modules
    listed in the other parameters section above.

    These properties can be either calculated by CoolProp or taken from the parameters
    dictionary. They are best accessed using the associated function.

    Calculated::

        my_adsorbate.surface_tension(77)

    Value from dictionary::

        my_adsorbate.surface_tension(77, calculate=False)
    """

    _named_params = ['nick', 'formula']

    def __init__(self, **properties):
        """
        Instantiation is done by passing a dictionary with the parameters.
        """
        # Required sample parameters checks
        if any(k not in properties
                for k in ('nick', 'formula')):
            raise ParameterError(
                "Adsorbate class MUST have the following information in the properties dictionary: 'nick', 'formula'")

        #: Adsorbate name
        self.name = properties.pop('nick')
        #: Adsorbate formula
        self.formula = properties.pop('formula')
        #: Adsorbate properties
        self.properties = properties

        # CoolProp interaction variables, only generate when called
        self._backend = None
        self._state = None

        return

    @classmethod
    def from_list(cls, adsorbate_name):
        """
        Gets the adsorbate from the master list using its name.

        Parameters
        ----------
        adsorbate_name : str
            the name of the adsorbate to search

        Returns
        -------
        Adsorbate
            instance of class

        Raises
        ------
        ``ParameterError``
            If it does not exist in list.
        """
        # See if adsorbate exists in master list
        adsorbate = next(
            (x for x in pygaps.ADSORBATE_LIST if adsorbate_name == x.name), None)
        if adsorbate is None:
            raise ParameterError(
                "Adsorbate {0} does not exist in list of adsorbates. "
                "First populate pygaps.ADSORBATE_LIST "
                "with required adsorbate class".format(adsorbate_name))

        return adsorbate

    def __str__(self):
        """
        Prints a short summary of all the adsorbate parameters.
        """
        string = ""

        string += ("Adsorbate: " + self.name + '\n')
        string += ("Formula:" + self.formula + '\n')

        for prop in self.properties:
            string += (prop + ':' + str(self.properties.get(prop)) + '\n')

        return string

    def _get_state(self):
        """
        Returns the CoolProp state associated with the fluid.
        """
        if not self._backend or self._backend != pygaps.COOLPROP_BACKEND:
            self._backend = pygaps.COOLPROP_BACKEND
            self._state = CoolProp.AbstractState(
                pygaps.COOLPROP_BACKEND, self.common_name())

        return self._state

    def to_dict(self):
        """
        Returns a dictionary of the adsorbate class.
        Is the same dictionary that was used to create it.

        Returns
        -------
        dict
            dictionary of all parameters
        """

        parameters_dict = {
            'nick': self.name,
            'formula': self.formula,
        }
        parameters_dict.update(self.properties)

        return parameters_dict

    def get_prop(self, prop):
        """
        Returns a property from the 'properties' dictionary.

        Parameters
        ----------
        prop : str
            property name desired

        Returns
        -------
        str/float
            Value of property in the properties dict

        Raises
        ------
        ``ParameterError``
            If the the property does not exist
            in the class dictionary.
        """

        req_prop = self.properties.get(prop)
        if req_prop is None:
            raise ParameterError(
                "Adsorbate {0} does not have a property named "
                "{1}.".format(self.name, prop))

        return req_prop

    def common_name(self):
        """
        Gets the common name of the adsorbate from the properties dict.

        Returns
        -------
        str
            Value of common_name in the properties dict

        Raises
        ------
        ``ParameterError``
            If the the property does not exist
            in the class dictionary.
        """
        c_name = self.properties.get("common_name")
        if c_name is None:
            raise ParameterError(
                "Adsorbate {0} does not have a property named "
                "common_name. This must be available for CoolProp "
                "interaction".format(self.name))
        return c_name

    def molar_mass(self, calculate=True):
        """
        Returns the molar mass of the adsorbate

        Parameters
        ----------
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Molar mass in g/mol.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.
        """
        if calculate:
            try:
                mol_m = self._get_state().molar_mass() * 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                return self.molar_mass(calculate=False)

        else:
            mol_m = self.properties.get("molar_mass")
            if mol_m is None:
                raise ParameterError(
                    "Adsorbate {0} does not have a property named "
                    "molar_mass.".format(self.name))

        return mol_m

    def saturation_pressure(self, temp, unit=None, calculate=True):
        """
        Uses an equation of state to determine the
        saturation pressure at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the pressure is desired in K.
        unit : str
            Unit in which to return the saturation pressure.
            If not specifies defaults to Pascal.
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Pressure in unit requested.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self._get_state()
                state.update(CoolProp.QT_INPUTS, 0.0, temp)
                sat_p = state.p()

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                return self.saturation_pressure(temp, unit=unit,
                                                calculate=False)

            if unit is not None:
                sat_p = c_unit(_PRESSURE_UNITS, sat_p, 'Pa', unit)
        else:
            sat_p = self.properties.get("saturation_pressure")
            if sat_p is None:
                raise ParameterError(
                    "Adsorbate {0} does not have a property named "
                    "saturation_pressure.".format(self.name))

        return sat_p

    def surface_tension(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        surface tension at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the surface_tension is desired in K.
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Surface tension in mN/m.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self._get_state()
                state.update(CoolProp.QT_INPUTS, 0.0, temp)
                surf_t = state.surface_tension() * 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                return self.surface_tension(temp, calculate=False)

        else:
            surf_t = self.properties.get("surface_tension")
            if surf_t is None:
                raise ParameterError(
                    "Adsorbate {0} does not have a property named "
                    "surface_tension.".format(self.name))

        return surf_t

    def liquid_density(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        liquid density at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the liquid density is desired in K.
        calculate : bool, optional.
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Liquid density in g/cm3.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self._get_state()
                state.update(CoolProp.QT_INPUTS, 0.0, temp)
                liq_d = state.rhomass() / 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                return self.liquid_density(temp, calculate=False)

        else:
            liq_d = self.properties.get("liquid_density")
            if liq_d is None:
                raise ParameterError(
                    "Adsorbate {0} does not have a property named "
                    "liquid_density.".format(self.name))

        return liq_d

    def gas_density(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        gas density at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the gas density is desired in K.
        calculate : bool, optional.
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Liquid density in g/cm3.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self._get_state()
                state.update(CoolProp.QT_INPUTS, 1.0, temp)
                gas_d = state.rhomass() / 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                return self.gas_density(temp, calculate=False)

        else:
            gas_d = self.properties.get("gas_density")
            if gas_d is None:
                raise ParameterError(
                    "Adsorbate {0} does not have a property named "
                    "gas_density.".format(self.name))

        return gas_d

    def enthalpy_liquefaction(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        enthalpy of liquefaction at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the enthalpy of liquefaction is desired, in K.
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Enthalpy of liquefaction in kJ/mol.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self._get_state()

                state.update(CoolProp.QT_INPUTS, 0.0, temp)
                h_liq = state.hmolar()

                state.update(CoolProp.QT_INPUTS, 1.0, temp)
                h_vap = state.hmolar()

                enth_liq = (h_vap - h_liq) / 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                return self.enthalpy_liquefaction(temp, calculate=False)

        else:
            enth_liq = self.properties.get("enthalpy_liquefaction")
            if enth_liq is None:
                raise ParameterError(
                    "Adsorbate {0} does not have a property named "
                    "enthalpy_liquefaction.".format(self.name))

        return enth_liq
