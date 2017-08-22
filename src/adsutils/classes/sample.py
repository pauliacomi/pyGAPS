"""
This module contains the sample class for easy manipulation
"""

__author__ = 'Paul A. Iacomi'

import adsutils.data as data


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

    @classmethod
    def from_list(cls, sample_name, sample_batch):
        """
        Gets the sample from the master list using its name
        Raises an exception if it does not exist
        """
        # Checks to see if sample exists in master list
        sample = next(
            (sample for sample in data.SAMPLE_LIST
                if sample_name == sample.name
                and
                sample_batch == sample.batch),
            None)

        if sample is None:
            raise Exception("Sample {0}{1} does not exist in list of samples. "
                            "First populate adsutils.SAMPLE_LIST "
                            "with required sample class".format(
                                sample_name, sample_batch))

        return sample

    def get_prop(self, prop):
        """
        Returns a property of a sample class
        """

        req_prop = self.properties.get(prop)
        if req_prop is None:
            raise Exception("The {0} entry was not found in the "
                            "sample.properties dictionary "
                            "for sample {1} {2}".format(
                                prop, self.name, self.batch))

        return req_prop

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
