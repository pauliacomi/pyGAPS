"""
An AIF (adsorption information file) parsing implementation.

Format developed in this publication:

Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

"""

import json
import os
import pathlib
from typing import Optional
from typing import cast

import pandas
from adsorption_file_parser.utils.unit_parsing import parse_loading_string
from adsorption_file_parser.utils.unit_parsing import parse_pressure_string
from adsorption_file_parser.utils.unit_parsing import parse_temperature_string
from gemmi import cif

import pygaps
from pygaps import logger
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.modelling import model_from_dict
from pygaps.parsing import _PARSER_PRECISION
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import ParsingError
from pygaps.utilities.pandas_utilities import try_numeric
from pygaps.utilities.string_utilities import cast_string

# AIF versions

_AIF_VERSION_LEGACY = "d546195"
_AIF_VERSION_v1p0 = "v1.0"
_AIF_VERSION_LATEST = _AIF_VERSION_v1p0

# Provenance marker written to `_audit_creation_method` for every file pyGAPS
# writes, and the exact value `isotherm_from_aif` checks for to recognize a
# pyGAPS-authored round-trip (`created_with_pygaps`). Kept as a single
# constant so the write and read sides can't drift apart.
_PYGAPS_CREATION_METHOD = "pyGAPS export"


def _pygaps_software_marker():
    """Provenance string written to `_audit_creation_software`.

    Computed with the same logic on both the write and read side (see
    `isotherm_to_aif`/`isotherm_from_aif`) so a pyGAPS round-trip recognizes
    its own marker and doesn't leak it back as a generic `audit_creation_software`
    property.
    """
    return 'pyGAPS' + (f" {pygaps.__version__}" if hasattr(pygaps, "__version__") else "")


# --- Metadata aliases ---------------------------------------------------
#
# Each known AIF schema version gets ONE complete, self-contained table
# (`_METADATA_ALIASES_xxx`), mapping `pygaps_key -> {'tag': aif_tag, 'type': type}`.
# This single table drives both directions, derived once below via
# `_metadata_write_aliases`/`_metadata_read_aliases`.
#
# Writing targets one version, so `isotherm_to_aif` looks up that
# version's derived write table via `_SCHEMA_REGISTRY[version]['metadata_write']`
# - a single dict access, no merging step at lookup time.
#
# Adding a future AIF version is then a matter of adding one more
# `_METADATA_ALIASES_*` table plus one more `_SCHEMA_REGISTRY` entry.

# NOTE: '_audit_aif_version' is intentionally absent from every alias table;
# it is consumed separately (as the schema version check) before any alias
# table is used, so it is never treated as generic metadata.

# `audit_creation_method`/`audit_creation_software` are recognized on read (to
# detect/preserve a foreign value) but must never be written through the
# generic write loop: the writer always sets both tags explicitly to the
# pyGAPS provenance marker (see `_PYGAPS_CREATION_METHOD`/`_pygaps_software_marker`),
# and a foreign value carried over from another file is redirected to a
# `_pygaps_*`-namespaced key instead so it can't clobber that marker (see
# `_write_scalar_metadata`).
_METADATA_WRITE_EXCLUDE = {'audit_creation_method', 'audit_creation_software'}

_METADATA_ALIASES_LEGACY = {
    # audit
    'audit_creation_method': {'tag': '_audit_creation_method', 'type': str},
    # exptl
    'experimental_operator': {'tag': '_exptl_operator', 'type': str},
    'experimental_date': {'tag': '_exptl_date', 'type': str},
    'experimental_instrument': {'tag': '_exptl_instrument', 'type': str},
    'adsorbate': {'tag': '_exptl_adsorptive', 'type': str},
    # 'adsorbate_name' would collide with the adsorbate 'name' on read
    'adsorbate_full_name': {'tag': '_exptl_adsorptive_name', 'type': str},
    'temperature': {'tag': '_exptl_temperature', 'type': float},
    'experimental_method': {'tag': '_exptl_method', 'type': str},
    'experimental_isotherm_type': {'tag': '_exptl_isotherm_type', 'type': str},
    'experimental_p0': {'tag': '_exptl_p0', 'type': str},
    'experimental_digitizer': {'tag': '_exptl_digitizer', 'type': str},
    # adsorbent
    'material': {'tag': '_adsnt_material_id', 'type': str},
    'material_info': {'tag': '_adsnt_info', 'type': str},
    'material_batch': {'tag': '_adsnt_sample_id', 'type': str},
    'material_hashkey': {'tag': '_adsnt_hashkey', 'type': str},
    'material_mass': {'tag': '_adsnt_sample_mass', 'type': float},
    'material_density': {'tag': '_adsnt_sample_density', 'type': float},
    'material_activation_summary': {'tag': '_adsnt_degas_summary', 'type': str},
    'material_activation_temperature': {'tag': '_adsnt_degas_temperature', 'type': float},
    'material_activation_time': {'tag': '_adsnt_degas_time', 'type': str},
    # simulation
    'simulation_code': {'tag': '_simltn_code', 'type': str},
    'simulation_date': {'tag': '_simltn_date', 'type': str},
    'simulation_forcefield_adsorbent': {'tag': '_simltn_forcefield_adsorbent', 'type': str},
    'simulation_forcefield_adsorptive': {'tag': '_simltn_forcefield_adsorptive', 'type': str},
    'simulation_input_files': {'tag': '_simltn_input_files', 'type': str},
    'simulation_lot': {'tag': '_simltn_lot', 'type': str},
    'simulation_sampling': {'tag': '_simltn_sampling', 'type': str},
    'simulation_size': {'tag': '_simltn_size', 'type': str},
    # citation
    'citation_doi': {'tag': '_citation_doi', 'type': str},
    'citation_source': {'tag': '_citation_source', 'type': str},
    # units
    'units_pressure': {'tag': '_units_pressure', 'type': str},
    'units_temperature': {'tag': '_units_temperature', 'type': str},
    'units_mass': {'tag': '_units_mass', 'type': str},
    'units_sorbed_amount': {'tag': '_units_loading', 'type': str},
    'units_density': {'tag': '_units_density', 'type': str},
    'units_time': {'tag': '_units_time', 'type': str},
    'units_enthalpy': {'tag': '_units_enthalpy', 'type': str},
    'units_composition_type': {'tag': '_units_composition_type', 'type': str},
}

# Tags used by pre-release AIF files (before d546195), only ever read.
_METADATA_READ_PRERELEASE = {
    '_sample_material_id': {'key': 'material', 'type': str},
    '_sample_id': {'key': 'material_batch', 'type': str},
    '_exptl_sample_mass': {'key': 'material_mass', 'type': float},
    '_exptl_activation_temperature': {'key': 'material_activation_temperature', 'type': float},
}


_METADATA_ALIASES_v1p0p0 = {
    # audit
    'audit_author': {'tag': '_audit_author', 'type': str},
    'audit_creation_date': {'tag': '_audit_creation_date', 'type': str},
    'audit_creation_method': {'tag': '_audit_creation_method', 'type': str},
    'audit_creation_software': {'tag': '_audit_creation_software', 'type': str},
    # experimental
    'experimental_operator': {'tag': '_exptl_operator', 'type': str},
    'experimental_date': {'tag': '_exptl_date', 'type': str},
    'experimental_instrument': {'tag': '_exptl_instrument', 'type': str},
    'temperature': {'tag': '_exptl_temperature', 'type': float},
    'experimental_method': {'tag': '_exptl_method', 'type': str},
    'experimental_isotherm_type': {'tag': '_exptl_isotherm_type', 'type': str},
    # adsorbent
    'material': {'tag': '_adsnt_material_name', 'type': str},
    'material_info': {'tag': '_adsnt_info', 'type': str},
    'material_batch': {'tag': '_adsnt_sample_name', 'type': str},
    'material_hashkey': {'tag': '_adsnt_hashkey', 'type': str},
    'material_structure_csd_refcode': {'tag': '_adsnt_structure_csd_refcode', 'type': str},
    'material_structure_topology': {'tag': '_adsnt_structure_topology', 'type': str},
    'material_structure_smiles': {'tag': '_adsnt_structure_smiles', 'type': str},
    'material_composition': {'tag': '_adsnt_composition', 'type': str},
    'material_molar_mass': {'tag': '_adsnt_molar_mass', 'type': float},
    'material_synthesis': {'tag': '_adsnt_synthesis', 'type': str},
    'material_mass': {'tag': '_adsnt_sample_mass', 'type': float},
    'material_density': {'tag': '_adsnt_sample_density', 'type': float},
    'material_activation_summary': {'tag': '_adsnt_degas_summary', 'type': str},
    'material_activation_temperature': {'tag': '_adsnt_degas_temperature', 'type': float},
    'material_activation_time': {'tag': '_adsnt_degas_time', 'type': float},
    # adsorptive
    'adsorbate': {'tag': '_adsorptive_name', 'type': str},
    'adsorbate_info': {'tag': '_adsorptive_info', 'type': str},
    'adsorbate_inchi': {'tag': '_adsorptive_inchi', 'type': str},
    'adsorbate_cas': {'tag': '_adsorptive_cas', 'type': str},
    'adsorbate_smiles': {'tag': '_adsorptive_smiles', 'type': str},
    'adsorbate_formula': {'tag': '_adsorptive_formula', 'type': str},
    'adsorbate_molecular_weight': {'tag': '_adsorptive_molecular_weight', 'type': float},
    'adsorbate_kinetic_diameter': {'tag': '_adsorptive_kinetic_diameter', 'type': float},
    'adsorbate_quadrupole_moment': {'tag': '_adsorptive_quadrupole_moment', 'type': float},
    # `_adsorptive_component_*` is a loop, kept as raw rows by `_read_other_loop`.
    # simulation
    'simulation_code': {'tag': '_simltn_code', 'type': str},
    'simulation_date': {'tag': '_simltn_date', 'type': str},
    'simulation_size': {'tag': '_simltn_size', 'type': str},
    'simulation_forcefield_adsorptive': {'tag': '_simltn_forcefield_adsorptive', 'type': str},
    'simulation_forcefield_adsorbent': {'tag': '_simltn_forcefield_adsorbent', 'type': str},
    'simulation_input_files': {'tag': '_simltn_input_files', 'type': str},
    'simulation_sampling': {'tag': '_simltn_sampling', 'type': str},
    'simulation_lot': {'tag': '_simltn_lot', 'type': str},
    # digitization
    'digitization_author': {'tag': '_digitization_author', 'type': str},
    'digitization_date': {'tag': '_digitization_date', 'type': str},
    'digitization_method': {'tag': '_digitization_method', 'type': str},
    'digitization_software': {'tag': '_digitization_software', 'type': str},
    'digitization_notes': {'tag': '_digitization_notes', 'type': str},
    # citation
    'citation_doi': {'tag': '_citation_doi', 'type': str},
    'citation_source': {'tag': '_citation_source', 'type': str},
    'citation_figure': {'tag': '_citation_figure', 'type': str},
    'citation_page': {'tag': '_citation_page', 'type': str},
    'citation_url': {'tag': '_citation_url', 'type': str},
    # analysis
    'analysis_method': {'tag': '_analysis_method', 'type': str},
    'analysis_bet_area': {'tag': '_analysis_bet_area', 'type': float},
    'analysis_bet_c_constant': {'tag': '_analysis_bet_c_constant', 'type': float},
    'analysis_bet_pressure_range_min': {'tag': '_analysis_bet_pressure_range_min', 'type': float},
    'analysis_bet_pressure_range_max': {'tag': '_analysis_bet_pressure_range_max', 'type': float},
    'analysis_langmuir_area': {'tag': '_analysis_langmuir_area', 'type': float},
    'analysis_langmuir_pressure_range_min': {'tag': '_analysis_langmuir_pressure_range_min', 'type': float},
    'analysis_langmuir_pressure_range_max': {'tag': '_analysis_langmuir_pressure_range_max', 'type': float},
    'analysis_total_pore_volume': {'tag': '_analysis_total_pore_volume', 'type': float},
    'analysis_total_pore_volume_pressure': {'tag': '_analysis_total_pore_volume_pressure', 'type': float},
    'analysis_psd_method_name': {'tag': '_analysis_psd_method_name', 'type': str},
    'analysis_psd_method_branch': {'tag': '_analysis_psd_method_branch', 'type': str},
    'analysis_psd_method_geometry': {'tag': '_analysis_psd_method_geometry', 'type': str},
    'analysis_psd_method_details': {'tag': '_analysis_psd_method_details', 'type': str},
    # `_analysis_psd_*`/`_analysis_fit_*`/`_analysis_fit_param_*` are loops, see `_LOOP_CATEGORIES_v1p0p0`.
    # units
    'units_temperature': {'tag': '_units_temperature', 'type': str},
    'units_pressure': {'tag': '_units_pressure', 'type': str},
    'units_mass': {'tag': '_units_mass', 'type': str},
    'units_sorbed_amount': {'tag': '_units_sorbed_amount', 'type': str},
    'units_density': {'tag': '_units_density', 'type': str},
    'units_time': {'tag': '_units_time', 'type': str},
    'units_molecular_weight': {'tag': '_units_molecular_weight', 'type': str},
    'units_enthalpy': {'tag': '_units_enthalpy', 'type': str},
    'units_composition_type': {'tag': '_units_composition_type', 'type': str},
    'units_concentration': {'tag': '_units_concentration', 'type': str},
    'units_surface_area': {'tag': '_units_surface_area', 'type': str},
    'units_pore_volume': {'tag': '_units_pore_volume', 'type': str},
    'units_pore_size': {'tag': '_units_pore_size', 'type': str},
    'units_kinetic_diameter': {'tag': '_units_kinetic_diameter', 'type': str},
    'units_quadrupole_moment': {'tag': '_units_quadrupole_moment', 'type': str},
}


# --- Data loop columns --------------------------------------------------
#
# `pygaps_column -> aif_suffix`, where the full AIF tag is
# `_adsorp_<suffix>` or `_desorp_<suffix>`.

_LOOP_COLUMNS_LEGACY = {
    'pressure': 'pressure',
    'fugacity': 'fugacity',
    'pressure_saturation': 'p0',
    'loading': 'amount',
    'loading_excess': 'amount_excess',
    'loading_absolute': 'amount_absolute',
    'loading_net': 'amount_net',
    'henry': 'henry',
    'enthalpy': 'enthalpy',
    'molefraction': 'molefraction',
    'selectivity': 'selectivity',
}

_LOOP_COLUMNS_v1p0p0 = {
    'index': 'index',
    'pressure': 'pressure',
    'fugacity': 'fugacity',
    'pressure_saturation': 'p0',
    'loading': 'amount',
    'loading_excess': 'amount_excess',
    'loading_absolute': 'amount_absolute',
    'loading_net': 'amount_net',
    'enthalpy': 'enthalpy_differential',
    'enthalpy_integral': 'enthalpy_integral',
}

# Numbered per-component columns, e.g. `_adsorp_amount_component_2`.
_LOOP_COLUMN_PREFIXES_v1p0p0 = {
    'fugacity_component_': 'fugacity_component_',
    'composition_component_': 'composition_component_',
    'loading_component_': 'amount_component_',
}

# Any data name ending with these is the uncertainty of the base data name.
_UNCERTAINTY_SUFFIXES = ('_uncertainty', '_su')

# Non-isotherm AIF loops, kept as a list of row dicts under the category name.
# Longest first, so e.g. `analysis_fit_param` wins over `analysis_fit`.
_LOOP_CATEGORIES_v1p0p0 = (
    'adsorptive_component',
    'adsorp_transient',
    'desorp_transient',
    'analysis_fit_param',
    'analysis_fit',
    'analysis_psd',
)

# Row lists without an AIF category are written as `_pygaps_<name>.<column>` loops.
_PYGAPS_LOOP_PREFIX = '_pygaps_'
_PYGAPS_LOOP_SEPARATOR = '.'

# --- Unit dependencies --------------------------------------------------
#
# AIF requires a `_units_*` tag whenever a dimensional value is present
# (`dependentRequired` in the AIF dictionary). If the isotherm does not carry
# the unit (e.g. as a `units_mass` property read from an AIF), the default
# below is written. Data loop columns are matched by their suffix.

_UNIT_DEPENDENCIES = {
    '_adsnt_sample_mass': ('_units_mass',),
    '_adsnt_sample_density': ('_units_density',),
    '_adsnt_molar_mass': ('_units_molecular_weight',),
    '_adsnt_degas_time': ('_units_time',),
    '_adsorptive_molecular_weight': ('_units_molecular_weight',),
    '_adsorptive_kinetic_diameter': ('_units_kinetic_diameter',),
    '_adsorptive_quadrupole_moment': ('_units_quadrupole_moment',),
    '_analysis_bet_area': ('_units_surface_area',),
    '_analysis_langmuir_area': ('_units_surface_area',),
    '_analysis_total_pore_volume': ('_units_pore_volume',),
    '_analysis_psd_dimension': ('_units_pore_size',),
    '_analysis_psd_dv_dd': ('_units_pore_volume', '_units_pore_size'),
}
_UNIT_DEPENDENCIES_LOOP_SUFFIX = {
    'enthalpy': ('_units_enthalpy',),
    'enthalpy_differential': ('_units_enthalpy',),
    'enthalpy_integral': ('_units_enthalpy',),
}
_UNIT_DEFAULTS = {
    '_units_mass': 'g',
    '_units_density': 'g/cm3',
    '_units_molecular_weight': 'g/mol',
    '_units_time': 'h',
    '_units_enthalpy': 'kJ/mol',
    '_units_surface_area': 'm2/g',
    '_units_pore_volume': 'cm3/g',
    '_units_pore_size': 'nm',
    '_units_kinetic_diameter': 'nm',
}


def _metadata_write_aliases(table):
    """Derive the `pygaps_key -> aif_tag` write table from a unified alias table.

    Keys in `_METADATA_WRITE_EXCLUDE` are dropped: their tags are always set
    explicitly elsewhere (the pyGAPS provenance markers), so they must never
    be reachable through the generic write loop.
    """
    return {key: info['tag'] for key, info in table.items() if key not in _METADATA_WRITE_EXCLUDE}


def _metadata_read_aliases(table, fallback=None):
    """Derive the `aif_tag -> {'key': pygaps_key, 'type': type}` read table from a unified alias table.

    `fallback`, if given, is an already derived read table (e.g. from an older
    version) whose tags are recognized unless redefined by `table`.
    """
    aliases = dict(fallback or {})
    aliases.update({info['tag']: {'key': key, 'type': info['type']} for key, info in table.items()})
    return aliases


def _loop_read_aliases(table, fallback=None):
    """Derive the `aif_suffix -> pygaps_column` read table for data loops."""
    aliases = dict(fallback or {})
    aliases.update({suffix: key for key, suffix in table.items()})
    return aliases


_METADATA_READ_LEGACY = _metadata_read_aliases(_METADATA_ALIASES_LEGACY, _METADATA_READ_PRERELEASE)
_LOOP_READ_LEGACY = _loop_read_aliases(_LOOP_COLUMNS_LEGACY)

_SCHEMA_REGISTRY = {
    _AIF_VERSION_LEGACY: {
        'name': 'legacy d546195',
        'metadata_write': _metadata_write_aliases(_METADATA_ALIASES_LEGACY),
        'metadata_read': _METADATA_READ_LEGACY,
        'loop_write': dict(_LOOP_COLUMNS_LEGACY),
        'loop_read': _LOOP_READ_LEGACY,
        'loop_read_prefixes': {},
        'loop_categories': (),
        'required': ('_exptl_adsorptive', '_exptl_temperature', '_adsnt_material_id'),
    },
    _AIF_VERSION_v1p0: {
        'name': 'AIF v1.0',
        'metadata_write': _metadata_write_aliases(_METADATA_ALIASES_v1p0p0),
        # older tags are still recognized when reading v1.0 (or unversioned) files
        'metadata_read': _metadata_read_aliases(_METADATA_ALIASES_v1p0p0, _METADATA_READ_LEGACY),
        'loop_write': dict(_LOOP_COLUMNS_v1p0p0),
        'loop_read': _loop_read_aliases(_LOOP_COLUMNS_v1p0p0, _LOOP_READ_LEGACY),
        'loop_read_prefixes': {suffix: key for key, suffix in _LOOP_COLUMN_PREFIXES_v1p0p0.items()},
        'loop_categories': _LOOP_CATEGORIES_v1p0p0,
        'required': ('_adsnt_material_name', '_exptl_method'),
    },
}


def _unquote(value):
    """Return the text of a raw STAR value, or None for null (`?`/`.`) values."""
    if value is None or cif.is_null(value):
        return None
    return cif.as_string(value)


def _quote(value):
    return cif.quote(str(value))


def _format_number(value, is_float):
    """Format a number to `_PARSER_PRECISION` significant figures, keeping floats recognizable."""
    if not is_float:
        return str(value)
    text = f"{float(value):.{_PARSER_PRECISION}g}"
    if text.lstrip('-').isdigit():
        text += '.0'
    return text


def _json_default(value):
    """Serialize numpy scalars and other non-JSON values."""
    if hasattr(value, 'item'):
        return value.item()
    return str(value)


def _to_text(value):
    """Return the AIF text of a property value; containers are JSON-encoded."""
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, default=_json_default)
    return value


def _from_text(value):
    """Cast AIF text back to a value, decoding JSON containers where possible."""
    if value[:1] in ('[', '{'):
        try:
            return json.loads(value)
        except ValueError:
            pass
    try:
        return cast_string(value)
    except (ValueError, SyntaxError, ParsingError):
        return value


def _cast_value(value, value_type):
    return value_type(value)


def _normalize_version(value):
    """Return the registered version name, accepting e.g. `1.0` for `v1.0`."""
    value = _unquote(value)
    if value and value not in _SCHEMA_REGISTRY and f"v{value}" in _SCHEMA_REGISTRY:
        return f"v{value}"
    return value


def _write_text_pair(block, key, value):
    if value is not None:
        block.set_pair(key, _quote(_to_text(value)))


def _parse_subsection(raw_dict, subsection):
    """Rebuild the material dictionary from normalized scalar/raw keys."""
    if subsection not in raw_dict:
        return raw_dict

    subdict = {'name': raw_dict.pop(subsection)}
    for key in list(raw_dict):
        # e.g. `material_unit` is an isotherm unit, not a material property
        if key in BaseIsotherm._unit_params:
            continue
        if key.startswith(f'{subsection}_'):
            subdict[key.replace(f'{subsection}_', '', 1)] = raw_dict.pop(key)

    if len(subdict) > 1:
        raw_dict[subsection] = subdict
    else:
        raw_dict[subsection] = subdict['name']

    return raw_dict


def _build_adsorbate(value):
    """Create an Adsorbate carrying the AIF adsorptive details.

    If the name resolves to a known adsorbate, its properties (e.g. the
    thermodynamic backend name) are kept and extended with the AIF details.
    A new instance is returned so the global adsorbate list is not modified.
    """
    if not isinstance(value, dict):
        return value

    details = dict(value)
    name = details.pop('name')
    try:
        known = Adsorbate.find(name)
    except ParameterError:
        logger.warning(
            f"Adsorbate '{name}' is not in internal list "
            "(or name cannot be resolved to an existing one). "
            "Thermodynamic backend disabled for this gas/vapour."
        )
        return Adsorbate(name, **details)

    return Adsorbate(known.name, alias=known.alias, **{**known.properties, **details})


def _read_loop_column(name, schema):
    """Map an AIF data loop column (without `_adsorp_`/`_desorp_`) to a pyGAPS column."""
    for ending in _UNCERTAINTY_SUFFIXES:
        if name.endswith(ending) and len(name) > len(ending):
            return _read_loop_column(name[: -len(ending)], schema) + ending

    if name in schema['loop_read']:
        return schema['loop_read'][name]

    for aif_prefix, key_prefix in schema['loop_read_prefixes'].items():
        if name.startswith(aif_prefix):
            return key_prefix + name[len(aif_prefix) :]

    return name


def _read_loop_rows(block, loop):
    """Return the unquoted loop values as a list of rows."""
    return [[_unquote(value) for value in row] for row in block.find(loop.tags)]


def _read_data_loop(block, loop, prefix, branch, schema):
    """Read an adsorption/desorption loop into a DataFrame."""
    columns = [_read_loop_column(tag.lower()[len(prefix) :], schema) for tag in loop.tags]

    missing = [f"{prefix}{suffix}" for column, suffix in (('pressure', 'pressure'), ('loading', 'amount')) if column not in columns]
    if missing:
        raise ParsingError(
            f"The AIF {'adsorption' if branch == 0 else 'desorption'} data loop is missing "
            f"the required column(s) {', '.join(missing)} (found: {', '.join(loop.tags)}). "
            "pyGAPS needs both a pressure and a total amount column: isotherms given only as "
            "fugacity, excess/absolute/net amount or per-component amount are not supported."
        )

    data_df = pandas.DataFrame(_read_loop_rows(block, loop), columns=columns).apply(try_numeric)

    # v1.0 onwards: points are ordered by the index column
    if 'index' in data_df.columns:
        data_df = data_df.sort_values(by='index', ignore_index=True).drop(columns='index')

    data_df['branch'] = branch
    return data_df


def _loop_category(tags):
    """Return the `_category_` prefix of a set of loop tags and whether it is a pyGAPS loop.

    Known AIF categories are matched first, then pyGAPS `_pygaps_<name>.<column>`
    loops, then the common prefix of all tags.
    """
    ltags = [tag.lower() for tag in tags]
    for category in _LOOP_CATEGORIES_v1p0p0:
        prefix = f"_{category}_"
        if all(tag.startswith(prefix) for tag in ltags):
            return prefix, False

    if all(tag.startswith(_PYGAPS_LOOP_PREFIX) and _PYGAPS_LOOP_SEPARATOR in tag for tag in tags):
        prefix = tags[0][: tags[0].index(_PYGAPS_LOOP_SEPARATOR) + 1]
        if all(tag.startswith(prefix) for tag in tags):
            return prefix, True

    prefix = os.path.commonprefix(ltags)
    if len(tags) == 1 or not prefix.endswith('_'):
        prefix = prefix[: prefix.rfind('_') + 1]
    return prefix, False


def _read_other_loop(block, loop):
    """Read any non-isotherm loop as a list of row dictionaries.

    Returns the property name to store the rows under and the rows themselves.
    """
    prefix, is_pygaps = _loop_category(loop.tags)
    if is_pygaps:
        # pyGAPS loops keep the exact property and column names
        name = prefix[len(_PYGAPS_LOOP_PREFIX) : -len(_PYGAPS_LOOP_SEPARATOR)]
        columns = [tag[len(prefix) :] for tag in loop.tags]
    else:
        name = prefix.strip('_')
        columns = [tag.lower()[len(prefix) :] for tag in loop.tags]

    rows = [
        {column: (_from_text(value) if value is not None else None) for column, value in zip(columns, row)}
        for row in _read_loop_rows(block, loop)
    ]

    return name, rows


def _flatten_section(iso_dict, section="material"):
    """Flatten section metadata without losing plain names or mutating nested data."""
    section_dict = iso_dict.pop(section, None)
    if section_dict is None:
        return

    if isinstance(section_dict, dict):
        section_dict = section_dict.copy()
        name = section_dict.pop('name', None)
        if name is not None:
            iso_dict[section] = name
    else:
        iso_dict[section] = section_dict
        return

    for key, value in section_dict.items():
        iso_dict[f"{section}_{key}"] = value


def _write_metadata(block, iso_dict, write_aliases):
    """Write scalar metadata handled by the target AIF schema, then keep pyGAPS extras."""
    # 'audit_creation_method' is never mapped back onto `_audit_creation_method`:
    # that tag is always set to 'pyGAPS' by the writer to record true
    # provenance, so a value carried over from a foreign/previous file is kept
    # as a namespaced pyGAPS extra instead (see `created_with_pygaps` in
    # `isotherm_from_aif`).
    if 'audit_creation_method' in iso_dict:
        _write_text_pair(
            block,
            '_pygaps_audit_previous_creation_method',
            iso_dict.pop('audit_creation_method'),
        )

    # Same treatment for 'audit_creation_software' (see above) - never mapped
    # back onto `_audit_creation_software`, kept as a namespaced pyGAPS extra.
    if 'audit_creation_software' in iso_dict:
        _write_text_pair(
            block,
            '_pygaps_audit_previous_creation_software',
            iso_dict.pop('audit_creation_software'),
        )

    # Generic text-pair fields understood by the target schema version.
    for key, value in list(iso_dict.items()):
        if key in write_aliases:
            _write_text_pair(block, write_aliases[key], value)
            iso_dict.pop(key)

    # Whatever remains is pyGAPS-specific and kept in a namespaced section.
    for key in list(iso_dict):
        if key.startswith('_pygaps_'):
            value = iso_dict.pop(key)
            _write_text_pair(block, key, value)


def _write_units(block, isotherm, write_aliases):
    """Write units using the selected AIF schema and keep exact pyGAPS unit hints."""
    _write_text_pair(
        block,
        write_aliases['units_temperature'],
        isotherm.temperature_unit,
    )

    if isotherm.pressure_mode == 'absolute':
        pressure_units = isotherm.pressure_unit
    else:
        pressure_units = isotherm.pressure_mode
    _write_text_pair(block, write_aliases['units_pressure'], pressure_units)

    if isotherm.loading_basis == 'fraction':
        loading_units = f'fraction {isotherm.material_basis}'
    elif isotherm.loading_basis == 'percent':
        loading_units = f'% {isotherm.material_basis}'
    else:
        loading_units = f'{isotherm.loading_unit}/{isotherm.material_unit}'
    _write_text_pair(block, write_aliases['units_sorbed_amount'], loading_units)


def _loop_suffix_for_write(key, schema):
    """Map a pyGAPS data column to its AIF loop suffix for the chosen schema."""
    for ending in _UNCERTAINTY_SUFFIXES:
        if key.endswith(ending) and len(key) > len(ending):
            return _loop_suffix_for_write(key[: -len(ending)], schema) + ending

    if key in schema['loop_write']:
        return schema['loop_write'][key]

    for aif_prefix, pygaps_prefix in schema['loop_read_prefixes'].items():
        if key.startswith(pygaps_prefix):
            return aif_prefix + key[len(pygaps_prefix) :]

    return key


def _write_loop(block, prefix, dataframe, pressure_key, loading_key, other_keys, schema):
    """Write a point-isotherm branch using the selected version's loop aliases."""
    loop_data = {
        'pressure': dataframe[pressure_key],
        'loading': dataframe[loading_key],
    }
    loop_data.update({key: dataframe[key] for key in other_keys})

    # AIF v1.0 data loops use a point index; it is not part of pyGAPS' data.
    if 'index' in schema['loop_write'] and 'index' not in loop_data:
        loop_data = {'index': range(1, len(dataframe) + 1), **loop_data}

    tags = [_loop_suffix_for_write(key, schema) for key in loop_data]
    values = []
    for series in loop_data.values():
        series = pandas.Series(series)
        if pandas.api.types.is_numeric_dtype(series) and not pandas.api.types.is_bool_dtype(series):
            is_float = pandas.api.types.is_float_dtype(series)
            values.append(['?' if pandas.isna(value) else _format_number(value, is_float) for value in series])
        else:
            values.append(['?' if pandas.isna(value) else _quote(value) for value in series])

    loop = block.init_loop(prefix, tags)
    loop.set_all_values(values)


def _is_row_list(value):
    """Check whether a property is a list of row dictionaries (an AIF loop)."""
    return isinstance(value, list) and len(value) > 0 and all(isinstance(row, dict) for row in value)


def _write_rows_loop(block, name, rows, schema):
    """Write a list of row dicts as a loop; inverse of `_read_other_loop`."""
    if name.lower() in schema['loop_categories']:
        prefix = f"_{name.lower()}_"
    else:
        prefix = f"{_PYGAPS_LOOP_PREFIX}{name}{_PYGAPS_LOOP_SEPARATOR}"

    columns = list(dict.fromkeys(column for row in rows for column in row))
    values = [['?' if row.get(column) is None else _quote(_to_text(row[column])) for row in rows] for column in columns]

    loop = block.init_loop(prefix, [str(column) for column in columns])
    loop.set_all_values(values)


def _write_dependent_units(block, loop_tags, schema):
    """Write any `_units_*` tag required by the values present but not written yet.

    `loop_tags` are the tags of loops that will be written after the units.
    """
    present = {item.pair[0].lower() for item in block if item.pair is not None}

    needed = []
    for tag in list(present) + [tag.lower() for tag in loop_tags]:
        needed.extend(_UNIT_DEPENDENCIES.get(tag, ()))
        for prefix in ('_adsorp_', '_desorp_'):
            if tag.startswith(prefix):
                needed.extend(_UNIT_DEPENDENCIES_LOOP_SUFFIX.get(tag[len(prefix) :], ()))

    known_unit_tags = set(schema['metadata_write'].values())
    for unit_tag in dict.fromkeys(needed):
        if unit_tag in present or unit_tag not in known_unit_tags:
            continue
        default = _UNIT_DEFAULTS.get(unit_tag)
        if default is None:
            logger.warning(f"No unit known for {unit_tag}; the AIF will be missing this tag.")
            continue
        logger.info(f"No unit specified for {unit_tag}, written as the pyGAPS default '{default}'.")
        _write_text_pair(block, unit_tag, default)


def isotherm_to_aif(isotherm: BaseIsotherm, path: Optional[str] = None, version: str = _AIF_VERSION_LATEST) -> Optional[str]:
    """
    Convert isotherm into an AIF representation [#]_.

    If the path is specified, the isotherm is saved as a file,
    otherwise it is returned as a string.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm to be written to AIF.
    path : str, None
        Path to the file to be written.
    version : str
        Which AIF schema version to write. Defaults to the latest version
        known to the parser (`_AIF_VERSION_LATEST`). Must be a version
        registered in `_SCHEMA_REGISTRY`.

    Returns
    -------
    str: optional
        String representation of the AIF, if path not provided.

    Notes
    -----
    Numerical data is written to ``_PARSER_PRECISION`` significant figures.

    List and dictionary properties are JSON-encoded. Lists of row dictionaries
    (e.g. ``analysis_fit`` read from an AIF) are written as loops: under their
    AIF category if it exists in the target version, otherwise as
    ``_pygaps_<name>.<column>`` loops.

    AIF requires a ``_units_*`` tag for dimensional values (sample mass,
    density, degas time, enthalpy...). If the isotherm has no corresponding
    ``units_*`` property, the pyGAPS defaults are written: ``g``, ``g/cm3``,
    ``g/mol``, ``h``, ``kJ/mol``, ``m2/g``, ``cm3/g`` and ``nm``.

    The material ``activation_temperature`` is written as
    ``_adsnt_degas_temperature`` which AIF expresses in ``_units_temperature``,
    the isotherm temperature unit. No conversion is performed, so it should be
    given in the same unit as the isotherm temperature.

    A missing or empty experimental method is exported as ``unspecified``.
    A pyGAPS marker preserves the original value (or absence) on re-import;
    explicitly supplied methods, including ``unspecified``, are retained.

    References
    ----------
    .. [#] Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
       ‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
       acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

    """
    if version not in _SCHEMA_REGISTRY:
        raise ParameterError(f"Unknown AIF schema version {version!r}. Known versions: {sorted(_SCHEMA_REGISTRY)}.")
    schema = _SCHEMA_REGISTRY[version]
    metadata_write = schema['metadata_write']

    iso_dict = isotherm.to_dict()
    if version == _AIF_VERSION_v1p0:
        adsorbate = isotherm.adsorbate.to_dict()
        adsorbate_properties = {}
        for key, value in adsorbate.items():
            if key == 'name' or value is None:
                continue
            if key == 'molar_mass':
                if 'molecular_weight' in adsorbate:
                    continue
                key = 'molecular_weight'
            if f'adsorbate_{key}' not in metadata_write:
                continue
            if key == 'quadrupole_moment' and not iso_dict.get('units_quadrupole_moment'):
                logger.warning("Adsorbate quadrupole_moment was not written because units_quadrupole_moment is not specified.")
                continue
            adsorbate_properties[key] = value
        iso_dict['adsorbate'] = {
            'name': adsorbate['name'],
            **adsorbate_properties,
        }

    # Separate material metadata so we can map known fields and keep extras.
    _flatten_section(iso_dict, "material")
    _flatten_section(iso_dict, "adsorbate")
    original_method = None
    if version == _AIF_VERSION_v1p0 and not iso_dict.get('experimental_method'):
        original_method = {'value': iso_dict['experimental_method']} if 'experimental_method' in iso_dict else {}
        iso_dict['experimental_method'] = 'unspecified'

    # Start writing AIF
    aif = cif.Document()

    # initialize aif block
    aif.add_new_block(str(isotherm.iso_id))
    block = aif.sole_block()

    # Audit
    _write_text_pair(block, '_audit_aif_version', version)
    _write_text_pair(block, '_audit_creation_method', _PYGAPS_CREATION_METHOD)
    _write_text_pair(block, '_audit_creation_software', _pygaps_software_marker())
    _write_text_pair(block, '_pygaps_original_experimental_method', original_method)

    # Metadata
    row_lists = {key: iso_dict.pop(key) for key in list(iso_dict) if _is_row_list(iso_dict[key])}
    _write_metadata(block, iso_dict, metadata_write)

    # Units
    _write_units(block, isotherm, metadata_write)

    loop_tags = []
    if isinstance(isotherm, PointIsotherm):
        loop_tags += [f"_adsorp_{_loop_suffix_for_write(key, schema)}" for key in ['pressure', 'loading', *isotherm.other_keys]]
    for name, rows in row_lists.items():
        if name.lower() in schema['loop_categories']:
            loop_tags += [f"_{name.lower()}_{column}" for row in rows for column in row]
    _write_dependent_units(block, loop_tags, schema)

    for unit in BaseIsotherm._unit_params:
        _write_text_pair(block, f"_pygaps_{unit}", iso_dict.pop(unit, None))

    # Keep pyGAPS-only metadata in a namespaced section for lossless round-trip.
    for meta in iso_dict:
        if meta == 'material':
            continue
        _write_text_pair(
            block,
            f"_pygaps_{meta.lstrip('_').replace(' ', '_')}",
            iso_dict[meta],
        )

    # data
    if isinstance(isotherm, PointIsotherm):
        other_keys = isotherm.other_keys

        # write adsorption data
        if isotherm.has_branch('ads'):
            df = isotherm.data(branch='ads')
            _write_loop(block, '_adsorp_', df, isotherm.pressure_key, isotherm.loading_key, other_keys, schema)

        # write desorption data
        if isotherm.has_branch('des'):
            df = isotherm.data(branch='des')
            _write_loop(block, '_desorp_', df, isotherm.pressure_key, isotherm.loading_key, other_keys, schema)

    elif isinstance(isotherm, ModelIsotherm):
        _write_text_pair(block, "_pygaps_model_name", isotherm.model.name)
        _write_text_pair(block, "_pygaps_model_rmse", f"{isotherm.model.rmse}")
        _write_text_pair(block, "_pygaps_model_pressure_range_min", f"{isotherm.model.pressure_range[0]}")
        _write_text_pair(block, "_pygaps_model_pressure_range_max", f"{isotherm.model.pressure_range[1]}")
        _write_text_pair(block, "_pygaps_model_loading_range_min", f"{isotherm.model.loading_range[0]}")
        _write_text_pair(block, "_pygaps_model_loading_range_max", f"{isotherm.model.loading_range[1]}")
        for key, val in isotherm.model.params.items():
            _write_text_pair(block, f"_pygaps_model_param_{key}", f"{val}")

    # other loops, e.g. analysis results or pyGAPS row lists
    for name, rows in row_lists.items():
        _write_rows_loop(block, name, rows, schema)

    if path:
        aif.write_file(f"{os.path.splitext(path)[0]}.aif")
    else:
        return aif.as_string()


def isotherm_from_aif(str_or_path: str, version: Optional[str] = None, **isotherm_parameters: dict):
    """
    Parse an isotherm from an AIF format (file or raw string) [#]_.

    Parameters
    ----------
    str_or_path : str
        The isotherm in a AIF string format or a path
        to where one can be read.
    version : str, optional
        The version of the AIF format to use for parsing.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the AIF file or string.

    Raises
    ------
    ParsingError
        If the AIF document does not contain exactly one data block, or a
        data loop lacks the pressure or total amount column needed by pyGAPS.

    References
    ----------
    .. [#] Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
       ‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
       acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

    """
    isfile = False
    try:
        if pathlib.Path(str_or_path).is_file():
            isfile = True
    except OSError:
        pass

    if isfile:
        aif = cif.read_file(str(str_or_path))
    else:
        try:
            aif = cif.read_string(str_or_path)
        except (RuntimeError, ValueError) as ex:
            raise ParsingError("Could not parse AIF isotherm. The `path/string` is invalid or does not exist. ") from ex

    if len(aif) != 1:
        raise ParsingError(f"The AIF file should have a single block; found {len(aif)}.")
    block = aif.sole_block()
    raw_dict = {}
    data_branches = {}
    original_method = None

    # Use the provided version if given, otherwise read the version from the file or set it to the latest.
    if not version:
        version = block.find_value('_audit_aif_version')
    version = _normalize_version(version)
    if not version:
        version = _AIF_VERSION_LATEST
        logger.warning(
            "There is no AIF version specified in the file. "
            f"The parser will still attempt to read it using the latest schema ({_AIF_VERSION_LATEST})."
        )
    if version not in _SCHEMA_REGISTRY:
        logger.warning(
            f"The file aif version is {version} while the parser knows "
            f"{sorted(_SCHEMA_REGISTRY)}. "
            f"The parser will still attempt to read it using the latest schema ({_AIF_VERSION_LATEST})."
        )
        version = _AIF_VERSION_LATEST

    # check for missing required tags
    schema = _SCHEMA_REGISTRY[version]
    missing = [tag for tag in schema['required'] if block.find_value(tag) is None]
    if missing:
        logger.warning(
            f"File declares AIF version {version} ({schema['name']}) but is missing "
            f"required tag(s): {', '.join(missing)}. Parsing will continue on a "
            "best-effort basis."
        )

    metadata_read = schema['metadata_read']
    created_with_pygaps = False

    # Read STAR entries sequentially to preserve unknown keys and loop columns.
    for item in block:
        # Handle the metadata key-value pairs
        if item.pair is not None:
            key, val = item.pair
            lkey = key.lower()
            val = _unquote(val)

            # unknown/inapplicable values carry no information
            if val is None or lkey == '_audit_aif_version':
                continue

            # pyGAPS provenance markers are not isotherm metadata
            if lkey == '_audit_creation_method' and val in (_PYGAPS_CREATION_METHOD, 'pyGAPS'):
                created_with_pygaps = True
                continue
            if lkey == '_audit_creation_software' and val.startswith('pyGAPS'):
                continue
            if lkey == '_pygaps_original_experimental_method':
                original_method = _from_text(val)
                if not isinstance(original_method, dict) or set(original_method) - {'value'}:
                    raise ParsingError(
                        "Invalid _pygaps_original_experimental_method marker: expected a JSON object with an optional 'value' key."
                    )
                continue

            # Handle known metadata keys
            if lkey in metadata_read:
                info = metadata_read[lkey]
                try:
                    raw_dict[info['key']] = _cast_value(val, info['type'])
                except (TypeError, ValueError):
                    logger.warning(f"Could not parse parameter {info['key']}, currently {val}")
                    raw_dict[info['key']] = cast_string(val)

            # Handle pygaps specific keys (namespaced with '_pygaps_')
            elif lkey.startswith('_pygaps_'):
                raw_dict[key[8:]] = _from_text(val)

            # Handle other keys by saving as-is (stripped of leading underscore)
            else:
                raw_dict[key.lstrip('_')] = _from_text(val)

        # Handle the STAR loops
        elif item.loop is not None:
            loop = item.loop
            first_tag = loop.tags[0].lower()

            if first_tag.startswith('_adsorp_') and not first_tag.startswith('_adsorp_transient_'):
                data_branches[0] = _read_data_loop(block, loop, '_adsorp_', 0, schema)
            elif first_tag.startswith('_desorp_') and not first_tag.startswith('_desorp_transient_'):
                data_branches[1] = _read_data_loop(block, loop, '_desorp_', 1, schema)
            else:
                # kept as raw rows, to be interpreted later
                name, rows = _read_other_loop(block, loop)
                raw_dict[name] = rows

    if created_with_pygaps and original_method is not None and raw_dict.get('experimental_method') == 'unspecified':
        raw_dict.pop('experimental_method')
        if 'value' in original_method:
            raw_dict['experimental_method'] = original_method['value']

    # Values that pyGAPS replaced with its own provenance on writing
    for marker in ('method', 'software'):
        previous = raw_dict.pop(f'audit_previous_creation_{marker}', None)
        if previous is not None:
            raw_dict[f'audit_creation_{marker}'] = previous

    # Default units added by the pyGAPS writer are implied, not metadata
    if created_with_pygaps:
        for unit_tag, default in _UNIT_DEFAULTS.items():
            if raw_dict.get(unit_tag[1:]) == default:
                raw_dict.pop(unit_tag[1:])

    # Parse STAR unit fields if pyGAPS-specific unit hints are not all present.
    missing_unit_hints = [unit_name for unit_name in BaseIsotherm._unit_params if unit_name not in raw_dict]
    if missing_unit_hints == ['pressure_unit'] and raw_dict.get('pressure_mode', '').startswith('relative'):
        missing_unit_hints = []
    parse_units = bool(missing_unit_hints)
    if isotherm_parameters and isotherm_parameters.pop("_parse_units", False):
        parse_units = True

    pressure_units = raw_dict.pop('units_pressure', None)
    loading_material_units = raw_dict.pop('units_sorbed_amount', None)
    temperature_units = raw_dict.pop('units_temperature', None)

    if parse_units:
        if pressure_units:
            raw_dict.update(cast(dict, parse_pressure_string(pressure_units)))
        if loading_material_units:
            raw_dict.update(cast(dict, parse_loading_string(loading_material_units)))
        if temperature_units:
            raw_dict['temperature_unit'] = parse_temperature_string(temperature_units)

    # parse the material dictionary from the AIF dict
    raw_dict = _parse_subsection(raw_dict, 'material')

    # parse the adsorbate dictionary from the AIF dict
    raw_dict = _parse_subsection(raw_dict, 'adsorbate')
    if 'adsorbate' in raw_dict:
        raw_dict['adsorbate'] = _build_adsorbate(raw_dict['adsorbate'])

    # update anything needed
    if isotherm_parameters:
        raw_dict.update(isotherm_parameters)

    # parse specific isotherm types

    # PointIsotherm
    if data_branches:
        ads_branch = data_branches.get(0)
        des_branch = data_branches.get(1)
        if ads_branch is None:
            ads_branch = des_branch
        elif des_branch is not None:
            ads_branch = pandas.concat([ads_branch, des_branch], ignore_index=True)

        # generate the isotherm
        return PointIsotherm(
            isotherm_data=ads_branch,
            pressure_key='pressure',
            loading_key='loading',
            **raw_dict,
        )

    # ModelIsotherm
    if 'model_name' in raw_dict:
        model = {}

        model['name'] = raw_dict.pop("model_name")
        model['rmse'] = raw_dict.pop("model_rmse")
        model['pressure_range'] = [
            raw_dict.pop("model_pressure_range_min"),
            raw_dict.pop("model_pressure_range_max"),
        ]
        model['loading_range'] = [
            raw_dict.pop("model_loading_range_min"),
            raw_dict.pop("model_loading_range_max"),
        ]
        model_parameters = {}
        keys = [key for key in raw_dict if key.startswith("model_param_")]
        for key in keys:
            model_parameters[key[12:]] = raw_dict.pop(key)
        model["parameters"] = model_parameters

        return ModelIsotherm(
            model=model_from_dict(model),
            **raw_dict,
        )

    # If no specific isotherm type was detected, return a generic BaseIsotherm.
    return BaseIsotherm(**raw_dict)
