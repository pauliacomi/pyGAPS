"""Regression checks for shared test-state and plotting cleanup."""

import subprocess
import sys
import textwrap
import warnings
from contextlib import nullcontext
from pathlib import Path

import matplotlib
import pytest
from matplotlib import pyplot
from matplotlib import units

import pygaps
from pygaps.utilities import coolprop_utilities

from .test_utils import isolated_pygaps_state
from .test_utils import mpl_cleanup
from .test_utils import registered_object

PYTEST_PROBE_TIMEOUT = 120


@pytest.mark.parametrize('fail', [False, True])
def test_registry_restoration(fail):
    adsorbate = pygaps.Adsorbate.find('nitrogen')
    registry = pygaps.ADSORBATE_LIST
    members = list(registry)
    properties = adsorbate.properties
    aliases = adsorbate.alias
    name = adsorbate.name
    with pytest.raises(RuntimeError) if fail else nullcontext():
        with isolated_pygaps_state():
            registry.clear()
            properties['nested_probe'] = {'items': ['changed']}
            aliases.append('changed')
            adsorbate.properties = {}
            adsorbate.alias = []
            adsorbate.name = 'changed'
            if fail:
                raise RuntimeError('cleanup probe')
    assert pygaps.ADSORBATE_LIST is registry
    assert len(registry) == len(members)
    assert all(actual is expected for actual, expected in zip(registry, members))
    assert adsorbate.name == name
    assert adsorbate.properties is properties and 'nested_probe' not in properties
    assert adsorbate.alias is aliases and 'changed' not in aliases


@pytest.mark.parametrize('kind', ['Material', 'Adsorbate'])
@pytest.mark.parametrize('fail', [False, True])
def test_registration_identity_cleanup(kind, fail):
    registry = []
    item = getattr(pygaps, kind)('equal-name')
    other = getattr(pygaps, kind)('equal-name')
    with pytest.raises(RuntimeError) if fail else nullcontext():
        with registered_object(registry, item):
            registry.append(other)
            if fail:
                raise RuntimeError('cleanup probe')
    assert len(registry) == 1 and registry[0] is other


@pytest.mark.parametrize('change', ['unchanged', 'backend', 'fluid', 'failed-construction', 'failed-current-backend'])
def test_native_cache_restoration(monkeypatch, change):
    adsorbate = pygaps.Adsorbate.find('nitrogen')
    sentinel = object()
    monkeypatch.setattr(adsorbate, '_state', sentinel)
    monkeypatch.setattr(adsorbate, '_backend_mode', 'HEOS')
    if change == 'failed-current-backend':
        monkeypatch.setattr(adsorbate, '_state', None)
        monkeypatch.setattr(adsorbate, '_backend_mode', None)

    def fail_construction(*args):
        raise ValueError('native construction probe')

    with pytest.raises(ValueError, match='native construction probe') if change.startswith('failed-') else nullcontext():
        with isolated_pygaps_state():
            if change == 'backend':
                coolprop_utilities.COOLPROP_BACKEND = 'REFPROP'
            elif change == 'fluid':
                adsorbate.properties['backend_name'] = 'ARGON'
            elif change.startswith('failed-'):
                monkeypatch.setattr('pygaps.core.adsorbate.CP.AbstractState', fail_construction)
                if change == 'failed-construction':
                    coolprop_utilities.COOLPROP_BACKEND = 'REFPROP'
                adsorbate.backend
    assert pygaps.thermodynamic_backend() == 'HEOS'
    if change == 'unchanged':
        assert adsorbate._state is sentinel
    else:
        assert adsorbate._state is None and adsorbate._backend_mode is None
        calls = []
        rebuilt = object()

        def construct(mode, fluid):
            calls.append((mode, fluid))
            return rebuilt

        monkeypatch.setattr('pygaps.core.adsorbate.CP.AbstractState', construct)
        assert adsorbate.backend is rebuilt
        assert adsorbate.backend is rebuilt
        assert calls == [('HEOS', adsorbate.backend_name)]


@pytest.mark.parametrize('kind', ['Material', 'Adsorbate'])
def test_nested_property_restoration(kind):
    registry = pygaps.MATERIAL_LIST if kind == 'Material' else pygaps.ADSORBATE_LIST
    item = getattr(pygaps, kind)('nested-probe', nested={'values': [1, 2]})
    with registered_object(registry, item):
        properties = item.properties
        with isolated_pygaps_state():
            item.properties['nested']['values'].append(3)
        assert item.properties is properties
        assert item.properties['nested'] == {'values': [1, 2]}


def test_autouse_restoration_after_failed_test(tmp_path):
    probe = tmp_path / 'test_probe.py'
    probe.write_text(
        textwrap.dedent(
            """
            import pygaps
            from pygaps.utilities import coolprop_utilities

            registry = pygaps.ADSORBATE_LIST
            members = list(registry)
            adsorbate = pygaps.Adsorbate.find('nitrogen')
            properties = adsorbate.properties
            aliases = adsorbate.alias
            backend = pygaps.thermodynamic_backend()

            def test_mutates_and_fails():
                registry.clear()
                properties['cleanup_probe'] = {'values': [1]}
                aliases.append('cleanup_probe')
                coolprop_utilities.COOLPROP_BACKEND = 'REFPROP'
                assert False, 'intentional fixture teardown probe'

            def test_restored():
                assert pygaps.ADSORBATE_LIST is registry
                assert len(registry) == len(members)
                assert all(a is b for a, b in zip(registry, members))
                assert adsorbate.properties is properties
                assert 'cleanup_probe' not in properties
                assert adsorbate.alias is aliases
                assert 'cleanup_probe' not in aliases
                assert pygaps.thermodynamic_backend() == backend
            """
        ),
        encoding='utf-8',
    )
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '-c', str(root / 'pyproject.toml'), '-p', 'tests.conftest', str(probe), '-q'],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=PYTEST_PROBE_TIMEOUT,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert 'intentional fixture teardown probe' in output
    assert '1 failed, 1 passed' in output, output


@pytest.mark.parametrize('mode', ['reordered', 'distributed', 'reverse-option'])
def test_sqlite_scheduling_guard(mode):
    scenario = str(Path('tests') / 'parsing' / 'test_sqlite_db.py')
    options = [scenario, '--collect-only', '-q']
    if mode == 'reverse-option':
        options.append('--reverse-independent')
    code = textwrap.dedent(
        f"""
        import pytest

        class SchedulingProbe:
            def pytest_collection_modifyitems(self, config, items):
                if {mode!r} == 'reordered':
                    items.reverse()
                elif {mode!r} == 'distributed':
                    config.workerinput = {{}}

        raise SystemExit(pytest.main(
            {options!r},
            plugins=[SchedulingProbe()],
        ))
        """
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        timeout=PYTEST_PROBE_TIMEOUT,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 4, output
    assert 'shared SQLite scenario' in output, output


@pytest.mark.parametrize('generator', [False, True])
def test_plotting_cleanup_failure(generator):
    linewidth = matplotlib.rcParams['lines.linewidth']
    converters = units.registry.copy()
    filters = list(warnings.filters)

    def change_state():
        pyplot.figure()
        units.registry.clear()
        warnings.simplefilter('ignore')
        raise RuntimeError('plot cleanup probe')

    if generator:

        @mpl_cleanup({'lines.linewidth': 7})
        def plot():
            assert matplotlib.rcParams['lines.linewidth'] == 7
            yield 1
            change_state()

        iterator = plot()
        assert next(iterator) == 1
        with pytest.raises(RuntimeError, match='plot cleanup probe'):
            next(iterator)
    else:

        @mpl_cleanup({'lines.linewidth': 7})
        def plot():
            assert matplotlib.rcParams['lines.linewidth'] == 7
            change_state()

        with pytest.raises(RuntimeError, match='plot cleanup probe'):
            plot()

    assert matplotlib.rcParams['lines.linewidth'] == linewidth
    assert units.registry == converters
    assert warnings.filters == filters
    assert pyplot.get_fignums() == []


def test_plotting_default_style_and_return():
    @mpl_cleanup
    def plot():
        pyplot.figure()
        return 7

    assert plot() == 7
    assert pyplot.get_fignums() == []
    assert matplotlib.get_backend().lower() == 'agg'
