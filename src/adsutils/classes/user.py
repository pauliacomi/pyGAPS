"""
This module contains the sample class for easy manipulation
"""

__author__ = 'Paul A. Iacomi'


class User:
    '''
    Class which contains the points from an adsorption isotherm and microcalorimetry
    '''

    def __init__(self, info):

        #: User name
        self.name = info['name']
        #: User nickname
        self.nick = info['nick']
        #: User email
        self.email = info['email']
        #: User lab
        self.lab = info['lab']

        return
