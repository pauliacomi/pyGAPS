"""Utilities for creating various axis labels."""

import logging

logger = logging.getLogger('pygaps')

from ..utilities.string_utilities import convert_chemformula
from ..utilities.string_utilities import convert_unit_ltx


def label_axis_title(key, iso_params):
    """Build an axis label for pressure/loading/other."""
    if key == "pressure":
        if iso_params['pressure_mode'] == "absolute":
            text = f"Pressure [${iso_params['pressure_unit']}$]"
        elif iso_params['pressure_mode'] == "relative":
            text = "Pressure [$p/p^0$]"
        elif iso_params['pressure_mode'] == "relative%":
            text = "Pressure [%$p/p^0$]"
    elif key == 'loading':
        if iso_params['loading_basis'] == "percent":
            text = f"Loading [${iso_params['material_basis']}$%]"
        elif iso_params['loading_basis'] == "fraction":
            text = fr"Loading [${iso_params['material_basis']}\/fraction$]"
        else:
            text = fr"Loading [${convert_unit_ltx(iso_params['loading_unit'])}\/{convert_unit_ltx(iso_params['material_unit'], True)}$]"
    elif key == "enthalpy":
        text = r"$\Delta_{ads}h$ $(-kJ\/mol^{-1})$"
    else:
        text = key
    return text


def label_lgd(isotherm, lbl_components, branch, key_def):
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
                logger.warning(f"Isotherm {isotherm} does not have an {selected} attribute.")
                continue
            text.append(str(val))

    return " ".join(text)
