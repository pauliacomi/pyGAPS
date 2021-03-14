"""Tests relating to the ModelIsotherm class."""

import pandas
import pytest
from matplotlib.testing.decorators import cleanup
from pandas.testing import assert_series_equal

import pygaps
import pygaps.utilities.exceptions as pgEx

from ..characterisation.conftest import DATA
from ..characterisation.conftest import DATA_N77_PATH
from .conftest import LOADING_AT_PARAM
from .conftest import LOADING_PARAM
from .conftest import PRESSURE_AT_PARAM
from .conftest import PRESSURE_PARAM


class TestModelConvenience():
    """Test the convenience model function."""
    def test_model_isotherm(self, basic_pointisotherm):
        pygaps.model_iso(basic_pointisotherm, model="Henry")


@pytest.mark.core
class TestModelIsotherm():
    """Test the ModelIsotherm class."""
    def test_isotherm_create(self):
        """Check isotherm can be created from basic data."""
        isotherm_param = {
            'loading_key': 'loading',
            'pressure_key': 'pressure',
            'material': 'carbon',
            'adsorbate': 'nitrogen',
            'temperature': 77,
        }

        pressure = [1, 2, 3, 4, 5, 3, 2]
        loading = [1, 2, 3, 4, 5, 3, 2]

        isotherm_data = pandas.DataFrame({
            'pressure': pressure,
            'loading': loading
        })

        # regular creation
        pygaps.ModelIsotherm(
            pressure=pressure,
            loading=loading,
            model='Henry',
            **isotherm_param
        )

        # regular creation, DataFrame
        pygaps.ModelIsotherm(
            isotherm_data=isotherm_data, model='Henry', **isotherm_param
        )

        # regular creation, desorption
        pygaps.ModelIsotherm(
            isotherm_data=isotherm_data,
            model='Henry',
            branch='des',
            **isotherm_param
        )

        # regular creation, guessed parameters
        pygaps.ModelIsotherm(
            isotherm_data=isotherm_data,
            model='Henry',
            param_guess={'K': 1.0},
            **isotherm_param
        )

        # Missing pressure/loading
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(
                pressure=pressure, loading=None, **isotherm_param
            )

        # Missing model
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(isotherm_data=isotherm_data, **isotherm_param)

        # Wrong model
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data=isotherm_data, model='Wrong', **isotherm_param
            )

        # Wrong branch
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data=isotherm_data,
                model='Henry',
                branch='random',
            )

        # Wrong parameters
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data=isotherm_data,
                model='Henry',
                param_guess={'K9': 'woof'},
                **isotherm_param
            )

    def test_isotherm_create_from_model(self, basic_isotherm):
        """Check isotherm can be created from a model."""
        model = pygaps.modelling.get_isotherm_model('Henry')
        pygaps.ModelIsotherm(
            model=model,
            material='Test',
            temperature=303,
            adsorbate='nitrogen'
        )

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        """Check isotherm can be created from Isotherm."""
        pygaps.ModelIsotherm.from_isotherm(
            basic_isotherm,
            isotherm_data=pandas.DataFrame({
                'pressure': [1, 2, 3, 4, 5, 3, 2],
                'loading': [1, 2, 3, 4, 5, 3, 2]
            }),
            pressure_key='pressure',
            loading_key='loading',
            model='Henry',
        )

    def test_isotherm_create_from_pointisotherm(self, basic_pointisotherm):
        """Check isotherm can be created from PointIsotherm."""
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm.from_pointisotherm(basic_pointisotherm)
        pygaps.ModelIsotherm.from_pointisotherm(
            basic_pointisotherm,
            model='Henry',
        )

    @cleanup
    @pytest.mark.parametrize(
        'file, ', [(data['file']) for data in list(DATA.values())]
    )
    def test_isotherm_create_guess(self, file):
        """Check isotherm can be guessed from PointIsotherm."""

        filepath = DATA_N77_PATH / file
        isotherm = pygaps.isotherm_from_json(filepath)

        pygaps.ModelIsotherm.from_pointisotherm(
            isotherm, model='guess', verbose=True
        )

        pygaps.ModelIsotherm.from_pointisotherm(
            isotherm, model=['Henry', 'Langmuir'], verbose=True
        )

        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm.from_pointisotherm(
                isotherm, model=['Henry', 'DummyModel'], verbose=True
            )

    ##########################

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            pytest.param(1, {'branch': 'des'},
                         marks=pytest.mark.xfail),  # Wrong branch
        ] + PRESSURE_PARAM
    )
    def test_isotherm_ret_pressure(
        self,
        use_adsorbate,
        basic_modelisotherm,
        expected,
        parameters,
    ):
        """Check that all the functions in ModelIsotherm return their specified parameter."""
        assert basic_modelisotherm.pressure(
            6,
            **parameters,
        )[0] == pytest.approx(expected, 1e-5)

    def test_isotherm_ret_pressure_indexed(
        self,
        basic_modelisotherm,
    ):
        """Indexed option specified."""
        assert basic_modelisotherm.pressure(5, indexed=True).equals(
            pandas.Series([1.0, 2.25, 3.5, 4.75, 6.0], name='loading')
        )

    @pytest.mark.parametrize(
        'expected, parameters',
        [
            pytest.param(1, {'branch': 'des'},
                         marks=pytest.mark.xfail),  # Wrong branch
        ] + LOADING_PARAM
    )
    def test_isotherm_ret_loading(
        self,
        use_material,
        use_adsorbate,
        basic_modelisotherm,
        expected,
        parameters,
    ):
        """Check that all the functions in ModelIsotherm return their specified parameter."""
        assert basic_modelisotherm.loading(
            6,
            **parameters,
        )[0] == pytest.approx(expected, 1e-5)

    def test_isotherm_ret_loading_indexed(
        self,
        basic_modelisotherm,
    ):
        """Indexed option specified."""
        assert_series_equal(
            basic_modelisotherm.loading(5, indexed=True),
            pandas.Series([1.0, 2.25, 3.5, 4.75, 6.0])
        )

    ##########################

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        [
            pytest.param(1, 1, {'branch': 'des'},
                         marks=pytest.mark.xfail),  # Wrong branch
        ] + PRESSURE_AT_PARAM
    )
    def test_isotherm_ret_pressure_at(
        self,
        use_material,
        use_adsorbate,
        basic_modelisotherm,
        inp,
        parameters,
        expected,
    ):
        """Check the ModelIsotherm pressure_at(loading) function."""
        assert basic_modelisotherm.pressure_at(
            inp,
            **parameters,
        ) == pytest.approx(expected, 1e-5)

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        [
            pytest.param(1, 1, {'branch': 'des'},
                         marks=pytest.mark.xfail),  # Wrong branch
        ] + LOADING_AT_PARAM
    )
    def test_isotherm_ret_loading_at(
        self,
        use_material,
        use_adsorbate,
        basic_modelisotherm,
        inp,
        parameters,
        expected,
    ):
        """Check the ModelIsotherm loading_at(pressure) function."""
        assert basic_modelisotherm.loading_at(
            inp,
            **parameters,
        ) == pytest.approx(expected, 1e-5)

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        [
            (1, 1, dict()),
            pytest.param(1, 1, {'branch': 'des'},
                         marks=pytest.mark.xfail),  # Wrong branch
            (100000, 1, dict(pressure_unit='Pa')),
            (0.5, 3.89137, dict(pressure_mode='relative')),
        ]
    )
    def test_isotherm_spreading_pressure_at(
        self,
        use_adsorbate,
        basic_modelisotherm,
        inp,
        parameters,
        expected,
    ):
        """Check the ModelIsotherm spreading pressure calculation."""
        assert basic_modelisotherm.spreading_pressure_at(
            inp, **parameters
        ) == pytest.approx(expected, 1e-5)

    @cleanup
    def test_isotherm_print_parameters(self, basic_modelisotherm):
        """Checks isotherm can print its own info."""

        print(basic_modelisotherm)
        basic_modelisotherm.plot()
        basic_modelisotherm.print_info()
