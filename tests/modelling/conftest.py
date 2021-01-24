"""
This configuration file contains data required for testing
isotherm models on pre-calculated data.
In this file there are:

    - references to sample isotherm files
    - pre-calculated relationships for various models


Explanation of parameters:

'initial_guess' :

    Ihe initial guess for the model parameters
    that is passed to the optimisation routine,
    at pressure=1 and loading=1.

'test_parameters' :

    Simple values for the model parameters which
    are used to produce the test data.

'test_data' :

    Pressure, loading and spreading pressure values
    pre-calculated with the 'test_parameters'.
    These are used as a test to check if the model
    outputs good values, as well as in a fitting
    test.

"""

import pytest

MODEL_DATA = {
    'Henry': {
        'initial_guess': {
            'K': 11
        },
        'test_parameters': {
            'K': 2
        },
        'test_values': {
            'pressure': [0.0, 1.0, 3.0],
            'loading': [0.0, 2.0, 6.0],
            'spreading_pressure': [0.0, 2.0, 6.0],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'Langmuir': {
        'initial_guess': {
            'K': 10,
            'n_m': 1.1
        },
        'test_parameters': {
            'K': 3,
            'n_m': 5
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 1.153846154, 3.75, 4.838709677],
            'spreading_pressure': [0.0, 1.311821322, 6.931471806, 17.16993602],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'DSLangmuir': {
        'initial_guess': {
            'K1': 4,
            'n_m1': 0.55,
            'K2': 6,
            'n_m2': 0.55
        },
        'test_parameters': {
            'K1': 3,
            'n_m1': 5,
            'K2': 10,
            'n_m2': 1
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 1.653846154, 4.659090909, 5.828808687],
            'spreading_pressure': [0.0, 2.004968503, 9.329367078, 21.78505654],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'TSLangmuir': {
        'initial_guess': {
            'K1': 2,
            'n_m1': 0.44,
            'K2': 4,
            'n_m2': 0.44,
            'K3': 4,
            'n_m3': 0.22
        },
        'test_parameters': {
            'K1': 3,
            'n_m1': 5,
            'K2': 10,
            'n_m2': 1,
            'K3': 0.1,
            'n_m3': 10
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 1.752856055, 5.568181818, 10.82880869],
            'spreading_pressure': [0.0, 2.104471811, 10.28246888, 28.71652834],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'BET': {
        'initial_guess': {
            'C': 10,
            'N': 0.01,
            'n_m': 1.1
        },
        'test_parameters': {
            'C': 5,
            'N': 0.05,
            'n_m': 10
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 3.361288046, 8.845643521, 19.8019802],
            'spreading_pressure': [0.0, 4.071387487, 18.34684514, 46.15120517],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'GAB': {
        'initial_guess': {
            'C': 100,
            'K': 0.01,
            'n_m': 1.1
        },
        'test_parameters': {
            'C': 50,
            'K': 0.01,
            'n_m': 10
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 0.477121545, 3.389600705, 9.416195857],
            'spreading_pressure': [0.0, 0.488378297, 4.088264558, 18.80312867],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'Freundlich': {
        'initial_guess': {
            'K': 11,
            'm': 1
        },
        'test_parameters': {
            'K': 5,
            'm': 5
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 3.154786722, 5.0, 7.924465962],
            'spreading_pressure': [0.0, 15.77393361, 25.0, 39.62232981],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'DA': {
        'initial_guess': {
            'e': 1000,
            'n_m': 1.1,
            'm': 1
        },
        'test_parameters': {
            'e': 3000,
            'n_m': 10,
            'm': 3
        },
        'test_values': {
            'pressure': [0.1, 0.5, 1.0],
            'loading': [6.362582158, 9.877415087, 10.0],
            'spreading_pressure': [6.0626826516, 19.879212055975, 26.78938534],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'DR': {
        'initial_guess': {
            'e': 1000,
            'n_m': 1.1
        },
        'test_parameters': {
            'e': 2000,
            'n_m': 10
        },
        'test_values': {
            'pressure': [0.1, 0.5, 1.0],
            'loading': [2.656768582, 8.868199956, 10.0],
            'spreading_pressure': [1.834278725, 11.06086651, 17.7245385],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'Quadratic': {
        'initial_guess': {
            'n_m': 0.55,
            'Ka': 10,
            'Kb': 100
        },
        'test_parameters': {
            'n_m': 10,
            'Ka': 0.1,
            'Kb': 1
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 0.294117647, 10.0, 19.70588235],
            'spreading_pressure': [0.0, 0.198026273, 7.419373447, 46.24972813],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'TemkinApprox': {
        'initial_guess': {
            'n_m': 1.1,
            'K': 10,
            'tht': 0
        },
        'test_parameters': {
            'n_m': 5,
            'K': 5,
            'tht': 1
        },
        'test_values': {
            'pressure': [0.0, 0.1, 1.0, 10.0],
            'loading': [0.0, 1.296296296, 3.587962963, 4.807728551],
            'spreading_pressure': [2.5, 4.249547763, 9.722686235, 19.75620621],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'Toth': {
        'initial_guess': {
            'n_m': 1.1,
            'K': 10,
            't': 1
        },
        'test_parameters': {
            'n_m': 5,
            'K': 3,
            't': 2
        },
        'test_values': {
            'pressure': [0.1, 1.0, 10.0],
            'loading': [1.436739428, 4.74341649, 4.997224535],
            'spreading_pressure': [1.47836523, 9.092232296, 20.473111121],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'JensenSeaton': {
        'initial_guess': {
            'K': 11,
            'a': 1,
            'b': 1,
            'c': 1
        },
        'test_parameters': {
            'K': 10,
            'a': 3,
            'b': 0.1,
            'c': 1
        },
        'test_values': {
            'pressure': [0.1, 1.0, 10.0],
            'loading': [0.7518610421836228, 2.481203007518797, 5.660377358],
            'spreading_pressure': [0.863759319324, 4.502267169, 12.9931948499],
            'spreading_pressure_mark': pytest.mark.okay,
        }
    },
    'Virial': {
        'initial_guess': {
            'K': 11,
            'A': 0.0,
            'B': 0.0,
            'C': 0.0
        },
        'test_parameters': {
            'K': 5,
            'A': 0.001,
            'B': 0.0001,
            'C': 0.0001
        },
        'test_values': {
            'pressure': [
                0.0, 0.040008193, 0.080033799, 0.120078938, 0.200240144,
                0.40128205
            ],
            'loading': [0.0, 0.2, 0.4, 0.6, 1.0, 2.0],
            'spreading_pressure':
            [0.0, 15.77393361, 18.77393361, 20.77393361, 25.0, 30.62232981],
            'spreading_pressure_mark':
            pytest.mark.xfail,
        }
    },
    'FHVST': {
        'initial_guess': {
            'n_m': 1.1,
            'K': 10,
            'a1v': 0
        },
        'test_parameters': {
            'n_m': 30,
            'K': 2,
            'a1v': 1
        },
        'test_values': {
            'pressure': [0.0, 0.10134005, 0.534198619, 44.75474093],
            'loading': [0.0, 0.2, 1.0, 20.0],
            'spreading_pressure': [0.0, 15.77393361, 25.0, 39.62232981],
            'spreading_pressure_mark': pytest.mark.xfail,
        }
    },
    'WVST': {
        'initial_guess': {
            'n_m': 1.1,
            'K': 10,
            'L1v': 1,
            'Lv1': 1
        },
        'test_parameters': {
            'n_m': 30,
            'K': 2,
            'L1v': 2,
            'Lv1': 1
        },
        'test_values': {
            'pressure': [0.0, 0.101346218, 0.534999558],
            'loading': [0.0, 0.2, 1.0],
            'spreading_pressure': [0.0, 15.77393361, 25.0],
            'spreading_pressure_mark': pytest.mark.xfail,
        }
    }
}
