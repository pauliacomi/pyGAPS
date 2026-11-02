"""Tests relating to the ModelIsotherm class."""

import numpy
import pandas
import pytest
from pandas.testing import assert_series_equal

import pygaps
import pygaps.modelling as pgm
import pygaps.parsing as pgp
import pygaps.utilities.exceptions as pgEx

from ..characterisation.conftest import DATA
from ..test_utils import mpl_cleanup
from .conftest import LOADING_AT_PARAM
from .conftest import LOADING_PARAM
from .conftest import PRESSURE_AT_PARAM
from .conftest import PRESSURE_PARAM


@pytest.fixture
def langmuir_pointisotherm():
    pressure = numpy.geomspace(0.001, 10, 64)
    loading = 5 * 3 * pressure / (1 + 3 * pressure)
    return pygaps.PointIsotherm(
        pressure=pressure,
        loading=loading,
        material='carbon',
        adsorbate='nitrogen',
        temperature=77,
        pressure_mode='absolute',
        pressure_unit='bar',
        loading_basis='molar',
        loading_unit='mmol',
        material_basis='mass',
        material_unit='g',
    )


@pytest.mark.core
class TestModelConvenience:
    """Test the convenience model function."""

    def test_model_isotherm(self, basic_pointisotherm):
        pgm.model_iso(basic_pointisotherm, model="Henry")


@pytest.mark.core
class TestModelIsotherm:
    """Test the ModelIsotherm class."""

    @pytest.mark.parametrize('index', [None, [10, 20, 30], ['same', 'same', 'other']])
    def test_descending_dataframe_branches(self, index, isotherm_parameters):
        data = pandas.DataFrame({'pressure': [3, 2, 1], 'loading': [6, 4, 2]}, index=index)
        original = data.copy(deep=True)
        arguments = dict(
            pressure_key='pressure',
            loading_key='loading',
            model='Henry',
            **isotherm_parameters,
        )
        with pytest.raises(pgEx.ParameterError, match='required isotherm branch does not contain any points'):
            pygaps.ModelIsotherm(isotherm_data=data, branch='ads', **arguments)
        isotherm = pygaps.ModelIsotherm(isotherm_data=data, branch='des', **arguments)
        assert isotherm.branch == 'des'
        numpy.testing.assert_allclose(isotherm.loading_at([1, 2, 3]), [2, 4, 6], rtol=1e-8)
        pandas.testing.assert_frame_equal(data, original)

        data['branch'] = 0
        explicit = pygaps.ModelIsotherm(isotherm_data=data, branch='ads', **arguments)
        assert explicit.branch == 'ads'
        numpy.testing.assert_allclose(explicit.loading_at([1, 2, 3]), [2, 4, 6], rtol=1e-8)

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

        isotherm_data = pandas.DataFrame({'pressure': pressure, 'loading': loading})

        # regular creation
        pygaps.ModelIsotherm(pressure=pressure, loading=loading, model='Henry', **isotherm_param)

        # regular creation, DataFrame
        pygaps.ModelIsotherm(isotherm_data=isotherm_data, model='Henry', **isotherm_param)

        # regular creation, desorption
        pygaps.ModelIsotherm(isotherm_data=isotherm_data, model='Henry', branch='des', **isotherm_param)

        # regular creation, guessed parameters
        pygaps.ModelIsotherm(isotherm_data=isotherm_data, model='Henry', param_guess={'K': 1.0}, **isotherm_param)

        # regular creation, with bounds
        pygaps.ModelIsotherm(
            isotherm_data=isotherm_data, model='Henry', param_guess={'K': 1.0}, param_bounds={'K': [0, 100]}, **isotherm_param
        )

        # Missing pressure/loading
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(pressure=pressure, loading=None, **isotherm_param)

        # Missing model
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(isotherm_data=isotherm_data, **isotherm_param)

        # Wrong model
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(isotherm_data=isotherm_data, model='Wrong', **isotherm_param)

        # Wrong branch
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(
                isotherm_data=isotherm_data,
                model='Henry',
                branch='random',
            )

        # Wrong parameters
        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm(isotherm_data=isotherm_data, model='Henry', param_guess={'K9': 'woof'}, **isotherm_param)

    def test_isotherm_create_from_model(self, basic_isotherm):
        """Check isotherm can be created from a model."""
        model = pygaps.modelling.get_isotherm_model('Henry')
        pygaps.ModelIsotherm(model=model, material='Test', temperature=303, adsorbate='nitrogen')

    def test_isotherm_create_from_isotherm(self, basic_isotherm):
        """Check isotherm can be created from Isotherm."""
        pygaps.ModelIsotherm.from_isotherm(
            basic_isotherm,
            isotherm_data=pandas.DataFrame({'pressure': [1, 2, 3, 4, 5, 3, 2], 'loading': [1, 2, 3, 4, 5, 3, 2]}),
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

    @pytest.mark.parametrize(
        'model',
        [
            pytest.param('Langmuir', id='single-model'),
            pytest.param(['Henry', 'Langmuir'], id='select-best'),
        ],
    )
    def test_isotherm_fit_known_langmuir(self, langmuir_pointisotherm, model):
        source = langmuir_pointisotherm
        before_data = source.data_raw.copy(deep=True)
        before_units = source.units.copy()
        options = {'param_guess': {'K': 2.4, 'n_m': 6}} if isinstance(model, str) else {}
        fitted = pygaps.ModelIsotherm.from_pointisotherm(source, model=model, optimization_params={'max_nfev': 2000}, **options)
        pressure = source.pressure()
        held_pressure = numpy.sqrt(pressure[:-1] * pressure[1:])
        expected_loading = 5 * 3 * held_pressure / (1 + 3 * held_pressure)

        assert fitted.model.name == 'Langmuir'
        assert numpy.isfinite(fitted.model.rmse) and fitted.model.rmse < 1e-4
        numpy.testing.assert_allclose(fitted.loading_at(held_pressure), expected_loading, rtol=1e-4, atol=1e-10)
        numpy.testing.assert_allclose([fitted.model.params['K'], fitted.model.params['n_m']], [3, 5], rtol=1e-4)
        assert fitted.material == source.material
        assert fitted.adsorbate == source.adsorbate
        assert fitted.temperature == source.temperature
        assert fitted.units == before_units
        assert fitted.branch == 'ads'
        pandas.testing.assert_frame_equal(source.data_raw, before_data)
        assert source.units == before_units

    def test_isotherm_guess_all_candidates_fail(self, langmuir_pointisotherm):
        with pytest.raises(pgEx.CalculationError, match='No model could be reliably fit'):
            pygaps.ModelIsotherm.from_pointisotherm(
                langmuir_pointisotherm, model=['Henry', 'Langmuir'], optimization_params={'max_nfev': 1}
            )

    @pytest.mark.parametrize('entrypoint', ['constructor', 'point', 'guess', 'wrapper'])
    def test_isotherm_fit_enforces_bounds(self, isotherm_parameters, entrypoint):
        point = pygaps.PointIsotherm(
            pressure=[1, 2, 3], loading=[2, 4, 6], branch='ads', **isotherm_parameters
        )
        options = {'param_bounds': {'K': [0.1, 0.2]}}
        if entrypoint == 'constructor':
            fitted = pygaps.ModelIsotherm(pressure=[1, 2, 3], loading=[2, 4, 6], model='Henry', **options, **isotherm_parameters)
        elif entrypoint == 'point':
            fitted = pygaps.ModelIsotherm.from_pointisotherm(point, model=['Henry'], **options)
        elif entrypoint == 'guess':
            fitted = pygaps.ModelIsotherm.guess(pressure=[1, 2, 3], loading=[2, 4, 6], models=['Henry'], **options, **isotherm_parameters)
        else:
            fitted = pgm.model_iso(point, model=['Henry'], **options)

        assert fitted.model.params['K'] == pytest.approx(0.2)
        assert fitted.model.param_bounds['K'] == [0.1, 0.2]

    @pytest.mark.parametrize('model', ['Langmuir', ['Henry', 'Langmuir']])
    def test_isotherm_fit_partial_bounds(self, langmuir_pointisotherm, model):
        fitted = pgm.model_iso(langmuir_pointisotherm, model=model, param_bounds={'K': [0.1, 1]})

        assert fitted.model.name == 'Langmuir'
        assert fitted.model.params['K'] == pytest.approx(1)
        assert fitted.model.param_bounds['n_m'] == (0, numpy.inf)

    @pytest.mark.parametrize('models', ['Langmuir', ['Henry', 'Langmuir'], 'guess'])
    @pytest.mark.parametrize('entrypoint', ['point', 'guess', 'wrapper'])
    def test_isotherm_selection_parameter_guesses(self, monkeypatch, langmuir_pointisotherm, entrypoint, models):
        guesses = {}
        original_fit = pgm.IsothermBaseModel.fit
        monkeypatch.setattr('pygaps.core.modelisotherm._GUESS_MODELS', ['Henry', 'Langmuir'])

        def capture_fit(model, pressure, loading, param_guess, *args, **kwargs):
            guesses[model.name] = param_guess.copy()
            return original_fit(model, pressure, loading, param_guess, *args, **kwargs)

        monkeypatch.setattr(pgm.IsothermBaseModel, 'fit', capture_fit)
        options = {'param_guess': {'n_m': 6}, 'param_bounds': {'K': [0.1, 10]}}
        point = langmuir_pointisotherm
        if entrypoint == 'point':
            fitted = pygaps.ModelIsotherm.from_pointisotherm(point, model=models, **options)
        elif entrypoint == 'guess':
            fitted = pygaps.ModelIsotherm.guess(
                pressure=point.pressure(), loading=point.loading(),
                models=['Langmuir'] if models == 'Langmuir' else models,
                **point.to_dict(), **options,
            )
        else:
            fitted = pgm.model_iso(point, model=models, **options)

        if models != 'Langmuir':
            assert set(guesses['Henry']) == {'K'}
        assert set(guesses['Langmuir']) == {'K', 'n_m'}
        assert guesses['Langmuir']['n_m'] == 6
        assert fitted.model.name == 'Langmuir'
        assert options == {'param_guess': {'n_m': 6}, 'param_bounds': {'K': [0.1, 10]}}

    @pytest.mark.parametrize('option', ['param_guess', 'param_bounds'])
    def test_isotherm_selection_unknown_parameter(self, basic_pointisotherm, option):
        with pytest.raises(pgEx.ParameterError, match='not a valid parameter'):
            pgm.model_iso(basic_pointisotherm, model=['Henry', 'Langmuir'], **{option: {'typo': 1}})

    @mpl_cleanup
    @pytest.mark.parametrize('file', [data['file'] for data in DATA.values()])
    def test_isotherm_create_guess(self, file, data_char_path):
        """Check isotherm can be guessed from PointIsotherm."""

        filepath = data_char_path / file
        isotherm = pgp.isotherm_from_json(filepath)

        pygaps.ModelIsotherm.from_pointisotherm(isotherm, model='guess', verbose=True)

        pygaps.ModelIsotherm.from_pointisotherm(isotherm, model=['Henry', 'Langmuir'], verbose=True)

        with pytest.raises(pgEx.ParameterError):
            pygaps.ModelIsotherm.from_pointisotherm(isotherm, model=['Henry', 'DummyModel'], verbose=True)

    ##########################

    @pytest.mark.parametrize(
        'expected, parameters',
        PRESSURE_PARAM,
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
        assert basic_modelisotherm.pressure(5, indexed=True).equals(pandas.Series([1.0, 2.25, 3.5, 4.75, 6.0], name='loading'))

    @pytest.mark.parametrize(
        'expected, parameters',
        LOADING_PARAM,
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
        assert_series_equal(basic_modelisotherm.loading(5, indexed=True), pandas.Series([1.0, 2.25, 3.5, 4.75, 6.0]))

    ##########################

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        PRESSURE_AT_PARAM,
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
        LOADING_AT_PARAM,
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

    def test_fractional_loading_conversion_paths(self, fractional_conversion_parameters):
        parameters = fractional_conversion_parameters
        model = pygaps.ModelIsotherm(
            pressure=[1, 2, 3],
            loading=[2, 4, 6],
            model='Henry',
            **parameters,
        )
        conversion = {
            'loading_basis': 'fraction',
            'material_basis': 'volume',
            'material_unit': 'cm3',
        }

        assert model.loading_at(2, **conversion) == pytest.approx(0.16)
        assert model.loading(points=3, **conversion)[1] == pytest.approx(0.16)
        assert model.pressure_at(0.16, loading_unit='cm3', **conversion) == pytest.approx(2)

        fractional_parameters = {**parameters, 'loading_basis': 'fraction', 'loading_unit': None}
        fractional_model = pygaps.ModelIsotherm(
            pressure=[1, 2, 3],
            loading=[0.01, 0.02, 0.03],
            model='Henry',
            **fractional_parameters,
        )
        material_conversion = {'material_basis': 'volume', 'material_unit': 'cm3'}

        assert fractional_model.loading_at(1, **material_conversion) == pytest.approx(0.04)
        assert fractional_model.loading(points=3, **material_conversion)[0] == pytest.approx(0.04)
        assert fractional_model.loading(loading_basis='percent', **material_conversion)[0] == pytest.approx(4)
        assert fractional_model.pressure_at(
            0.04,
            loading_basis='fraction',
            loading_unit='cm3',
            **material_conversion,
        ) == pytest.approx(1)

    @pytest.mark.parametrize(
        'inp, expected, parameters',
        [
            (1, 1, dict()),
            (100000, 1, dict(pressure_unit='Pa')),
            (0.5, 3.89137, dict(pressure_mode='relative')),
        ],
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
        assert basic_modelisotherm.spreading_pressure_at(inp, **parameters) == pytest.approx(expected, 1e-5)

    @pytest.mark.parametrize('method', ['pressure', 'loading', 'pressure_at', 'loading_at', 'spreading_pressure_at'])
    def test_isotherm_wrong_branch(self, basic_modelisotherm, method):
        with pytest.raises(pgEx.ParameterError, match="based on an 'ads' branch .* supplied was 'des'"):
            getattr(basic_modelisotherm, method)(1, branch='des')

    @mpl_cleanup
    def test_isotherm_print_parameters(self, basic_modelisotherm):
        """Checks isotherm can print its own info."""

        print(basic_modelisotherm)
        basic_modelisotherm.plot()
        basic_modelisotherm.print_info()
