"""
This module contains the adsorbent class
"""

__author__ = 'Paul A. Iacomi'

from CoolProp.CoolProp import PropsSI

import adsutils.data as data


class Adsorbate(object):
    '''
    This class acts as a unified descriptor for an adsorbate.

    Its purpose is to expose properties such as adsorbate name,
    and formula, as well as physical properties, such as molar mass
    vapour pressure, etc

    The properties can be either calculated through a wrapper over
    CoolProp or supplied in the initial sample dictionary

    To initially construct the class, use a dictionary::

        adsorbate_info = {
            'nick' : 'nitrogen',
            'formula' : 'N2',
            'properties' : {
                'x' : 'y'
                'z' : 't'
            }
        }

        my_adsorbate = Adsorbate(adsorbate_info)

    The members of the properties dictionary are left at the discretion
    of the user, to keep the class extensible. There are, however, some
    unique properties which are used by calculations in other modules:

        * common_name: used for integration with CoolProp. For a list of names
          look at the CoolProp list of fluids `here
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
        The info dictionary must contain an entry for 'nick'.

        :param info: dictionary of the form::

            adsorbate_info = {
                'nick' : 'nitrogen',
                'formula' : 'N2',
                properties : {
                    'x' : 'y'
                    'z' : 't'
                }
            }
        """
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

        :param adsorbate_name: the name of the adsorbate to search
        :returns: instance of class
        :raises: ``Exception`` if it does not exist
        """
        # See if adsorbate exists in master list
        adsorbate = next(
            (x for x in data.GAS_LIST if adsorbate_name == x.name), None)
        if adsorbate is None:
            raise Exception("Adsorbate {0} does not exist in list of gasses. "
                            "First populate adsutils.data.GAS_LIST "
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

        :returns: dictionary of all parameters
        :rtype: dict
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

        :param prop: Property name desired
        :returns: Value of property in the properties dict
        :raises: ``Exception`` if it does not exist
        """

        req_prop = self.properties.get(prop)
        if req_prop is None:
            raise Exception("Adsorbate {0} does not have a property named "
                            "{1}.".format(self.name, prop))

        return req_prop

    def common_name(self):
        """
        Gets the common name of the adsorbate from the properties dict

        :returns: Value of common_name in the properties dict
        :raises: ``Exception`` if it does not exist
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

        :param calculate: bool, whether to calculate the property
                          or look it up in the properties dictionary
                          default - True
        :returns: molar mass in g/mol
        :raises: ``Exception`` if it does not exist or cannot be calculated

        """
        mol_m = self.properties.get("molar_mass")
        if mol_m is None or calculate:
            mol_m = PropsSI('M', self.common_name()) * 1000

        return mol_m

    def saturation_pressure(self, temp, calculate=True):
        """
        Uses an equation of state to determine the`
        saturation pressure at a particular temperature

        :param temp: temperature at which the pressure is desired in K
        :param calculate: bool, whether to calculate the property
                    or look it up in the properties dictionary
                    default - True
        :return: pressure in Pascal
        :raises: ``Exception`` if it does not exist or cannot be calculated

        """
        sat_p = self.properties.get("saturation_pressure")
        if sat_p is None or calculate:
            sat_p = PropsSI('P', 'T', temp, 'Q', 0, self.common_name())

        return sat_p

    def surface_tension(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        surface tension at a particular temperature

        :param temp: temperature at which the surface_tension is desired in K
        :param calculate: bool, whether to calculate the property
                    or look it up in the properties dictionary
                    default - True
        :return: surface tension in mN/m
        :raises: ``Exception`` if it does not exist or cannot be calculated

        """
        surf_t = self.properties.get("surface_tension")
        if surf_t is None or calculate:
            surf_t = PropsSI('I', 'T', temp, 'Q', 0, self.common_name()) * 1000

        return surf_t

    def liquid_density(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        liquid density at a particular temperature

        :param temp: temperature at which the liquid density is desired in K
        :param calculate: bool, whether to calculate the property
                    or look it up in the properties dictionary
                    default - True
        :return: density in g/cm3
        :raises: ``Exception`` if it does not exist or cannot be calculated

        """
        liq_d = self.properties.get("liquid_density")
        if liq_d is None or calculate:
            liq_d = PropsSI('D', 'T', temp, 'Q', 0, self.common_name()) / 1000

        return liq_d
