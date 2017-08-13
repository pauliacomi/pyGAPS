"""
This module contains the gas class for easy manipulation
"""

__author__ = 'Paul A. Iacomi'
# %%
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

    def print_info(self):
        '''
        Prints a short summary of all the gas parameters
        '''

        print("Gas:", self.name)
        print("Formula:", self.formula)

        for prop in self.properties:
            print(prop, self.properties.get(prop))

        return


# %%
def saturation_pressure_at_temperature(temp, gas):
    """
    Uses an equation of state to determine the
    saturation pressure at a particular temperature

    Used mostly for absolute/relative pressure conversion

    @param: temp - temperature where the pressure is desired in K

    :return: pressure in Pascal
    """
    # See if gas exists in master list
    ads_gas = next(
        (x for x in data.GAS_LIST if gas == x.name), None)
    if ads_gas is None:
        raise Exception("Gas {0} does not exist in list of gasses. "
                        "First populate adsutils.data.GAS_LIST "
                        "with required gas class".format(gas))

    gas_name = ads_gas.properties.get("common_name")
    if gas_name is None:
        raise Exception("Gas {0} does not have a property named "
                        "common_name. This must be available for CoolProp "
                        "interaction".format(gas))

    return PropsSI('P', 'T', temp, 'Q', 0, gas_name)
