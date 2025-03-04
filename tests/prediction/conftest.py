"""
This configuration file contains data required for testing
scientific pygaps functions on real or model data.
"""

from ..conftest import DATA_PATH

DATA_WHITTAKER_PATH = DATA_PATH / 'enth_whittaker'
DATA_IAST_PATH = DATA_PATH / 'iast'

DATA_IAST = {
    'CH4': {
        'file': 'MOF-5(Zn) CH4 298K.json',
    },
    'C2H6': {
        'file': 'MOF-5(Zn) C2H6 298K.json',
    },
}

DATA_ETI = {
    'predict_presssure_raw_single_point': {
        'T_experiment': 298,
        'T_predict': 330,
        'enthalpy': [20,],
        'P_experiment': [1,],
        'P_predict': [2.187450035680577,],
    },
}

DATA_WHITTAKER = {
    'example1': {
        'file': 'whittaker_iso_1.aiff',
        'ref_enth': 16.08745,
    }
}
