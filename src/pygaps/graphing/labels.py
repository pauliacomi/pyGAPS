"""Utilities for creating various axis labels."""

from pygaps import logger
from pygaps.utilities.string_utilities import convert_chemformula
from pygaps.utilities.string_utilities import convert_unit_ltx


def label_units_iso(iso, key: str):
    """Build an axis label for pressure/loading/other starting from an isotherm."""
    unit_params = {
        "pressure_mode": iso.pressure_mode,
        "pressure_unit": iso.pressure_unit,
        "loading_basis": iso.loading_basis,
        "loading_unit": iso.loading_unit,
        "material_basis": iso.material_basis,
        "material_unit": iso.material_unit,
    }
    return label_units_dict(key, unit_params)


def label_units_dict(key: str, unit_params: dict):
    """Build an axis label for pressure/loading/other."""
    if key == "pressure":
        if unit_params['pressure_mode'] == "absolute":
            text = f"Pressure [${unit_params['pressure_unit']}$]"
        elif unit_params['pressure_mode'] == "relative":
            text = "Pressure [$p/p^0$]"
        elif unit_params['pressure_mode'] == "relative%":
            text = "Pressure [%$p/p^0$]"
    elif key == 'loading':
        if unit_params['loading_basis'] == "percent":
            text = f"Loading [${unit_params['material_basis']}$%]"
        elif unit_params['loading_basis'] == "fraction":
            text = fr"Loading [${unit_params['material_basis']}\/fraction$]"
        else:
            text = fr"Loading [${convert_unit_ltx(unit_params['loading_unit'])}\/{convert_unit_ltx(unit_params['material_unit'], True)}$]"
    elif key == "enthalpy":
        text = r"$\Delta_{ads}h$ $(-kJ\/mol^{-1})$"
    else:
        text = key
    return text


def label_lgd(isotherm, lbl_components: list, branch: str = None, key_def: str = None):
    """Build a legend label."""

    if not lbl_components:
        lbl_components = ['material', 'adsorbate', 'temperature', 'key']

    text = []
    for selected in lbl_components:
        if selected == 'branch':
            text.append(branch)
        elif selected == 'adsorbate':
            text.append(convert_chemformula(isotherm.adsorbate))
        elif selected == 'temperature':
            text.append(f"{isotherm.temperature} {isotherm.temperature_unit}")
        elif selected == 'type':
            isotype = "points"
            if hasattr(isotherm, 'model'):
                isotype = "model"
            text.append(isotype)
        elif selected == 'key':
            text.append(key_def)
        else:
            val = getattr(isotherm, selected, None)
            if not val:
                val = isotherm.properties.get(selected, None)
            if not val:
                logger.warning(
                    f"Isotherm {isotherm.__repr__()} does not have an {selected} attribute."
                )
                continue
            text.append(str(val))

    return " ".join(text)
