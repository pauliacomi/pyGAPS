"""
This module contains the sample (or material) class.
"""

import pygaps

from ..utilities.exceptions import ParameterError


class Sample(object):
    '''
    This class acts as a unified descriptor for an adsorbent material.
    Its purpose is to store properties such as adsorbent name,
    and batch.


    Parameters
    ----------
    name : str
        The name of the sample.
    batch : str
        A batch number or secondary identifier for the material.

    Other Parameters
    ----------------
    contact : str
        Sample contact name.
    source : str
        Sample source laboratory.
    project : str
        Sample associated project.
    struct : str
        Sample structure.
    type : str
        Sample type (MOF/carbon/zeolite etc).
    form : str
        Sample form (powder/ pellet etc).
    comment : str
        Sample comments.
    density : float
        Sample density.
    molar_mass
        Sample molar mass.

    Notes
    -----

    The members of the properties are left at the discretion
    of the user. There are, however, some unique properties
    which can be set as seen above.

    '''
    _named_params = [
        'contact',
        'source',
        'project',
        'struct',
        'type',
        'form',
        'comment',
    ]

    def __init__(self, **sample_info):
        """
        Instantiation is done by passing all the parameters.
        """
        # TODO Should make the sample unique using
        # some sort of convention id

        # Required sample parameters checks
        if any(k not in sample_info
               for k in ('name', 'batch')):
            raise ParameterError(
                "Sample class MUST have the following information in the "
                "properties dictionary: 'name', 'batch'")

        #: Sample name
        self.name = sample_info.pop('name')
        #: Sample batch
        self.batch = sample_info.pop('batch')

        for parameter in self._named_params:
            if parameter in sample_info:
                setattr(self, parameter, sample_info.pop(parameter))

        #: Rest of sample properties
        self.properties = sample_info

        return

    @classmethod
    def from_list(cls, sample_name, sample_batch):
        """
        Gets the sample from the master list using its name

        Parameters
        ----------
        sample_name : str
            The name of the material to search.
        sample_batch : str
            The batch of the material to search.

        Returns
        -------
        Sample
            Instance of class.

        Raises
        ------
        ``ParameterError``
            if it does not exist or cannot be calculated.
        """
        # Checks to see if sample exists in master list
        sample = next(
            (sample for sample in pygaps.SAMPLE_LIST
                if sample_name == sample.name
                and
                sample_batch == sample.batch),
            None)

        if sample is None:
            raise ParameterError(
                "Sample {0} {1} does not exist in list of samples. "
                "First populate pygaps.SAMPLE_LIST "
                "with required sample class".format(
                    sample_name, sample_batch))

        return sample

    def __str__(self):
        '''
        Prints a short summary of all the sample parameters.
        '''
        string = ""

        if self.name:
            string += ("Sample:" + self.name + '\n')
        if self.batch:
            string += ("Batch:" + self.batch + '\n')

        for parameter in self._named_params:
            if hasattr(self, parameter):
                string += (parameter.title() + ":" +
                           getattr(self, parameter) + '\n')

        if self.properties:
            for prop in self.properties:
                string += (prop + ':' + str(self.properties.get(prop)) + '\n')

        return string

    def to_dict(self):
        """
        Returns a dictionary of the sample class
        Is the same dictionary that was used to create it.

        Returns
        -------
        dict
            Dictionary of all parameters.
        """

        parameters_dict = {
            'name': self.name,
            'batch': self.batch
        }

        for parameter in self._named_params:
            if hasattr(self, parameter):
                parameters_dict.update({parameter: getattr(self, parameter)})

        parameters_dict.update(self.properties)

        return parameters_dict

    def get_prop(self, prop):
        """
        Returns a property from the 'properties' dictionary.
        Or a named property if requested.

        Parameters
        ----------
        prop : str
            Property name desired.

        Returns
        -------
        str/float
            Value of property in the properties dict.

        Raises
        ------
        ``ParameterError``
            if it does not exist.
        """

        req_prop = self.properties.get(prop)
        if req_prop is None:
            try:
                req_prop = getattr(self, prop)
            except AttributeError:
                raise ParameterError("The {0} entry was not found in the "
                                     "sample properties "
                                     "for sample {1} {2}".format(
                                         prop, self.name, self.batch))

        return req_prop
