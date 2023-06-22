"""
This configuration file contains data required for testing
scientific pygaps functions on real or model data.
In this file there are:

    - references to sample isotherm files

"""

import pytest

DATA_IAST_PATH = pytest.DATA_PATH / 'iast'

DATA_IAST = {
    'CH4': {
        'file': 'MOF-5(Zn) CH4 298K.json',
    },
    'C2H6': {
        'file': 'MOF-5(Zn) C2H6 298K.json',
    },
}
