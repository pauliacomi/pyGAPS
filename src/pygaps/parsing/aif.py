"""
An AIF (adsorption information file) parsing implementation.

Format developed in this publication:

Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

"""
import os
import pathlib

import pandas
from adsorption_file_parser.utils.unit_parsing import parse_loading_string
from adsorption_file_parser.utils.unit_parsing import parse_pressure_string
from adsorption_file_parser.utils.unit_parsing import parse_temperature_string
from gemmi import cif

from pygaps import logger
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.modelling import model_from_dict
from pygaps.parsing import _PARSER_PRECISION
from pygaps.utilities.exceptions import ParsingError
from pygaps.utilities.string_utilities import cast_string

_parser_version = "1.0"

_META_DICT = {
    '_exptl_temperature': {
        'text': 'temperature',
        'type': float
    },
    '_exptl_adsorptive': {
        'text': 'adsorbate',
        'type': str
    },
    '_sample_material_id': {
        'text': 'material',
        'type': str
    },
    '_exptl_operator': {
        'text': 'user',
        'type': str
    },
    '_exptl_date': {
        'text': 'date',
        'type': str
    },
    '_exptl_instrument': {
        'text': 'instrument',
        'type': str
    },
    '_exptl_sample_mass': {
        'text': 'material_mass',
        'type': float
    },
    '_units_mass': {
        'text': 'material_mass_unit',
        'type': str
    },
    '_exptl_activation_temperature': {
        'text': 'activation_temperature',
        'type': float
    },
    '_sample_id': {
        'text': 'material_batch',
        'type': str
    },
}
_DATA_DICT = {
    'pressure': 'pressure',
    'p0': 'pressure_saturation',
    'amount': 'loading',
    'enthalpy': 'enthalpy',
}
_UNITS_DICT = [
    "_units_pressure",
    "_units_loading",
    "_units_mass",
    "_units_temperature",
]


def isotherm_to_aif(isotherm: PointIsotherm, path: str = None):
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

    Returns
    -------
    str: optional
        String representation of the AIF, if path not provided.

    References
    ----------
    .. [#] Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
       ‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
       acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

    """
    iso_dict = isotherm.to_dict()

    # Parse material
    material = iso_dict['material']
    if isinstance(material, dict):
        iso_dict['material'] = material.pop('name')
        iso_dict.update({f"sample_{key}": val for key, val in material.items()})

    # Start writing AIF
    aif = cif.Document()

    # initialize aif block
    aif.add_new_block(str(isotherm.iso_id))
    block = aif.sole_block()

    # write metadata
    block.set_pair('_audit_aif_version', _parser_version)
    block.set_pair('_audit_creation_method', 'pyGAPS')

    # required pygaps data
    block.set_pair('_exptl_adsorptive', f"\'{iso_dict.pop('adsorbate')}\'")
    block.set_pair('_exptl_temperature', f"{iso_dict.pop('temperature')}")
    block.set_pair('_sample_material_id', f"\'{iso_dict.pop('material')}\'")

    # other possible specs
    for key, val in _META_DICT.items():
        if val['text'] in iso_dict:
            block.set_pair(key, f"\'{iso_dict.pop(val['text'])}\'")

    # units
    block.set_pair('_units_temperature', f"'{isotherm.temperature_unit}'")

    if isotherm.pressure_mode == 'absolute':
        block.set_pair('_units_pressure', isotherm.pressure_unit)
    else:
        block.set_pair('_units_pressure', isotherm.pressure_mode)

    if isotherm.loading_basis == 'fraction':
        block.set_pair('_units_loading', f"'fraction {isotherm.material_basis}'")
    elif isotherm.loading_basis == 'percent':
        block.set_pair('_units_loading', f"'% {isotherm.material_basis}'")
    else:
        block.set_pair('_units_loading', f"'{isotherm.loading_unit}/{isotherm.material_unit}'")

    # TODO introduce these as standard in AIF
    for unit in BaseIsotherm._unit_params:
        block.set_pair(f"_pygaps_{unit}", f"'{iso_dict[unit]}'")
        iso_dict.pop(unit)

    # remaining metadata
    for meta in iso_dict:
        block.set_pair(f"_pygaps_{meta.replace(' ', '_')}", f"\'{iso_dict[meta]}\'")

    # data
    if isinstance(isotherm, PointIsotherm):

        other_keys = isotherm.other_keys
        columns = [isotherm.pressure_key, isotherm.loading_key] + other_keys

        # write adsorption data
        if isotherm.has_branch('ads'):
            loop_ads = block.init_loop('_adsorp_', ['pressure', 'amount'] + other_keys)
            df = isotherm.data(branch='ads')[columns]
            loop_ads.set_all_values(df.round(_PARSER_PRECISION).astype("string").values.T.tolist())

        # write desorption data
        if isotherm.has_branch('des'):
            loop_des = block.init_loop('_desorp_', ['pressure', 'amount'] + other_keys)
            df = isotherm.data(branch='des')[columns]
            loop_des.set_all_values(df.round(_PARSER_PRECISION).astype("string").values.T.tolist())

    elif isinstance(isotherm, ModelIsotherm):

        block.set_pair("_pygaps_model_name", isotherm.model.name)
        block.set_pair("_pygaps_model_rmse", f"{isotherm.model.rmse}")
        block.set_pair("_pygaps_model_pressure_range_min", f"{isotherm.model.pressure_range[0]}")
        block.set_pair("_pygaps_model_pressure_range_max", f"{isotherm.model.pressure_range[1]}")
        block.set_pair("_pygaps_model_loading_range_min", f"{isotherm.model.loading_range[0]}")
        block.set_pair("_pygaps_model_loading_range_max", f"{isotherm.model.loading_range[1]}")
        for key, val in isotherm.model.params.items():
            block.set_pair(f"_pygaps_model_param_{key}", f"{val}")

    if path:
        aif.write_file(f"{os.path.splitext(path)[0]}.aif")
    else:
        return aif.as_string()


def isotherm_from_aif(str_or_path: str, **isotherm_parameters: dict):
    """
    Parse an isotherm from an AIF format (file or raw string) [#]_.

    Parameters
    ----------
    str_or_path : str
        The isotherm in a AIF string format or a path
        to where one can be read.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the AIF file or string.


    References
    ----------
    .. [#] Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
       ‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
       acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

    """
    if pathlib.Path(str_or_path).exists():
        aif = cif.read_file(str(str_or_path))
    else:
        try:
            aif = cif.read_string(str_or_path)
        except Exception as ex:
            raise ParsingError(
                "Could not parse AIF isotherm. "
                "The `path/string` is invalid or does not exist. "
            ) from ex

    block = aif.sole_block()
    raw_dict = {}

    # read version
    version = block.find_value('_audit_aif_version').strip("'")
    if not version or float(version.strip("'")) < float(_parser_version):
        logger.warning(
            f"The file version is {version} while the parser uses version {_parser_version}. "
            "Strange things might happen, so double check your data."
        )

    # creation method (excluded if created in pygaps)
    cmethod = block.find_value('_audit_creation_method')
    if cmethod and cmethod.strip("'") != "pyGAPS":
        raw_dict["_audit_creation_method"] = cmethod.strip("'")

    # read data and metadata through sequential iteration
    # some properties are special and read separately
    excluded = [
        "_audit_aif_version",
        "_audit_creation_method",
    ] + _UNITS_DICT
    columns = []
    for item in block:
        # metadata handling
        if item.pair is not None:
            key, val = item.pair
            val = val.strip("'")

            if key in _META_DICT:
                raw_dict[_META_DICT[key]['text']] = _META_DICT[key]['type'](val)
            elif key.startswith('_pygaps_'):
                raw_dict[key[8:]] = cast_string(val)
            elif key not in excluded:
                raw_dict[key] = cast_string(val)

        # data handling
        elif item.loop is not None:
            loop = item.loop
            loop_data = block.find(loop.tags)

            # check for adsorption or desorption
            branch = 0
            if loop.tags[0].startswith('_desorp_'):
                branch = 1

            if not columns:
                for col in [tag[8:] for tag in loop.tags]:
                    def_col = _DATA_DICT.get(col, col)
                    columns.append(def_col)

            # data is often as strings
            # need to use to_numeric to convert what is appropriate
            data_df = pandas.DataFrame(
                loop_data,
                columns=columns,
            ).apply(pandas.to_numeric, errors='ignore')
            data_df['branch'] = branch
            raw_dict[f"data{branch:d}"] = data_df

    # deal with units gracefully
    # if the AIF was created with pygaps, exact backup units are created
    parse_units = False
    for unit_name in BaseIsotherm._unit_params:
        if unit_name not in raw_dict:
            parse_units = True
            break
    if isotherm_parameters and isotherm_parameters.pop("_parse_units"):
        parse_units = True

    if parse_units:
        # pressure units
        pressure_units = block.find_value('_units_pressure').strip("'")
        pressure_dict = parse_pressure_string(pressure_units)
        raw_dict.update(pressure_dict)

        # loading/material units
        loading_material_units = block.find_value('_units_loading').strip("'")
        loading_material_dict = parse_loading_string(loading_material_units)
        raw_dict.update(loading_material_dict)

        # temperature units
        temperature_units = block.find_value('_units_temperature').strip("'")
        raw_dict['temperature_unit'] = parse_temperature_string(temperature_units)

    # check if material needs parsing
    material = {}
    for key, val in raw_dict.items():
        if key.startswith("sample_"):
            material[key.replace("sample_", "")] = val
    if material:
        for key in material:
            raw_dict.pop("sample_" + key)
        material['name'] = raw_dict['material']
        raw_dict['material'] = material

    # update anything needed
    if isotherm_parameters:
        raw_dict.update(isotherm_parameters)

    if any(a.startswith("data") for a in raw_dict):
        ads_branch = raw_dict.pop("data0", None)
        des_branch = raw_dict.pop("data1", None)
        if des_branch is not None:
            ads_branch = pandas.concat([ads_branch, des_branch], ignore_index=True)

        # generate the isotherm
        return PointIsotherm(
            isotherm_data=ads_branch,
            pressure_key='pressure',
            loading_key='loading',
            **raw_dict,
        )

    if any(a.startswith("model") for a in raw_dict):

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
        keys = [key for key in raw_dict if key.startswith("model_param")]
        for key in keys:
            model_parameters[key[12:]] = raw_dict.pop(key)
        model["parameters"] = model_parameters

        return ModelIsotherm(
            model=model_from_dict(model),
            **raw_dict,
        )

    return BaseIsotherm(**raw_dict)
