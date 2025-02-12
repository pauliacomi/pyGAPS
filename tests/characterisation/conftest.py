"""
This configuration file contains data required for testing
scientific pygaps functions on real or model data.
In this file there are:

    - references to sample isotherm files
    - pre-calculated values for each isotherm on various
      characterisation tests.

Explanation of parameters:

'bet_area':             BET area automatically calculated
'bet_area_s':           BET area in a selected range
'bet_area_des':         BET area for desorption branch
'langmuir_area':        Langmuir area automatically calculated
's_langmuir_area':      Langmuir area in a selected range
't_area':               t-plot calculated area
't_pore_volume':        t-plot calculated volume
's_t_area':             t-plot calculated area in a selected range
'as_ref':               reference alpha-s isotherm
'as_area':              alpha-s calculated area
'as_pore_volume':       alpha-s calculated volume
's_as_area':            alpha-s calculated area in a selected range
'Khi_slope':            initial henry constant (slope method)
'Khi_virial':           initial henry constant (virial method)
'dr_volume':            Dubinin-Radushkevitch calculated micropore volume
'dr_potential':         Dubinin-Radushkevitch calculated surface potential
'da_volume':            Dubinin-Astakov calculated micropore volume
'da_potential':         Dubinin-Astakov calculated surface potential
'psd_meso_pore_size':   Primary pore size peak, mesopore range
'psd_micro_pore_size':  Primary pore size peak, micropore range
'psd_dft_pore_size':    Primary pore size peak, DFT range
"""

import pytest


@pytest.fixture
def data_char_path(request):
    """Fixture for providing the path to characterisation data."""
    return request.config.DATA_PATH / 'characterisation'


@pytest.fixture
def data_isosteric_path(request):
    """Fixture for providing the path to isosteric data."""
    return request.config.DATA_PATH / 'enth_isosteric'


@pytest.fixture
def data_whittaker_path(request):
    """Fixture for providing the path to Whittaker data."""
    return request.config.DATA_PATH / 'enth_whittaker'


@pytest.fixture
def data_calo_path(request):
    """Fixture for providing the path to calorimetry data."""
    return request.config.DATA_PATH / 'calorimetry'


DATA = {
    'MCM-41': {
        'file': 'MCM-41 N2 77K.json',
        'bet_area': 350.0,
        'bet_area_s': 350.0,
        'langmuir_area': 1450.0,
        'langmuir_area_s': 550.0,
        't_area': 340.0,
        't_pore_volume': 0.28,
        's_t_area': 55.0,
        'as_ref': 'SiO2',
        'as_area': 350,
        'as_volume': 0.3,
        's_as_area': 360,
        'Khi_slope': 57000,
        'Khi_virial': 195000,
        'psd_meso_pore_size': 3.3,
        'psd_dft_pore_size': 3.4,
    },
    'NaY': {
        'file': 'NaY N2 77K.json',
        'bet_area': 700.0,
        'langmuir_area': 1100.0,
        't_area': 160.0,
        't_pore_volume': 0.26,
        'Khi_slope': 1770000,
        'Khi_virial': 1260000,
    },
    'SiO2': {
        'file': 'SiO2 N2 77K.json',
        'bet_area': 200.0,
        'bet_area_des': 190.0,
        'langmuir_area': 800,
        't_area': 320.0,
        't_pore_volume': 0.0,
        'Khi_slope': 780,
        'Khi_virial': 249,
    },
    'Takeda 5A': {
        'file': 'Takeda 5A N2 77K.json',
        'bet_area': 1075.0,
        'langmuir_area': 1600.0,
        't_area': 1100.0,
        't_pore_volume': 0.43,
        'Khi_slope': 1600000,
        'Khi_virial': 4300000,
        'dr_volume': 0.484,
        'dr_potential': 5.84,
        'da_volume': 0.346,
        'da_potential': 7.071,
        'psd_micro_pore_size': 0.6,
        'psd_dft_pore_size': 0.5,
    },
    'UiO-66(Zr)': {
        'file': 'UiO-66(Zr) N2 77K.json',
        'bet_area': 1250.0,
        'langmuir_area': 1350.0,
        't_pore_volume': 0.48,
        'Khi_slope': 700000,
        'Khi_virial': 1350000,
        'psd_micro_pore_size': 0.7,
        'psd_dft_pore_size': 0.6,
    },
}

DATA_ISOSTERIC = {
    't1': {
        'file': 'BAX 1500 C4H10 298K.json',
    },
    't2': {
        'file': 'BAX 1500 C4H10 323K.json',
    },
    't3': {
        'file': 'BAX 1500 C4H10 348K.json',
    },
}

DATA_CALO = {
    'HKUST-1': {
        'file': 'HKUST-1(Cu) CO2 303K.json',
        'ienth': 27,
    },
    'Takeda 5A': {
        'file': 'Takeda 5A CO2 303K.json',
        'ienth': 35,
    },
}

DATA_WHITTAKER = {
    'example1': {
        'file': 'whittaker_iso_1.aiff',
        'ref_enth': 16.08745,
    }
}
