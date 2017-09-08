"""
This module contains the adsorbate class
"""

from CoolProp.CoolProp import PropsSI

from ..utilities.unit_converter import convert_pressure
import pygaps.data as data


class Adsorbate(object):
    '''
    This class acts as a unified descriptor for an adsorbate.

    Its purpose is to expose properties such as adsorbate name,
    and formula, as well as physical properties, such as molar mass
    vapour pressure, etc

    The properties can be either calculated through a wrapper over
    CoolProp or supplied in the initial sample dictionary

    Parameters
    ----------
    info : dict
        To initially construct the class, use a dictionary of the form::

        adsorbate_info = {
            'nick' : 'nitrogen',
            'formula' : 'N2',
            'properties' : {
                'x' : 'y'
                'z' : 't'
            }
        }

        The info dictionary must contain an entry for 'nick'.

    Notes
    -----

    The members of the properties dictionary are left at the discretion
    of the user, to keep the class extensible. There are, however, some
    unique properties which are used by calculations in other modules:

        * common_name: used for integration with CoolProp. For a list of names
          look at the CoolProp `list of fluids
          <http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids>`_
        * molar_mass
        * saturation_pressure
        * surface_tension
        * liquid_density

    These properties can be either calculated by CoolProp or taken from the parameters
    dictionary. They are best accessed using the associated function.

    Calculated::

        my_adsorbate.surface_tension(77)

    Value from dictionary::

        my_adsorbate.surface_tension(77, calculate=False)
    '''

    def __init__(self, info):
        """
        Instantiation is done by passing a dictionary with the parameters.
        """
        # Required sample parameters cheks
        if any(k not in info
                for k in ('nick', 'formula')):
            raise Exception(
                "Adsorbate class MUST have the following information in the properties dictionary: 'nick', 'formula'")

        #: Adsorbate name
        self.name = info.get('nick')
        #: Adsorbate formula
        self.formula = info.get('formula')
        #: Adsorbate properties
        self.properties = info.get('properties')

        return

    @classmethod
    def from_list(cls, adsorbate_name):
        """
        Gets the adsorbate from the master list using its name

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
        ``Exception``
            if it does not exist or cannot be calculated
        """
        # See if adsorbate exists in master list
        adsorbate = next(
            (x for x in data.GAS_LIST if adsorbate_name == x.name), None)
        if adsorbate is None:
            raise Exception("Adsorbate {0} does not exist in list of adsorbates. "
                            "First populate pygaps.data.GAS_LIST "
                            "with required adsorbate class".format(adsorbate_name))

        return adsorbate

    def __str__(self):
        '''
        Prints a short summary of all the adsorbate parameters
        '''
        string = ""

        string += ("Adsorbate: " + self.name + '\n')
        string += ("Formula:" + self.formula + '\n')

        for prop in self.properties:
            string += (prop + ':' + str(self.properties.get(prop)) + '\n')

        return string

    def to_dict(self):
        """
        Returns a dictionary of the adsorbate class
        Is the same dictionary that was used to create it

        Returns
        -------
        dict
            dictionary of all parameters
        """

        parameters_dict = {
            'nick': self.name,
            'formula': self.formula,
            'properties': self.properties,
        }

        return parameters_dict

    def get_prop(self, prop):
        """
        Returns a property from the 'properties' dictionary

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
        ``Exception``
            if it does not exist
        """

        req_prop = self.properties.get(prop)
        if req_prop is None:
            raise Exception("Adsorbate {0} does not have a property named "
                            "{1}.".format(self.name, prop))

        return req_prop

    def common_name(self):
        """
        Gets the common name of the adsorbate from the properties dict

        Returns
        -------
        str
            Value of common_name in the properties dict

        Raises
        ------
        ``Exception``
            if it does not exist
        """
        c_name = self.properties.get("common_name")
        if c_name is None:
            raise Exception("Adsorbate {0} does not have a property named "
                            "common_name. This must be available for CoolProp "
                            "interaction".format(self.name))
        return c_name

    def molar_mass(self, calculate=True):
        """
        Returns the molar mass of the adsorbate

        Parameters
        ----------
        calculate : bool, optional
            whether to calculate the property or look it up in the properties
            dictionary, default - True

        Returns
        -------
        float
            molar mass in g/mol

        Raises
        ------
        ``Exception``
            if it does not exist or cannot be calculated

        """
        mol_m = self.properties.get("molar_mass")
        if mol_m is None or calculate:
            mol_m = PropsSI('M', self.common_name()) * 1000

        return mol_m

    def saturation_pressure(self, temp, unit=None, calculate=True):
        """
        Uses an equation of state to determine the
        saturation pressure at a particular temperature

        Parameters
        ----------
        temp : float
            temperature at which the pressure is desired in K
        unit : str
            unit in which to return the saturation pressure
            if not specifies defaults to Pascal
        calculate : bool, optional
            whether to calculate the property or look it up in the properties
            dictionary, default - True

        Returns
        -------
        float
            pressure in unit requested

        Raises
        ------
        ``Exception``
            if it does not exist or cannot be calculated

        """
        sat_p = self.properties.get("saturation_pressure")
        if sat_p is None or calculate:
            sat_p = PropsSI('P', 'T', temp, 'Q', 0, self.common_name())

            if unit is not None:
                sat_p = convert_pressure(sat_p, 'Pa', unit)

        return sat_p

    def surface_tension(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        surface tension at a particular temperature

        Parameters
        ----------
        temp : float
            temperature at which the surface_tension is desired in K
        calculate : bool, optional
            whether to calculate the property or look it up in the properties
            dictionary, default - True

        Returns
        -------
        float
            surface tension in mN/m

        Raises
        ------
        ``Exception``
            if it does not exist or cannot be calculated

        """
        surf_t = self.properties.get("surface_tension")
        if surf_t is None or calculate:
            surf_t = PropsSI('I', 'T', temp, 'Q', 0, self.common_name()) * 1000

        return surf_t

    def liquid_density(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        liquid density at a particular temperature

        Parameters
        ----------
        temp : float
            temperature at which the liquid density is desired in K
        calculate : bool, optional
            whether to calculate the property or look it up in the properties
            dictionary, default - True

        Returns
        -------
        float
            density in g/cm3

        Raises
        ------
        ``Exception``
            if it does not exist or cannot be calculated

        """
        liq_d = self.properties.get("liquid_density")
        if liq_d is None or calculate:
            liq_d = PropsSI('D', 'T', temp, 'Q', 0, self.common_name()) / 1000

        return liq_d
