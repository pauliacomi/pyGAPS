"""
This test module has tests relating to the adsorbate class
"""

import os

import pandas
import pytest
from matplotlib.testing.decorators import cleanup

import pygaps

from ..calculations.conftest import DATA
from ..calculations.conftest import DATA_PATH


class TestModelIsotherm(object):
    """
    Tests the pointisotherm class
    """

    def test_isotherm_create(self):
        "Checks isotherm can be created from basic data"
        isotherm_param = {
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
                loading_key='loading',
                pressure_key='pressure',
                param_guess=None,
                optimization_method="Nelder-Mead",
                **isotherm_param
            )

        # Wrong model
        with pytest.raises(pygaps.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data,
                loading_key='loading',
                pressure_key='pressure',
                model='Wrong',
                param_guess=None,
                optimization_method="Nelder-Mead",
                **isotherm_param
            )

        # Wrong parameters
        with pytest.raises(pygaps.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data,
                loading_key='loading',
                pressure_key='pressure',
                model='Henry',
                param_guess={'K9': 'woof'},
                optimization_method="Nelder-Mead",
                **isotherm_param
            )

        # regular creation
        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            model='Henry',
            param_guess=None,
            optimization_method="Nelder-Mead",
            **isotherm_param
        )

        # regular creation, desorption
        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            model='Henry',
            branch='des',
            param_guess=None,
            optimization_method="Nelder-Mead",
            **isotherm_param
        )

        # regular creation, guessed parameters
        isotherm = pygaps.ModelIsotherm(
            isotherm_data,
            loading_key='loading',
            pressure_key='pressure',
            model='Henry',
            param_guess={'KH': 1.0},
            optimization_method="Nelder-Mead",
            **isotherm_param
        )

        return isotherm

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        "Checks isotherm can be created from isotherm"

        isotherm_data = pandas.DataFrame({
            'pressure': [1, 2, 3, 4, 5, 3, 2],
            'loading': [1, 2, 3, 4, 5, 3, 2]
        })

        # regular creation
        isotherm = pygaps.ModelIsotherm.from_isotherm(
            basic_isotherm,
            isotherm_data,
            model='Henry',
            param_guess=None,
            optimization_method="Nelder-Mead",
        )

        return isotherm

    def test_isotherm_create_from_pointisotherm(self, basic_pointisotherm):
        "Checks isotherm can be created from isotherm"

        # regular creation
        isotherm = pygaps.ModelIsotherm.from_pointisotherm(
            basic_pointisotherm,
            model='Henry',
            param_guess=None,
            optimization_method="Nelder-Mead"
        )

        return isotherm

    @pytest.mark.parametrize('file, ',
                             [(data['file']) for data in list(DATA.values())])
    def test_isotherm_create_guess(self, file):
        "Checks isotherm can be created from a pointisotherm"

        filepath = os.path.join(DATA_PATH, file)

        with open(filepath, 'r') as text_file:
            isotherm = pygaps.PointIsotherm.from_json(
                text_file.read())

        isotherm = pygaps.ModelIsotherm.from_pointisotherm(
            isotherm, guess_model=True, verbose=True)

        return isotherm

    def test_isotherm_ret_pressure(self, basic_modelisotherm, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.pressure(branch='des')

        # Regular return
        assert set(basic_modelisotherm.pressure(5)) == set(
            [1.0, 2.25, 3.5, 4.75, 6.0])

        # Unit specified
        assert set(basic_modelisotherm.pressure(5, unit='Pa')) == set(
            [100000, 225000, 350000, 475000, 600000])

        # Mode specified
        assert basic_modelisotherm.pressure(5, mode='relative')[
            0] == pytest.approx(0.12849, 0.001)

        # Range specified
        assert set(basic_modelisotherm.pressure(5, min_range=2, max_range=5)) == set(
            [2.25, 3.5, 4.75])

        # Indexed option specified
        assert basic_modelisotherm.pressure(5, indexed=True).equals(pandas.Series(
            [1.0, 2.25, 3.5, 4.75, 6.0]
        ))

        return

    def test_isotherm_ret_loading(self, basic_modelisotherm, use_sample):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.loading(branch='des')

        # Standard return
        assert basic_modelisotherm.loading(5)[0] == pytest.approx(1.0, 1e-5)

        # Unit specified
        assert basic_modelisotherm.loading(
            5, unit='mol')[0] == pytest.approx(0.001, 1e-5)

        # Basis specified
        assert basic_modelisotherm.loading(5, basis='volume')[
            0] == pytest.approx(0.1, 1e-5)

        # Range specified
        assert basic_modelisotherm.loading(5, min_range=2, max_range=5)[
            0] == pytest.approx(2.25, 1e-5)

        # Indexed option specified
        assert isinstance(basic_modelisotherm.loading(
            5, indexed=True), pandas.Series)

        return

    def test_isotherm_ret_loading_at(self, basic_modelisotherm, use_sample, use_adsorbate):
        """Checks that all the functions in ModelIsotherm return their specified parameter"""

        # Wrong branch
        with pytest.raises(pygaps.ParameterError):
            basic_modelisotherm.loading_at(1, branch='des')

        # Standard return
        loading = basic_modelisotherm.loading_at(1)
        assert loading == pytest.approx(1.0, 1e-5)

        # Loading unit specified
        loading_lunit = basic_modelisotherm.loading_at(1, loading_unit='mol')
        assert loading_lunit == pytest.approx(0.001, 1e-5)

        # Pressure unit specified
        loading_punit = basic_modelisotherm.loading_at(
            100000, pressure_unit='Pa')
        assert loading_punit == pytest.approx(1.0, 1e-5)

        # Basis specified
        loading_bads = basic_modelisotherm.loading_at(
            1, adsorbent_basis='volume')
        assert loading_bads == pytest.approx(0.1, 1e-5)

        # Mode specified
        loading_mode = basic_modelisotherm.loading_at(
            0.5, pressure_mode='relative')
        assert loading_mode == pytest.approx(3.89137, 1e-5)

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
        assert spressure_mode == pytest.approx(3.89137, 1e-5)

        return

    @cleanup
    def test_isotherm_print_parameters(self, basic_modelisotherm):
        "Checks isotherm can print its own info"

        basic_modelisotherm.print_info(show=False)

        return
