"""
This test module has tests relating to the sample class
"""

import pytest

import pygaps


@pytest.mark.core
class TestSample(object):
    """
    Tests the sample class
    """

    def test_sample_created(self, sample_data, basic_sample):
        "Checks sample can be created from test data"

        assert sample_data == basic_sample.to_dict()

        with pytest.raises(pygaps.ParameterError):
            pygaps.Sample()

    def test_sample_retrieved_list(self, sample_data, basic_sample):
        "Checks sample can be retrieved from master list"
        pygaps.data.SAMPLE_LIST.append(basic_sample)
        uploaded_sample = pygaps.Sample.from_list(
            sample_data.get('name'),
            sample_data.get('batch'))

        assert sample_data == uploaded_sample.to_dict()

        with pytest.raises(pygaps.ParameterError):
            pygaps.Sample.from_list('noname', 'nobatch')

    def test_sample_get_properties(self, sample_data, basic_sample):
        "Checks if properties of a sample can be located"

        assert basic_sample.get_prop(
            'density') == sample_data.get('density')

        density = basic_sample.properties.pop('density')
        with pytest.raises(pygaps.ParameterError):
            basic_sample.get_prop('density')
        basic_sample.properties['density'] = density

    def test_sample_print(self, basic_sample):
        """Checks the printing is done"""

        print(basic_sample)
