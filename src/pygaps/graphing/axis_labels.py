"""Utilities for creating various axis labels."""

import logging

logger = logging.getLogger('pygaps')

from ..utilities.string_utilities import convert_chemformula
from ..utilities.string_utilities import convert_unit_ltx


def label_axis_text_pl(iso_params, key):
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


def label_lgd(isotherm, lbl_components, current_branch, branch_def, key_def):
    """Build a legend label."""
    if branch_def == 'all-nol' and current_branch == 'des':
        return ''

    if lbl_components is None:
        lbl_components = ['material', 'adsorbate', 'branch']

    text = []
    for selected in lbl_components:
        if selected == 'branch':
            text.append(current_branch)
        elif selected == 'key':
            text.append(key_def)
        else:
            val = getattr(isotherm, selected, None)
            if val:
                if selected == 'adsorbate':
                    text.append(convert_chemformula(isotherm.adsorbate))
                elif selected == 'temperature':
                    text.append(f"{isotherm.temperature} K")
                else:
                    text.append(str(val))
            else:
                logger.warning(
                    f"Isotherm {isotherm} does not have an {selected} attribute."
                )

    return " ".join(text)
