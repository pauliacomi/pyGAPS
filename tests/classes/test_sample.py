"""
This test module has tests relating to the sample class
"""

import pytest

import pygaps


class TestSample(object):
    """
    Tests the sample class
    """

    def test_sample_created(self, sample_data, basic_sample):
        "Checks sample can be created from test data"

        assert sample_data == basic_sample.to_dict()

        with pytest.raises(pygaps.ParameterError):
            pygaps.Sample({})

    def test_sample_retreived_list(self, sample_data, basic_sample):
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
            'density') == sample_data['properties'].get('density')

        density = basic_sample.properties.pop('density')
        with pytest.raises(pygaps.ParameterError):
            basic_sample.get_prop('density')
        basic_sample.properties['density'] = density

    def test_sample_basis_conversion(self, basic_sample):
        """Tests the conversion between relative and absolute pressure"""

        mass = 10
        volume = 1

        assert basic_sample.convert_basis(
            'volume', mass) == pytest.approx(volume, 0.1)

        assert basic_sample.convert_basis(
            'mass', volume) == pytest.approx(mass, 0.1)

        return

    def test_sample_print(self, basic_sample):
        """Checks the printing is done"""

        print(basic_sample)
