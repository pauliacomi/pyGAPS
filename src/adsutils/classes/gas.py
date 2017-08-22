"""
This module contains the gas class for easy manipulation
"""

__author__ = 'Paul A. Iacomi'

from CoolProp.CoolProp import PropsSI

import adsutils.data as data


class Gas(object):
    '''
    Class which contains all info about a gas
    '''

    def __init__(self, info):
        #: Gas name
        self.name = info['nick']
        #: Gas formula
        self.formula = info['formula']
        #: Gas properties
        self.properties = info['properties']

        return

    @classmethod
    def from_list(cls, gas_name):
        """
        Gets the gas from the master list using its name
        Raises an exception if it does not exist
        """
        # See if gas exists in master list
        ads_gas = next(
            (x for x in data.GAS_LIST if gas_name == x.name), None)
        if ads_gas is None:
            raise Exception("Gas {0} does not exist in list of gasses. "
                            "First populate adsutils.data.GAS_LIST "
                            "with required gas class".format(gas_name))

        return ads_gas

    def to_dict(self):
        """
        Returns a dictionary of the gas class
        Is the same dictionary that was used to create it
        """

        parameters_dict = {
            'nick': self.name,
            'formula': self.formula,
            'properties': self.properties,
        }

        return parameters_dict

    def get_prop(self, prop):
        """
        Returns a property of a gas class
        Raises an exception if it does not exist
        """

        req_prop = self.properties.get(prop)
        if req_prop is None:
            raise Exception("Gas {0} does not have a property named "
                            "{1}.".format(self.name, prop))

        return req_prop

    def common_name(self):
        """
        Gets the common name of the gas from the properties dict
        Raises an exception if it does not exist
        """
        c_name = self.properties.get("common_name")
        if c_name is None:
            raise Exception("Gas {0} does not have a property named "
                            "common_name. This must be available for CoolProp "
                            "interaction".format(self.name))
        return c_name

    def molar_mass(self, calculate=True):
        """
        Uses the database to calculate molar mass

        @param: temp - temperature where the pressure is desired in K

        :return: pressure in g/mol
        """
        mol_m = self.properties.get("molar_mass")
        if mol_m is None or calculate:
            mol_m = PropsSI('M', self.common_name()) * 1000

        return mol_m

    def saturation_pressure(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        saturation pressure at a particular temperature

        @param: temp - temperature where the pressure is desired in K

        :return: pressure in Pascal
        """
        sat_p = self.properties.get("saturation_pressure")
        if sat_p is None or calculate:
            sat_p = PropsSI('P', 'T', temp, 'Q', 0, self.common_name())

        return sat_p

    def surface_tension(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        surface tension at a particular temperature

        @param: temp - temperature where the pressure is desired in K

        :return: surface tension in mN/m
        """
        surf_t = self.properties.get("surface_tension")
        if surf_t is None or calculate:
            surf_t = PropsSI('I', 'T', temp, 'Q', 0, self.common_name()) * 1000

        return surf_t

    def liquid_density(self, temp, calculate=True):
        """
        Uses an equation of state to determine the
        liquid density at a particular temperature

        @param: temp - temperature where the pressure is desired in K

        :return: density in g/cm3
        """
        liq_d = self.properties.get("liquid_density")
        if liq_d is None or calculate:
            liq_d = PropsSI('D', 'T', temp, 'Q', 0, self.common_name()) / 1000

        return liq_d

    def print_info(self):
        '''
        Prints a short summary of all the gas parameters
        '''

        print("Gas:", self.name)
        print("Formula:", self.formula)

        for prop in self.properties:
            print(prop, self.properties.get(prop))

        return
