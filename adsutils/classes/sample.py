"""
This module contains the sample class for easy manipulation
"""

__author__ = 'Paul A. Iacomi'


class sample:
    '''
    Class which contains the points from an adsorption isotherm and microcalorimetry
    '''

    def __init__(self, info):
        #: Sample MOF name
        self.name = info['name']
        #: Sample batch
        self.batch = info['batch']
        #: Sample owner nickname
        self.owner = info['owner']
        #: Sample contact nickname
        self.contact = info['contact']
        #: Sample source laboratory
        self.source_lab = info['source_lab']
        #: Sample project
        self.project = info['project']
        #: Sample structure
        self.struct = info['struct']
        #: Sample family
        self.family = info['family']
        #: Sample form
        self.form = info['form']
        #: Sample comments
        self.comment = info['comment']
        #: Sample properties
        self.properties = info['properties']

        return

    def print_info(self):
        '''
        Prints a short summary of all the sample parameters

        '''

        print("Sample:", self.name)
        print("Batch:", self.batch)
        print("Owner:", self.owner)
        print("Contact:", self.contact)
        print("Source Laboratory:", self.source_lab)
        print("Project:", self.project)
        print("Structure:", self.struct)
        print("Family:", self.family)
        print("Form:", self.form)
        print("Comments:", self.comment)

        return
