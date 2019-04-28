"""Test CoolProp interaction."""

import CoolProp

import pygaps


class TestCoolProp():
    """Test CoolProp interaction."""

    def test_backend_change(self):
        """Test if backend can change."""
        previous_backend = pygaps.COOLPROP_BACKEND
        pygaps.backend_use_refprop()
        assert previous_backend != pygaps.COOLPROP_BACKEND
        pygaps.backend_use_coolprop()
        assert previous_backend == pygaps.COOLPROP_BACKEND

    def test_backend_names_coolprop(self):
        """Test if CoolProp can be called for database adsorbents."""
        for adsorbate in pygaps.ADSORBATE_LIST:
            try:
                adsorbate.backend.molar_mass()
            except pygaps.utilities.exceptions.ParameterError:
                pass

    def test_backend_names_refprop(self):
        """Test if RERFPROP can be called for database adsorbents."""
        version = CoolProp.CoolProp.get_global_param_string("REFPROP_version")
        if version == 'n/a':
            pass
        else:
            pygaps.backend_use_refprop()
            for adsorbate in pygaps.ADSORBATE_LIST:
                try:
                    adsorbate.backend.molar_mass()
                except pygaps.utilities.exceptions.ParameterError:
                    pass
            pygaps.backend_use_coolprop()
