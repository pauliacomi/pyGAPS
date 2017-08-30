"""
Basic tests regarding module import and functionality
"""

import sys

import pytest


@pytest.mark.skip(reason="not well implemented")
def test_python_three(monkeypatch):
    monkeypatch.setattr(sys, 'version_info', (2, 7, 0, 'final', 0))

    del sys.modules['pygaps']

    with pytest.raises(SystemExit):
        __import__('pygaps')

    return


@pytest.mark.skip(reason="not well implemented")
def test_dependency_check(monkeypatch):

    monkeypatch.delitem(sys.modules, 'pandas')

    with pytest.raises(ImportError):
        __import__('pygaps')

    return
