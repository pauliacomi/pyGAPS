"""
Tests excel interaction
"""

from ..conftest import windows

import pygaps


@windows
def test_create_excel(basic_pointisotherm, tmpdir_factory):
    """Tests creation of excel file"""

    pygaps.isotherm_to_xl(basic_pointisotherm,
                          path=tmpdir_factory.mktemp('excel'))
