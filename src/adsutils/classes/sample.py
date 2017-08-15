"""
This module contains the sample class for easy manipulation
"""

__author__ = 'Paul A. Iacomi'


class Sample(object):
    '''
    Class which describes a material
    '''

    def __init__(self, sample_info):

        # TODO Should make the sample unique using
        # some sort of convention id

        # Required sample parameters cheks
        if any(k not in sample_info
                for k in ('name', 'batch')):
            raise Exception(
                "Sample class MUST have the following information in the properties dictionary: 'name', 'batch'")

        #: Sample name
        self.name = sample_info['name']
        #: Sample batch
        self.batch = sample_info['batch']

        #: Sample owner nickname
        self.owner = sample_info['owner']
        #: Sample contact nickname
        self.contact = sample_info['contact']
        #: Sample source laboratory
        self.source_lab = sample_info['source_lab']
        #: Sample project
        self.project = sample_info['project']
        #: Sample structure
        self.struct = sample_info['struct']
        #: Sample type (MOF/carbon/zeolite etc)
        self.type = sample_info['type']
        #: Sample form (powder/ pellet etc)
        self.form = sample_info['form']
        #: Sample comments
        self.comment = sample_info['comment']
        #: Sample properties
        self.properties = sample_info['properties']

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
        print("Type:", self.type)
        print("Form:", self.form)
        print("Comments:", self.comment)

        for prop in self.properties:
            print(prop, self.properties.get(prop))

        return
