"""
Basic tests regarding module import and functionality
"""

import pytest
import sys


def test_python_three(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'version_info', (2, 7, 0, 'final', 0))

    del sys.modules['adsutils']

    with pytest.raises(SystemExit):
        __import__('adsutils')

    return


def test_dependency_check(monkeypatch):

    monkeypatch.delitem(sys.modules, 'pandas')

    with pytest.raises(ImportError):
        __import__('adsutils')

    return
