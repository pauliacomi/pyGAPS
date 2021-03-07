"""Test CoolProp interaction."""

import pygaps
import pygaps.utilities.exceptions as pgEx


class TestCoolProp():
    """Test CoolProp interaction."""
    def test_backend_change(self):
        """Test if backend can change."""
        previous_backend = pygaps.thermodynamic_backend()
        pygaps.backend_use_refprop()
        assert previous_backend != pygaps.thermodynamic_backend()
        pygaps.backend_use_coolprop()
        assert previous_backend == pygaps.thermodynamic_backend()

    def test_backend_names_coolprop(self):
        """Test if CoolProp can be called for database adsorbates."""
        for adsorbate in pygaps.ADSORBATE_LIST:
            try:
                adsorbate.backend.molar_mass()
            except pgEx.ParameterError:
                pass

    def test_backend_names_refprop(self):
        """Test if RERFPROP can be called for database adsorbates."""
        import CoolProp
        version = CoolProp.CoolProp.get_global_param_string("REFPROP_version")
        if version == 'n/a':
            pass
        else:
            pygaps.backend_use_refprop()
            for adsorbate in pygaps.ADSORBATE_LIST:
                try:
                    adsorbate.backend.molar_mass()
                except pgEx.ParameterError:
                    pass
                except ValueError:
                    pass
            pygaps.backend_use_coolprop()
