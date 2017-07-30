import sys

import pytest

windows = pytest.mark.skipif(
    sys.platform != 'win32', reason="requires windows")


@windows
def test_func_skipped():
    """Test the function"""
    return
