"""Check the differential identity used in the adsorption-potential reference."""

import numpy
import pytest

from pygaps.modelling import model_from_dict


@pytest.mark.modelling
@pytest.mark.parametrize(
    'name, parameters',
    [
        ('Henry', {'K': 2.0}),
        ('Langmuir', {'K': 0.5, 'n_m': 3.0}),
        ('DSLangmuir', {'K1': 0.5, 'n_m1': 3.0, 'K2': 0.1, 'n_m2': 2.0}),
        ('TSLangmuir', {'K1': 0.5, 'n_m1': 3.0, 'K2': 0.1, 'n_m2': 2.0, 'K3': 0.2, 'n_m3': 1.0}),
        ('Toth', {'K': 0.5, 'n_m': 3.0, 't': 0.8}),
        ('DSToth', {'K1': 0.5, 'n_m1': 3.0, 't1': 0.8, 'K2': 0.1, 'n_m2': 2.0, 't2': 1.2}),
        ('ChemiPhysisorption', {'K1': 0.5, 'n_m1': 3.0, 't1': 0.8, 'K2': 0.1, 'n_m2': 2.0, 'Ea': 1000}),
        ('Freundlich', {'K': 2.0, 'm': 1.5}),
    ],
)
def test_toth_correction_matches_loading_derivative(name, parameters):
    model = model_from_dict({'name': name, 'parameters': parameters})
    for pressure in (0.1, 1.0, 5.0):
        step = pressure * 1e-5
        derivative = (model.loading(pressure + step) - model.loading(pressure - step)) / (2 * step)
        expected = model.loading(pressure) / (pressure * derivative) - 1
        numpy.testing.assert_allclose(model.toth_correction(pressure), expected, rtol=1e-6, atol=1e-8)
