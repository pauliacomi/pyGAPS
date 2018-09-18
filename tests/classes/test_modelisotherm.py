"""
This test module has tests relating to the adsorbate class
"""

import os

import numpy
import pandas
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps

from ..calculations.conftest import DATA
from ..calculations.conftest import DATA_N77_PATH


@pytest.mark.core
class TestModelIsotherm(object):
    """
    Tests the pointisotherm class
    """

    def test_isotherm_create(self):
        "Checks isotherm can be created from basic data"
        isotherm_param = {
            'loading_key': 'loading',
            'pressure_key': 'pressure',
            'sample_name': 'carbon',
            'sample_batch': 'X1',
            'adsorbate': 'nitrogen',
            't_exp': 77,
        }

        isotherm_data = pandas.DataFrame({
            'pressure': [1, 2, 3, 4, 5, 3, 2],
            'loading': [1, 2, 3, 4, 5, 3, 2]
        })

        # Missing model
        with pytest.raises(pygaps.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data,
                **isotherm_param
            )

        # Wrong model
        with pytest.raises(pygaps.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data,
                model='Wrong',
                **isotherm_param
            )

        # Wrong parameters
        with pytest.raises(pygaps.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data,
                model='Henry',
                param_guess={'K9': 'woof'},
                **isotherm_param
            )

        # regular creation
        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            model='Henry',
            **isotherm_param
        )

        # regular creation, desorption
        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            model='Henry',
            branch='des',
            **isotherm_param
        )

        # regular creation, guessed parameters
        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            model='Henry',
            param_guess={'K': 1.0},
            **isotherm_param
        )

        return isotherm

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        "Checks isotherm can be created from isotherm"

        # regular creation
        isotherm = pygaps.ModelIsotherm.from_isotherm(
            basic_isotherm,
            pandas.DataFrame({
                'pressure': [1, 2, 3, 4, 5, 3, 2],
                'loading': [1, 2, 3, 4, 5, 3, 2]
            }),
            pressure_key='pressure',
            loading_key='loading',
            model='Henry',
        )

        return isotherm

    def test_isotherm_create_from_pointisotherm(self, basic_pointisotherm):
        "Checks isotherm can be created from isotherm"

        # regular creation
        isotherm = pygaps.ModelIsotherm.from_pointisotherm(
            basic_pointisotherm,
            model='Henry',
        )

        return isotherm

    @pytest.mark.parametrize('file, ',
                             [(data['file']) for data in list(DATA.values())])
    def test_isotherm_create_guess(self, file):
        "Checks isotherm can be created from a pointisotherm"

        filepath = os.path.join(DATA_N77_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.PointIsotherm.from_json(
                text_file.read())

        model_iso = pygaps.ModelIsotherm.from_pointisotherm(
            isotherm, guess_model=True, verbose=True)

        return model_iso

##########################
    def test_isotherm_ret_pressure(self, basic_modelisotherm, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.pressure(branch='des')

        # Regular return
        assert set(basic_modelisotherm.pressure(5)) == set(
            [1.0, 2.25, 3.5, 4.75, 6.0])

        # Unit specified
        assert set(basic_modelisotherm.pressure(5, pressure_unit='Pa')) == set(
            [100000, 225000, 350000, 475000, 600000])

        # Mode specified
        assert basic_modelisotherm.pressure(5, pressure_mode='relative')[
            0] == pytest.approx(0.12849, 0.001)

        # Range specified
        assert set(basic_modelisotherm.pressure(5, min_range=2, max_range=5)) == set(
            [2.25, 3.5, 4.75])

        # Indexed option specified
        assert basic_modelisotherm.pressure(5, indexed=True).equals(pandas.Series(
            [1.0, 2.25, 3.5, 4.75, 6.0]
        ))

        return

    def test_isotherm_ret_loading(self, basic_modelisotherm, use_sample, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.loading(branch='des')

        # Standard return
        assert basic_modelisotherm.loading(5)[0] == pytest.approx(1.0, 1e-5)

        # Loading unit specified
        assert basic_modelisotherm.loading(
            5, loading_unit='mol')[0] == pytest.approx(0.001, 1e-5)

        # Loading basis specified
        assert numpy.isclose(basic_modelisotherm.loading(
            5, loading_basis='mass', loading_unit='g')[0], 0.02801, 1e-4, 1e-4)

        # Adsorbent unit specified
        assert basic_modelisotherm.loading(5, adsorbent_unit='kg')[
            0] == pytest.approx(1000, 1e-5)

        # Adsorbent basis specified
        assert basic_modelisotherm.loading(5, adsorbent_basis='volume',
                                           adsorbent_unit='cm3')[0] == pytest.approx(10, 1e-5)

        # Range specified
        assert basic_modelisotherm.loading(5, min_range=2, max_range=5)[
            0] == pytest.approx(2.25, 1e-5)

        # Indexed option specified
        assert isinstance(basic_modelisotherm.loading(
            5, indexed=True), pandas.Series)

        return

##########################
    def test_isotherm_ret_loading_at(self, basic_modelisotherm, use_sample, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.loading_at(1, branch='des')

        # Standard return
        loading = basic_modelisotherm.loading_at(1)
        assert loading == pytest.approx(1.0, 1e-5)

        # Pressure unit specified
        loading_punit = basic_modelisotherm.loading_at(
            100000, pressure_unit='Pa')
        assert loading_punit == pytest.approx(1.0, 1e-5)

        # Pressure mode specified
        loading_mode = basic_modelisotherm.loading_at(
            0.5, pressure_mode='relative')
        assert loading_mode == pytest.approx(3.89137, 1e-4)

        # Loading unit specified
        loading_lunit = basic_modelisotherm.loading_at(1, loading_unit='mol')
        assert loading_lunit == pytest.approx(0.001, 1e-5)

        # Loading basis specified
        loading_lbasis = basic_modelisotherm.loading_at(
            1, loading_basis='mass', loading_unit='g')
        # Loading basis specified
        assert numpy.isclose(loading_lbasis, 0.02801, 1e-4, 1e-4)

        # Adsorbent unit specified
        loading_bunit = basic_modelisotherm.loading_at(
            1, adsorbent_unit='kg')
        assert loading_bunit == pytest.approx(1000, 0.1)

        # Adsorbent basis specified
        loading_bads = basic_modelisotherm.loading_at(
            1, adsorbent_basis='volume', adsorbent_unit='cm3')
        assert loading_bads == pytest.approx(10, 1e-3)

        return

    def test_isotherm_ret_pressure_at(self, basic_modelisotherm, use_sample, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.pressure_at(1, branch='des')

        # Standard return
        pressure = basic_modelisotherm.pressure_at(1)
        assert pressure == pytest.approx(1.0, 1e-5)

        # Pressure unit specified
        pressure_punit = basic_modelisotherm.pressure_at(
            1.0, pressure_unit='Pa')
        assert pressure_punit == pytest.approx(100000, 1)

        # Pressure mode specified
        pressure_mode = basic_modelisotherm.pressure_at(
            3.89137, pressure_mode='relative')
        assert pressure_mode == pytest.approx(0.5, 1e-5)

        # Loading unit specified
        pressure_lunit = basic_modelisotherm.pressure_at(
            0.001, loading_unit='mol')
        assert pressure_lunit == pytest.approx(1, 1e-5)

        # Loading basis specified
        pressure_lbasis = basic_modelisotherm.pressure_at(
            0.02808, loading_basis='mass', loading_unit='g')
        assert pressure_lbasis == pytest.approx(1, 1e-2)

        # Adsorbent unit specified
        pressure_bunit = basic_modelisotherm.pressure_at(
            1000, adsorbent_unit='kg')
        assert pressure_bunit == pytest.approx(1.0, 1e-5)

        # Adsorbent basis specified
        pressure_bads = basic_modelisotherm.pressure_at(
            10, adsorbent_basis='volume', adsorbent_unit='cm3')
        assert pressure_bads == pytest.approx(1.0, 1e-5)

        return

    def test_isotherm_spreading_pressure_at(self, basic_modelisotherm, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.spreading_pressure_at(1, branch='des')

        # Standard return
        spressure = basic_modelisotherm.spreading_pressure_at(1)
        assert spressure == pytest.approx(1.0, 1e-5)

        # Pressure unit specified
        spressure_punit = basic_modelisotherm.spreading_pressure_at(
            100000, pressure_unit='Pa')
        assert spressure_punit == pytest.approx(1.0, 1e-5)

        # Mode specified
        spressure_mode = basic_modelisotherm.spreading_pressure_at(
            0.5, pressure_mode='relative')
        assert spressure_mode == pytest.approx(3.89137, 1e-2)

        return

    @cleanup
    def test_isotherm_print_parameters(self, basic_modelisotherm):
        "Checks isotherm can print its own info"

        basic_modelisotherm.print_info(show=False)

        return
