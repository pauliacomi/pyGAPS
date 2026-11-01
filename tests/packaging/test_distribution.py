"""Focused checks for archive validation, without building on every test run."""

import base64
import csv
import hashlib
import io
import tarfile
import zipfile

import pytest

from .check_distribution import RESOURCES
from .check_distribution import check_archives
from .check_distribution import check_metadata
from .check_distribution import check_sdist
from .check_distribution import check_wheel

METADATA = b'Metadata-Version: 2.4\nName: pygaps\nVersion: 1.0\nRequires-Python: >=3.10\n'
DIST_INFO_DIR = 'pygaps-1.0.dist-info'


@pytest.fixture
def wheel_files():
    return {
        **dict.fromkeys(RESOURCES, b'resource'),
        'pygaps/__init__.py': b'',
        'pygaps/cli/__main__.py': b'',
        f'{DIST_INFO_DIR}/METADATA': METADATA,
        f'{DIST_INFO_DIR}/WHEEL': b'Wheel-Version: 1.0\nTag: py3-none-any\n',
        f'{DIST_INFO_DIR}/entry_points.txt': b'[console_scripts]\npygaps = pygaps.cli:main\n',
    }


def write_wheel(path, files):
    record = io.StringIO()
    writer = csv.writer(record)
    for name, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode('ascii')
        writer.writerow([name, f'sha256={digest}', len(data)])
    writer.writerow([f'{DIST_INFO_DIR}/RECORD', '', ''])
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr(f'{DIST_INFO_DIR}/RECORD', record.getvalue())
    return path


def write_sdist(path, missing=None):
    files = {
        **{f'src/{name}': b'resource' for name in RESOURCES},
        'src/pygaps/__init__.py': b'',
        'PKG-INFO': METADATA,
        'pyproject.toml': b'',
        'README.rst': b'',
        'LICENSE': b'',
    }
    if missing:
        del files[missing]
    with tarfile.open(path, 'w:gz') as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(f'pygaps-1.0/{name}')
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return path


def test_valid_distributions(tmp_path, wheel_files):
    wheel = write_wheel(tmp_path / 'pygaps.whl', wheel_files)
    sdist = write_sdist(tmp_path / 'pygaps.tar.gz')
    assert check_wheel(wheel) == check_sdist(sdist) == '1.0'
    check_archives(sdist, wheel)


@pytest.mark.parametrize('resource', RESOURCES)
def test_missing_wheel_resource(tmp_path, wheel_files, resource):
    del wheel_files[resource]
    with pytest.raises(ValueError, match='Missing archive members'):
        check_wheel(write_wheel(tmp_path / 'missing.whl', wheel_files))


@pytest.mark.parametrize('name', ['pygaps/data/__pycache__/data.pyc', 'pygaps/data/cache.pyc', '../escaped.py', '/escaped.py'])
def test_unwanted_wheel_member(tmp_path, wheel_files, name):
    wheel_files[name] = b'unwanted'
    with pytest.raises(ValueError, match='Generated archive member|Unsafe archive member'):
        check_wheel(write_wheel(tmp_path / 'unwanted.whl', wheel_files))


def test_invalid_entry_point(tmp_path, wheel_files):
    wheel_files[f'{DIST_INFO_DIR}/entry_points.txt'] = b'[console_scripts]\npygaps = wrong:main\n'
    with pytest.raises(ValueError, match='console entry point'):
        check_wheel(write_wheel(tmp_path / 'wrong.whl', wheel_files))


def test_record_corruption(tmp_path, wheel_files):
    wheel = write_wheel(tmp_path / 'corrupt.whl', wheel_files)
    with zipfile.ZipFile(wheel) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    # Change the payload without updating RECORD so its original hash no longer matches.
    members[RESOURCES[0]] = b'tampered'
    with zipfile.ZipFile(wheel, 'w') as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    with pytest.raises(ValueError, match='RECORD hash mismatch'):
        check_wheel(wheel)


def test_missing_sdist_resource(tmp_path):
    with pytest.raises(ValueError, match='Missing archive members'):
        check_sdist(write_sdist(tmp_path / 'missing.tar.gz', missing=f'src/{RESOURCES[0]}'))


@pytest.mark.parametrize('raw', [b'Name: pygaps\n', METADATA + b'Version: 2.0\n', METADATA.replace(b'pygaps', b'other')])
def test_invalid_metadata(raw):
    with pytest.raises(ValueError, match='metadata field|distribution name'):
        check_metadata(raw)


def test_version_mismatch(tmp_path, wheel_files):
    wheel_files[f'{DIST_INFO_DIR}/METADATA'] = METADATA.replace(b'Version: 1.0', b'Version: 2.0')
    with pytest.raises(ValueError, match='versions differ'):
        check_archives(write_sdist(tmp_path / 'source.tar.gz'), write_wheel(tmp_path / 'wheel.whl', wheel_files))
