"""
This configuration file contains data required for testing
scientific pygaps functions on real or model data.
In this file there are:

    - references to sample isotherm files

"""

from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / 'docs' / 'examples' / 'data'
DATA_IAST_PATH = DATA_PATH / 'iast'

DATA_IAST = {
    'CH4': {
        'file': 'MOF-5(Zn) - IAST - CH4.json',
    },
    'C2H6': {
        'file': 'MOF-5(Zn) - IAST - C2H6.json',
    },
}
