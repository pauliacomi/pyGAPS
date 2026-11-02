"""Verify documentation configuration without invoking hosted services."""

import runpy
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.documentation
ROOT = Path(__file__).resolve().parents[2]


def test_source_links_follow_checkout(monkeypatch):
    monkeypatch.delenv('READTHEDOCS_GIT_COMMIT_HASH', raising=False)
    config = runpy.run_path(str(ROOT / 'docs' / 'conf.py'))
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert config['release_ref'] == revision
    assert 'nbviewer.org/github/' in config['nbsphinx_prolog']
    assert '<script>' not in config['nbsphinx_prolog']
    assert config['nbsphinx_execute'] == 'never'


def test_source_links_follow_hosted_revision(monkeypatch):
    monkeypatch.setenv('READTHEDOCS_GIT_COMMIT_HASH', 'a' * 40)
    config = runpy.run_path(str(ROOT / 'docs' / 'conf.py'))
    assert config['release_ref'] == 'a' * 40


def test_optional_spelling_configuration(monkeypatch):
    monkeypatch.setenv('SPELLCHECK', '1')
    config = runpy.run_path(str(ROOT / 'docs' / 'conf.py'))
    assert 'sphinxcontrib.spelling' in config['extensions']
    assert config['spelling_lang'] == 'en_GB'
