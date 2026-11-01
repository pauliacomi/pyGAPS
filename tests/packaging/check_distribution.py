"""Validate distributions and smoke-test a non-editable installation.

Run this script directly with ``archives SDIST WHEEL`` or
``installed WHEEL PREFIX``. The installed check must run outside the checkout.
"""

import argparse
import base64
import configparser
import csv
import hashlib
import io
import json
import math
import os
import sqlite3
import subprocess
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path
from pathlib import PurePosixPath

RESOURCES = (
    'pygaps/data/default.db',
    'pygaps/data/kernels/DFT-N2-77K-carbon-slit.csv',
    'pygaps/data/stdiso/Cabot BP280 carbon black.csv',
    'pygaps/data/stdiso/LiChrospher Si-1000 silica.csv',
)


def check_members(names, required):
    """Reject missing resources, unsafe paths and generated cache contents."""
    if len(names) != len(set(names)):
        raise ValueError('Archive contains duplicate members.')
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError(f'Unsafe archive member: {name}')
        if any(part in ('__pycache__', '.pytest_cache', '.ruff_cache', 'build') for part in path.parts) or path.suffix in ('.pyc', '.pyo'):
            raise ValueError(f'Generated archive member: {name}')
    missing = set(required) - set(names)
    if missing:
        raise ValueError(f'Missing archive members: {sorted(missing)}')


def check_metadata(raw):
    """Check basic core metadata without adding a packaging dependency."""
    metadata = BytesParser().parsebytes(raw)
    for field in ('Metadata-Version', 'Name', 'Version', 'Requires-Python'):
        if len(metadata.get_all(field, [])) != 1 or not metadata[field].strip():
            raise ValueError(f'Missing or ambiguous metadata field: {field}')
    if metadata['Name'].lower() != 'pygaps':
        raise ValueError(f"Unexpected distribution name: {metadata['Name']}")
    return metadata['Version']


def check_record(archive, record_path):
    """Validate wheel RECORD coverage, file sizes and hashes."""
    names = archive.namelist()
    rows = list(csv.reader(io.StringIO(archive.read(record_path).decode('utf-8'))))
    if any(len(row) != 3 for row in rows):
        raise ValueError('Malformed wheel RECORD.')
    if len(rows) != len(names) or {row[0] for row in rows} != set(names):
        raise ValueError('Wheel RECORD does not match archive members.')
    for name, digest, size in rows:
        if name == record_path:
            # RECORD cannot hash itself; its own hash and size fields must be blank.
            if digest or size:
                raise ValueError('RECORD must not hash itself.')
            continue
        data = archive.read(name)
        if not digest or not size or int(size) != len(data):
            raise ValueError(f'Missing or incorrect RECORD size/hash: {name}')
        algorithm, expected = digest.split('=', 1)
        if algorithm not in ('sha256', 'sha384', 'sha512'):
            raise ValueError(f'Unsupported RECORD hash: {algorithm}')
        # Wheel hashes use URL-safe Base64 with trailing padding removed.
        actual = base64.urlsafe_b64encode(hashlib.new(algorithm, data).digest()).rstrip(b'=').decode('ascii')
        if actual != expected:
            raise ValueError(f'RECORD hash mismatch: {name}')


def check_wheel(path):
    """Validate wheel resources, entry point and RECORD contents."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_paths = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata_paths) != 1:
            raise ValueError('Wheel must have exactly one metadata directory.')
        metadata_path = metadata_paths[0]
        dist_info_dir = metadata_path.rsplit('/', 1)[0]
        check_members(
            names,
            (
                *RESOURCES,
                'pygaps/__init__.py',
                'pygaps/cli/__main__.py',
                f'{dist_info_dir}/WHEEL',
                f'{dist_info_dir}/RECORD',
                f'{dist_info_dir}/entry_points.txt',
            ),
        )
        version = check_metadata(archive.read(metadata_path))
        wheel_metadata = BytesParser().parsebytes(archive.read(f'{dist_info_dir}/WHEEL'))
        if wheel_metadata['Wheel-Version'] != '1.0' or not wheel_metadata.get_all('Tag'):
            raise ValueError('Missing or unsupported wheel metadata.')
        entry_points = configparser.ConfigParser()
        entry_points.read_string(archive.read(f'{dist_info_dir}/entry_points.txt').decode('utf-8'))
        if entry_points.get('console_scripts', 'pygaps', fallback=None) != 'pygaps.cli:main':
            raise ValueError('Missing or incorrect pygaps console entry point.')
        check_record(archive, f'{dist_info_dir}/RECORD')
        return version


def check_sdist(path):
    """Check source-distribution resources and core build inputs."""
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        check_members([member.name for member in members], ())
        roots = {PurePosixPath(member.name).parts[0] for member in members}
        if len(roots) != 1:
            raise ValueError('Source distribution must have one root directory.')
        root = roots.pop()
        if any(not member.isfile() and not member.isdir() for member in members):
            raise ValueError('Source distribution contains links or special files.')
        files = {member.name: member for member in members if member.isfile()}
        check_members(
            list(files),
            (
                f'{root}/PKG-INFO',
                f'{root}/pyproject.toml',
                f'{root}/README.rst',
                f'{root}/LICENSE',
                f'{root}/src/pygaps/__init__.py',
                *(f'{root}/src/{name}' for name in RESOURCES),
            ),
        )
        with archive.extractfile(files[f'{root}/PKG-INFO']) as metadata_file:
            return check_metadata(metadata_file.read())


def check_archives(sdist, wheel):
    """Require matching versions in the source and wheel distributions."""
    source_version = check_sdist(sdist)
    wheel_version = check_wheel(wheel)
    if source_version != wheel_version:
        raise ValueError(f'Distribution versions differ: {source_version} / {wheel_version}')
    print(f'Validated sdist and wheel for pygaps {wheel_version}.')


def check_installed(wheel, prefix):
    """Exercise the installed package, console script and packaged data."""
    from importlib.metadata import distribution

    # Archive validation must work without importing an editable checkout or its dependencies.
    import pygaps
    from pygaps.data import KERNELS
    from pygaps.data import STANDARD_ISOTHERMS

    prefix = prefix.resolve()
    assert Path(sys.prefix).resolve() == prefix, 'Wrong virtual environment.'
    assert Path(pygaps.__file__).resolve().is_relative_to(prefix), 'Imported pygaps outside the isolated installation.'
    installed = distribution('pygaps')
    assert Path(installed.locate_file('')).resolve().is_relative_to(prefix), 'Metadata comes from outside the installation.'
    assert installed.version == pygaps.__version__ == check_wheel(wheel), 'Installed and built versions differ.'
    direct_url = installed.read_text('direct_url.json')
    assert not direct_url or not json.loads(direct_url).get('dir_info', {}).get('editable'), 'Editable installation detected.'
    assert pygaps.ADSORBATE_LIST, 'Packaged adsorbate data was not loaded.'
    assert pygaps.DATABASE.is_file() and pygaps.DATABASE.stat().st_size, 'Packaged database is missing or empty.'
    with sqlite3.connect(pygaps.DATABASE.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Packaged database integrity failed.'
    for name, resource in {**KERNELS, **STANDARD_ISOTHERMS}.items():
        assert resource.is_file() and resource.read_bytes(), f'Missing or empty registered resource: {name}'

    executable = prefix / 'Scripts' / 'pygaps.exe' if sys.platform == 'win32' else prefix / 'bin' / 'pygaps'
    # Console subprocesses do not inherit the parent's -I flag; remove source/home overrides.
    environment = {key: value for key, value in os.environ.items() if key.upper() not in ('PYTHONPATH', 'PYTHONHOME')}
    help_result = subprocess.run([str(executable), '--help'], capture_output=True, text=True, check=True, timeout=45, env=environment)
    assert 'usage: pygaps' in help_result.stdout, 'Console help is missing.'
    version_result = subprocess.run([str(executable), '--version'], capture_output=True, text=True, check=True, timeout=45, env=environment)
    assert version_result.stdout.strip() == installed.version, 'Console version differs from installed metadata.'

    check_bet_result()
    print(f'Installed-wheel smoke passed for pygaps {installed.version} in {prefix}.')


def check_bet_result():
    """Check JSON-to-BET against independently generated data and area."""
    from pygaps.characterisation import area_BET
    from pygaps.parsing import isotherm_from_json

    monolayer_mmol_per_g = 2
    bet_constant = 80
    cross_section_nm2 = 0.162
    avogadro_constant = 6.02214076e23
    pressures = [0.05 + index * 0.01 for index in range(26)]
    isotherm_data = {
        'file_version': '3.0',
        'material': 'packaging-smoke',
        'adsorbate': 'nitrogen',
        'temperature': 77.0,
        'temperature_unit': 'K',
        'pressure_mode': 'relative',
        'pressure_unit': None,
        'loading_basis': 'molar',
        'loading_unit': 'mmol',
        'material_basis': 'mass',
        'material_unit': 'g',
        'isotherm_data': [
            {'pressure': p, 'loading': monolayer_mmol_per_g * bet_constant * p / ((1 - p) * (1 + (bet_constant - 1) * p))}
            for p in pressures
        ],
    }
    result = area_BET(isotherm_from_json(json.dumps(isotherm_data)), p_limits=(0.05, 0.30))
    expected_area = monolayer_mmol_per_g * 1e-3 * avogadro_constant * cross_section_nm2 * 1e-18
    assert math.isclose(result['area'], expected_area, rel_tol=1e-8), f"Incorrect packaged BET result: {result['area']}"
    assert math.isclose(result['c_const'], bet_constant, rel_tol=1e-8), 'Incorrect packaged BET constant.'


def main():
    """Run archive validation or isolated installed-package checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    archives = commands.add_parser('archives')
    archives.add_argument('sdist', type=Path)
    archives.add_argument('wheel', type=Path)
    installed = commands.add_parser('installed')
    installed.add_argument('wheel', type=Path)
    installed.add_argument('prefix', type=Path)
    args = parser.parse_args()
    if args.command == 'archives':
        check_archives(args.sdist, args.wheel)
    else:
        check_installed(args.wheel, args.prefix)


if __name__ == '__main__':
    main()
