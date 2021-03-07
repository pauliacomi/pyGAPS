"""
This configuration file contains common data for
parametrizing various tests such as isotherms.
"""
PRESSURE_PARAM = [
    (1, {}),  # Standard return
    (100000, {
        'pressure_unit': 'Pa'
    }),  # Unit specified
    (0.128489, {
        'pressure_mode': 'relative'
    }),  # Mode relative
    (12.8489, {
        'pressure_mode': 'relative%'
    }),  # Mode relative%
    (0.128489, {
        'pressure_unit': 'Pa',
        'pressure_mode': 'relative'
    }),  # Mode and unit specified
    (3, {
        'limits': (2.3, 5.0)
    }),  # Range specified
]

LOADING_PARAM = [
    (1, {}),  # Standard return
    (0.001, {
        'loading_unit': 'mol'
    }),  # Loading unit specified
    (0.876484, {
        'loading_basis': 'volume',
        'loading_unit': 'cm3'
    }),  # Loading basis specified
    (1000, {
        'material_unit': 'kg'
    }),  # Adsorbent unit specified
    (2, {
        'material_basis': 'volume',
        'material_unit': 'cm3',
    }),  # Adsorbent basis specified
    (0.0280135, {
        'loading_basis': 'fraction',
    }),  # Fractional weight (will be 1/1000 mol * 28.01 g/mol)
    (2.80134, {
        'loading_basis': 'percent',
    }),  # Percent weight
    (
        0.01, {
            'loading_basis': 'fraction',
            'material_basis': 'molar',
            'material_unit': 'mmol',
        }
    ),  # Fractional molar (will be 1/1000 mol * 10 g/mol)
    (
        1.7529697, {
            'loading_basis': 'fraction',
            'material_basis': 'volume',
            'material_unit': 'cm3',
        }
    ),  # Fractional volume
    (
        56.02696, {
            'loading_basis': 'mass',
            'loading_unit': 'kg',
            'material_basis': 'volume',
            'material_unit': 'm3',
        }
    ),  # All specified
    (3.0, {
        'limits': (2.3, 5.0)
    }),  # Range specified
]

PRESSURE_AT_PARAM = [
    (1, 1, {}),  # Standard return
    (1, 1, {
        'branch': 'ads'
    }),  # Branch specified
    (1, 100000, {
        'pressure_unit': 'Pa'
    }),  # Pressure unit specified
    (2, 0.256978, {
        'pressure_mode': 'relative'
    }),  # Pressure mode specified
    (0.002, 2, {
        'loading_unit': 'mol'
    }),  # Loading unit specified
    (0.02808, 1.00237, {
        'loading_basis': 'mass',
        'loading_unit': 'g'
    }),  # Loading mode specified
    (1000, 1, {
        'material_unit': 'kg'
    }),  # Loading basis specified
    (2, 1, {
        'material_basis': 'volume',
        'material_unit': 'cm3'
    }),  # Adsorbent basis specified
    (
        0.1, 0.229334, {
            'pressure_mode': 'relative',
            'pressure_unit': 'Pa',
            'loading_basis': 'mass',
            'loading_unit': 'g',
            'material_basis': 'volume',
            'material_unit': 'cm3',
        }
    ),  # All specified
]

LOADING_AT_PARAM = [
    (1, 1, {}),  # Standard return
    (1, 1, {
        'branch': 'ads'
    }),  # Branch specified
    (100000, 1, {
        'pressure_unit': 'Pa'
    }),  # Pressure unit specified
    (0.256978, 2, {
        'pressure_mode': 'relative'
    }),  # Pressure mode specified
    (2, 0.002, {
        'loading_unit': 'mol'
    }),  # Loading unit specified
    (1.00237, 0.02808, {
        'loading_basis': 'mass',
        'loading_unit': 'g'
    }),  # Loading mode specified
    (1, 1000, {
        'material_unit': 'kg'
    }),  # Loading basis specified
    (1, 2, {
        'material_basis': 'volume',
        'material_unit': 'cm3'
    }),  # Adsorbent basis specified
    (
        0.229334, 0.1, {
            'pressure_unit': 'Pa',
            'pressure_mode': 'relative',
            'loading_basis': 'mass',
            'loading_unit': 'g',
            'material_basis': 'volume',
            'material_unit': 'cm3',
        }
    ),  # All specified
]
