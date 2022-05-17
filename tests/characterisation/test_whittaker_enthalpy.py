import pytest
from matplotlib.testing.decorators import cleanup
from numpy import average
from numpy import isclose
from numpy import linspace

import pygaps.characterisation.whittaker as we
import pygaps.parsing as pgp
import pygaps.modelling as pgm
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH


loading = linspace(0.1, 20, 100)


@pytest.mark.characterisation
class TestWhittakerEnthalpy():

    def test_whittaker_checks(self):
        filepath = DATA_WHITTAKER_PATH / DATA_WHITTAKER['example']
        isotherm = pgp.isotherm_from_aif(filepath)

        model_isotherms = []
        for model in ['Henry', 'Langmuir', 'Toth']:
            isotherm.convert(
                pressure_unit='kPa',
                loading_unit='mol',
                material_unit='kg',
            )
            model_isotherm = pgm.model_iso(
                isotherm,
                branch='ads',
                model=model,
                verbose=True,
            )
            model_isotherms.append(model_isotherm)

        with pytest.raises(pgEx.ParameterError):
            we.whittaker(model_isotherms[0])

        with pytest.raises(pgEx.CalculationError):
            we.whittaker(model_isotherms[1])

    def test_whittaker(self):
        pass

    @cleanup
    def test_whittaker_output(self):
        pass
