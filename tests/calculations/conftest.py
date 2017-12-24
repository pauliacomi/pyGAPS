import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'docs', 'examples', 'data')

DATA_N77_PATH = os.path.join(DATA_PATH, 'characterisation')
DATA_IAST_PATH = os.path.join(DATA_PATH, 'iast')
DATA_ISOSTERIC_PATH = os.path.join(DATA_PATH, 'isosteric')
DATA_CALO_PATH = os.path.join(DATA_PATH, 'calorimetry')

DATA = {
    'MCM-41': {
        'file': 'MCM-41 N2 77.355.json',
        'bet_area': 400.0,
        's_bet_area': 350.0,
        'langmuir_area': 1450.0,
        's_langmuir_area': 500.0,
        't_pore_volume': 0.28,
        't_area': 80.0,
        'Khslope': 57000,
        'Khvirial': 200000,
    },
    'NaY': {
        'file': 'NaY N2 77.355.json',
        'bet_area': 700.0,
        'langmuir_area': 1100.0,
        't_pore_volume': 0.26,
        't_area': 120.0,
        'Khslope': 1770000,
        'Khvirial': 1260000,
    },
    'SiO2': {
        'file': 'SiO2 N2 77.355.json',
        'bet_area': 200.0,
        'langmuir_area': 850.0,
        't_pore_volume': 0.0,
        't_area': 280.0,
        'Khslope': 780,
        'Khvirial': 250,
    },
    'Takeda 5A': {
        'file': 'Takeda 5A N2 77.355.json',
        'bet_area': 1075.0,
        'langmuir_area': 1600.0,
        't_pore_volume': 0.43,
        't_area': 130.0,
        'Khslope': 1610000,
        'Khvirial': 4300000,
    },
    'UiO-66(Zr)': {
        'file': 'UiO-66(Zr) N2 77.355.json',
        'bet_area': 1250.0,
        'langmuir_area': 1350.0,
        't_pore_volume': 0.48,
        't_area': 20.0,
        'Khslope': 700000,
        'Khvirial': 1350000,
    },

}

DATA_IAST = {
    'CH4': {
        'file': 'MOF-5(Zn) - IAST - CH4.json',
    },
    'C2H6': {
        'file': 'MOF-5(Zn) - IAST - C2H6.json',
    },
}

DATA_ISOSTERIC = {
    't1': {
        'file': 'BAX 1500 - Isosteric Heat - 298.json',
    },
    't2': {
        'file': 'BAX 1500 - Isosteric Heat - 323.json',
    },
    't3': {
        'file': 'BAX 1500 - Isosteric Heat - 348.json',
    },
}

DATA_CALO = {
    't1': {
        'file': 'HKUST-1(Cu) KRICT.json',
        'ienth': 27,
    },
    't2': {
        'file': 'Takeda 5A Test CO2.json',
        'ienth': 35,
    },
}
