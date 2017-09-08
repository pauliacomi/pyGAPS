"""
This module contains the experimental sample class
"""

import pygaps.data as data


class Sample(object):
    '''
    This class acts as a unified descriptor for an adsorbent material.
    Its purpose is to store properties such as adsorbent name,
    and batch.

    Parameters
    ----------
    info : dict
        To initially construct the class, use a dictionary of the form::

        adsorbent_info = {
            'name' : 'Zeolite-1',
            'batch' : '1234',

            'owner' : 'John Doe',
            'properties' : {
                'density' : 1.5
                'x' : 'y'
            }
        }

        The info dictionary must contain an entry for 'name' and 'batch'.

    Notes
    -----

    The members of the properties dictionary are left at the discretion
    of the user. There are, however, some unique properties which are used
    by calculations in other modules:

        * density

    '''

    def __init__(self, sample_info):
        """
        Instantiation is done by passing a dictionary with the parameters.
        """
        # TODO Should make the sample unique using
        # some sort of convention id

        # Required sample parameters cheks
        if any(k not in sample_info
                for k in ('name', 'batch')):
            raise Exception(
                "Sample class MUST have the following information in the properties dictionary: 'name', 'batch'")

        #: Sample name
        self.name = sample_info.get('name')
        #: Sample batch
        self.batch = sample_info.get('batch')

        #: Sample owner nickname
        self.owner = sample_info.get('owner')
        #: Sample contact nickname
        self.contact = sample_info.get('contact')
        #: Sample source laboratory
        self.source_lab = sample_info.get('source_lab')
        #: Sample project
        self.project = sample_info.get('project')
        #: Sample structure
        self.struct = sample_info.get('struct')
        #: Sample type (MOF/carbon/zeolite etc)
        self.type = sample_info.get('type')
        #: Sample form (powder/ pellet etc)
        self.form = sample_info.get('form')
        #: Sample comments
        self.comment = sample_info.get('comment')
        #: Sample properties
        self.properties = sample_info.get('properties')

        return

    @classmethod
    def from_list(cls, sample_name, sample_batch):
        """
        Gets the sample from the master list using its name

        Parameters
        ----------
        sample_name : str
            the name of the material to search
        sample_batch : str
            the batch of the material to search

        Returns
        -------
        Sample
            instance of class

        Raises
        ------
        ``Exception``
            if it does not exist or cannot be calculated
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
                            "First populate pygaps.SAMPLE_LIST "
                            "with required sample class".format(
                                sample_name, sample_batch))

        return sample

    def __str__(self):
        '''
        Prints a short summary of all the sample parameters
        '''
        string = ""

        string += ("Sample:" + self.name + '\n')
        string += ("Batch:" + self.batch + '\n')
        string += ("Owner:" + self.owner + '\n')
        string += ("Contact:" + self.contact + '\n')
        string += ("Source Laboratory:" + self.source_lab + '\n')
        string += ("Project:" + self.project + '\n')
        string += ("Structure:" + self.struct + '\n')
        string += ("Type:" + self.type + '\n')
        string += ("Form:" + self.form + '\n')
        string += ("Comments:" + self.comment + '\n')

        for prop in self.properties:
            string += (prop + ':' + str(self.properties.get(prop)) + '\n')

        return string

    def to_dict(self):
        """
        Returns a dictionary of the sample class
        Is the same dictionary that was used to create it

        Returns
        -------
        dict
            dictionary of all parameters
        """

        parameters_dict = {
            'name': self.name,
            'batch': self.batch,
            'owner': self.owner,
            'contact': self.contact,
            'source_lab': self.source_lab,
            'project': self.project,
            'struct': self.struct,
            'type': self.type,
            'form': self.form,
            'comment': self.comment,
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
            raise Exception("The {0} entry was not found in the "
                            "sample.properties dictionary "
                            "for sample {1} {2}".format(
                                prop, self.name, self.batch))

        return req_prop
