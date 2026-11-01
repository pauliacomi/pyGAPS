"""Observable CLI contracts using real files and scientific calculations."""

import builtins
import subprocess
import sys
from importlib.metadata import version

import numpy
import pytest

import pygaps
import pygaps.characterisation as pgc
import pygaps.parsing as pgp
from pygaps.cli import cli as cli_module
from pygaps.cli import main
from pygaps.utilities.exceptions import CalculationError

from ..test_utils import mpl_cleanup

READERS = {'.json': pgp.isotherm_from_json, '.csv': pgp.isotherm_from_csv, '.xlsx': pgp.isotherm_from_xl, '.aif': pgp.isotherm_from_aif}
WRITERS = {'.json': 'to_json', '.csv': 'to_csv', '.xlsx': 'to_xl', '.aif': 'to_aif'}
AVOGADRO = 6.02214076e23
NITROGEN_CROSS_SECTION_NM2 = 0.162


def synthetic_isotherm(pressure, loading, relative=False):
    return pygaps.PointIsotherm(
        pressure=pressure,
        loading=loading,
        material='cli-test',
        adsorbate='nitrogen',
        temperature=77,
        temperature_unit='K',
        pressure_mode='relative' if relative else 'absolute',
        pressure_unit=None if relative else 'bar',
        loading_basis='molar',
        loading_unit='mmol',
        material_basis='mass',
        material_unit='g',
    )


@pytest.fixture
def input_json(tmp_path):
    pressure = numpy.geomspace(0.001, 10, 64)
    iso = synthetic_isotherm(pressure, 5 * 3 * pressure / (1 + 3 * pressure))
    path = tmp_path / 'input.json'
    iso.to_json(path)
    return path


@pytest.mark.cli
class TestCLI:
    @pytest.mark.parametrize('arguments', [[], ['--help']])
    def test_help(self, arguments, capsys):
        if arguments:
            with pytest.raises(SystemExit) as error:
                main(arguments)
            assert error.value.code == 0
        else:
            assert main(arguments) is None
        output = capsys.readouterr()
        assert 'usage: pygaps' in output.out
        assert '--characterize' in output.out and '--convert' in output.out
        assert output.err == ''

    def test_version(self, capsys):
        assert main(['--version']) is None
        output = capsys.readouterr()
        assert output.out.strip() == version('pygaps')
        assert output.err == ''

    def test_no_argument_call(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, 'argv', ['pygaps', '--version'])
        main()
        assert capsys.readouterr().out.strip() == version('pygaps')

    @pytest.mark.parametrize('argument', ['--help', '--version'])
    def test_module_entrypoint(self, argument):
        result = subprocess.run([sys.executable, '-m', 'pygaps.cli', argument], capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stderr
        if argument == '--help':
            assert 'usage: pygaps' in result.stdout
        else:
            assert result.stdout.strip() == version('pygaps')

    @pytest.mark.parametrize('suffix', WRITERS)
    def test_default_formats(self, suffix, input_json, tmp_path, capsys):
        iso = pgp.isotherm_from_json(input_json)
        path = tmp_path / f'format{suffix}'
        getattr(iso, WRITERS[suffix])(path)
        main([str(path)])
        output = capsys.readouterr()
        assert 'cli-test' in output.out
        assert 'nitrogen' in output.out
        assert output.err == ''

    def test_legacy_xls_input(self, request, capsys):
        path = next((request.config.DATA_PATH / 'parsing').rglob('*.xls'))
        iso = pgp.isotherm_from_xl(path)
        main([str(path)])
        assert str(iso.material) in capsys.readouterr().out

    @pytest.mark.parametrize('method', ['a_bet', 'a_lang', 'kh'])
    @pytest.mark.parametrize('verbose', [False, True])
    @mpl_cleanup
    def test_characterize(self, method, verbose, tmp_path, monkeypatch, capsys):
        from matplotlib import pyplot

        pressure = numpy.linspace(0.05, 0.30, 26)
        if method == 'a_bet':
            loading = 2 * 80 * pressure / ((1 - pressure) * (1 + 79 * pressure))
        elif method == 'a_lang':
            loading = 5 * 3 * pressure / (1 + 3 * pressure)
        else:
            loading = 2 * pressure
        path = tmp_path / 'characterize.json'
        synthetic_isotherm(pressure, loading, relative=True).to_json(path)
        shown = []
        monkeypatch.setattr(pyplot, 'show', lambda: shown.append(True))
        printed = []

        def capture_result(result):
            printed.append(result)
            builtins.print(result)

        monkeypatch.setattr(cli_module, 'print', capture_result, raising=False)
        main([str(path), '-ch', method, *(['-v'] if verbose else [])])
        assert len(printed) == 1
        result = printed[0]
        assert capsys.readouterr().out.strip() == str(result)
        if method == 'kh':
            assert result == pytest.approx(2, rel=1e-8)
        else:
            capacity = 2 if method == 'a_bet' else 5
            expected_area = capacity * 1e-3 * AVOGADRO * NITROGEN_CROSS_SECTION_NM2 * 1e-18
            assert numpy.isfinite(result['area'])
            assert result['area'] == pytest.approx(expected_area, rel=1e-8)
            constant = 'c_const' if method == 'a_bet' else 'langmuir_const'
            assert result[constant] == pytest.approx(80 if method == 'a_bet' else 3, rel=1e-8)
        assert len(shown) == int(verbose)

    @pytest.mark.parametrize('model', ['guess', 'henry', 'langmuir', 'dslangmuir', 'bet'])
    @pytest.mark.parametrize('verbose', [False, True])
    @mpl_cleanup
    def test_model(self, model, verbose, tmp_path, monkeypatch, capsys):
        from matplotlib import pyplot

        pressure = numpy.geomspace(0.001, 10, 64)

        def curve(p):
            if model == 'henry':
                return 2 * p
            if model == 'dslangmuir':
                return 5 * 3 * p / (1 + 3 * p) + 1 * 10 * p / (1 + 10 * p)
            if model == 'bet':
                return 5 * 3 * p / ((1 - 0.05 * p) * (1 - 0.05 * p + 3 * p))
            return 5 * 3 * p / (1 + 3 * p)

        path = tmp_path / 'model-input.json'
        synthetic_isotherm(pressure, curve(pressure)).to_json(path)
        original = path.read_bytes()
        outpath = tmp_path / 'model.json'
        shown = []
        monkeypatch.setattr(pyplot, 'show', lambda: shown.append(True))
        main([str(path), '-md', model, '-o', str(outpath), *(['-v'] if verbose else [])])
        output = capsys.readouterr()
        restored = pgp.isotherm_from_json(outpath)
        held_pressure = numpy.sqrt(pressure[:-1] * pressure[1:])
        assert isinstance(restored, pygaps.ModelIsotherm)
        assert numpy.isfinite(restored.model.rmse) and restored.model.rmse < 1e-4
        numpy.testing.assert_allclose(restored.loading_at(held_pressure), curve(held_pressure), rtol=1e-4, atol=1e-10)
        if model != 'guess':
            assert restored.model.name.lower() == model
        assert str(restored.material) == 'cli-test' and restored.adsorbate == 'nitrogen'
        assert restored.temperature == 77 and restored.pressure_unit == 'bar'
        assert path.read_bytes() == original
        assert len(shown) == int(verbose)
        assert ('cli-test' in output.out) == verbose

    @pytest.mark.parametrize('suffix', [*WRITERS, '.xls'])
    @pytest.mark.parametrize('operation', ['convert', 'model'])
    def test_export_formats(self, suffix, operation, input_json, tmp_path):
        destination = tmp_path / f'export{suffix}'
        if operation == 'convert':
            pressure = numpy.arange(1.0, 7.0)
            synthetic_isotherm(pressure, 2 * pressure).to_json(input_json)
            args = ['-cv', 'pressure_unit=Pa,loading_unit=mol,material_unit=kg']
        else:
            args = ['-md', 'langmuir']
        arguments = [str(input_json), *args, '-o', str(destination)]
        original = input_json.read_bytes()
        if suffix == '.xls':
            with pytest.warns(UserWarning, match=r'\.xls'):
                main(arguments)
            assert not destination.exists()
            destination = destination.with_suffix('.xlsx')
        else:
            main(arguments)
        result = READERS[destination.suffix](destination)
        source = pgp.isotherm_from_json(input_json)
        if operation == 'convert':
            assert result.units['pressure_unit'] == 'Pa'
            assert result.loading_unit == 'mol' and result.material_unit == 'kg'
            numpy.testing.assert_allclose(result.pressure(), source.pressure() * 1e5, rtol=1e-10)
            numpy.testing.assert_allclose(result.loading(), source.loading(), rtol=1e-10)
        else:
            assert isinstance(result, pygaps.ModelIsotherm)
            assert result.model.name == 'Langmuir'
            numpy.testing.assert_allclose(result.loading_at(source.pressure()), source.loading(), rtol=1e-4, atol=1e-10)
        assert result.adsorbate == source.adsorbate
        assert result.material == source.material
        assert input_json.read_bytes() == original

    @pytest.mark.parametrize('conversion, expected_scale', [('loading_unit=mol', 1e-3), ('material_unit=kg', 1e3)])
    def test_conversion_individual_scaling(self, conversion, expected_scale, input_json, tmp_path):
        destination = tmp_path / 'scaled.json'
        main([str(input_json), '-cv', conversion, '-o', str(destination)])
        source = pgp.isotherm_from_json(input_json)
        result = pgp.isotherm_from_json(destination)
        numpy.testing.assert_allclose(result.loading(), source.loading() * expected_scale, rtol=1e-10)
        numpy.testing.assert_allclose(result.pressure(), source.pressure(), rtol=1e-10)

    def test_model_without_output(self, input_json, tmp_path, capsys):
        main([str(input_json), '-md', 'langmuir'])
        assert list(tmp_path.iterdir()) == [input_json]
        assert capsys.readouterr().out == ''

    @mpl_cleanup
    def test_plot(self, input_json, monkeypatch, capsys):
        from matplotlib import pyplot

        shown = []
        monkeypatch.setattr(pyplot, 'show', lambda: shown.append(True))
        main([str(input_json), '-p'])
        assert shown == [True]
        assert pyplot.get_fignums()
        assert capsys.readouterr().out == ''

    def test_verbose_conversion_without_export(self, input_json, capsys):
        original = input_json.read_bytes()
        main([str(input_json), '-cv', ' pressure_unit = Pa , loading_unit = mol ', '-v'])
        assert 'cli-test' in capsys.readouterr().out
        assert input_json.read_bytes() == original

    @pytest.mark.parametrize(
        'conversion, message',
        [
            ('pressure_unit', 'key=value'),
            ('', 'key=value'),
            ('pressure_unit=bar,', 'key=value'),
            ('pressure_unit=', 'cannot be empty'),
            ('pressure_unit=bar=extra', 'key=value'),
            ('unknown=bar', 'Unknown conversion key'),
            ('pressure_unit=bar,pressure_unit=Pa', 'Duplicate conversion key'),
            ('pressure_unit=bad', 'Unit selected'),
            ('pressure_mode=bad', 'Basis selected'),
            ('loading_unit=bad', 'Unit selected'),
            ('loading_basis=bad', 'Basis selected'),
            ('material_unit=bad', 'Unit selected'),
            ('material_basis=bad', 'Basis selected'),
        ],
    )
    def test_conversion_errors(self, conversion, message, input_json, capsys):
        with pytest.raises(SystemExit) as error:
            main([str(input_json), '-cv', conversion])
        assert error.value.code == 2
        output = capsys.readouterr()
        assert 'usage: pygaps' in output.err and message in output.err
        assert 'Traceback' not in output.err and output.out == ''

    @pytest.mark.parametrize(
        'extra',
        [
            ['-md', 'henry', '-cv', 'pressure_unit=Pa'],
            ['-p', '-ch', 'kh'],
            ['-ch', 'kh', '-md', 'henry'],
            ['-p', '-cv', 'pressure_unit=Pa'],
        ],
    )
    def test_conflicting_actions(self, extra, input_json, capsys):
        with pytest.raises(SystemExit) as error:
            main([str(input_json), *extra])
        assert error.value.code == 2
        assert 'not allowed with argument' in capsys.readouterr().err

    @pytest.mark.parametrize('extra', [['--unknown'], ['-ch', 'bad'], ['-md', 'bad']])
    def test_invalid_options(self, extra, input_json, capsys):
        with pytest.raises(SystemExit) as error:
            main([str(input_json), *extra])
        assert error.value.code == 2
        assert 'error:' in capsys.readouterr().err

    @pytest.mark.parametrize('kind', ['missing', 'directory', 'input-suffix', 'output-suffix'])
    def test_file_errors(self, kind, input_json, tmp_path, capsys):
        if kind == 'missing':
            args = [str(tmp_path / 'missing.json')]
        elif kind == 'directory':
            args = [str(tmp_path)]
        elif kind == 'input-suffix':
            path = tmp_path / 'input.txt'
            path.write_bytes(input_json.read_bytes())
            args = [str(path)]
        else:
            args = [str(input_json), '-md', 'henry', '-o', str(tmp_path / 'output.txt')]
        with pytest.raises(SystemExit) as error:
            main(args)
        assert error.value.code == 2
        output = capsys.readouterr()
        assert 'error:' in output.err and 'Traceback' not in output.err
        assert output.out == ''

    @pytest.mark.parametrize('action', [['-ch', 'kh'], ['-p'], ['-md', 'henry'], ['-cv', 'pressure_unit=Pa']])
    def test_base_input_action_errors(self, action, basic_isotherm, tmp_path, capsys):
        path = tmp_path / 'metadata.json'
        basic_isotherm.to_json(path)
        with pytest.raises(SystemExit) as error:
            main([str(path), *action])
        assert error.value.code == 2
        assert 'requires point' in capsys.readouterr().err

    @pytest.mark.parametrize('action', [['-md', 'henry'], ['-cv', 'pressure_unit=Pa']])
    def test_model_input_action_errors(self, action, basic_modelisotherm, tmp_path, capsys):
        path = tmp_path / 'model.json'
        basic_modelisotherm.to_json(path)
        with pytest.raises(SystemExit) as error:
            main([str(path), *action])
        assert error.value.code == 2
        assert 'requires point isotherm data' in capsys.readouterr().err

    def test_scientific_failure_propagates(self, input_json, monkeypatch):
        def fail(*args, **kwargs):
            raise CalculationError('scientific failure probe')

        monkeypatch.setattr(pgc, 'area_BET', fail)
        with pytest.raises(CalculationError, match='scientific failure probe'):
            main([str(input_json), '-ch', 'a_bet'])

    @pytest.mark.parametrize('exception', [CalculationError('scientific conversion probe'), RuntimeError('programming probe')])
    def test_unexpected_conversion_failure_propagates(self, exception, input_json, monkeypatch):
        def fail(*args, **kwargs):
            raise exception

        monkeypatch.setattr(pygaps.PointIsotherm, 'convert', fail)
        with pytest.raises(type(exception), match=str(exception)):
            main([str(input_json), '-cv', 'pressure_unit=Pa'])
