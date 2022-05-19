import pytest
from matplotlib.testing.decorators import cleanup
<<<<<<< HEAD
from numpy import average
from numpy import isclose
=======
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533
from numpy import linspace

import pygaps.characterisation.whittaker as we
import pygaps.parsing as pgp
import pygaps.modelling as pgm
import pygaps.utilities.exceptions as pgEx

from .conftest import DATA_WHITTAKER
from .conftest import DATA_WHITTAKER_PATH

<<<<<<< HEAD

=======
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533
loading = linspace(0.1, 20, 100)


@pytest.mark.characterisation
class TestWhittakerEnthalpy():
<<<<<<< HEAD

    def test_whittaker_checks(self):
        filepath = DATA_WHITTAKER_PATH / DATA_WHITTAKER['example']
=======
    def test_whittaker_checks(self):
        filepath = DATA_WHITTAKER_PATH / DATA_WHITTAKER['example1']['file']
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533
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
<<<<<<< HEAD
            we.whittaker(model_isotherms[0])

        with pytest.raises(pgEx.CalculationError):
            we.whittaker(model_isotherms[1])
=======
            we.whittaker_enthalpy(model_isotherms[0], loading)

        with pytest.raises(pgEx.CalculationError):
            we.whittaker_enthalpy(model_isotherms[1], loading)
>>>>>>> f838bc8a8b84543e587533183c53505a8083f533

    def test_whittaker(self):
        pass

    @cleanup
    def test_whittaker_output(self):
        pass
