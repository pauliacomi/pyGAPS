"""
An AIF (adsorption information file) parsing implementation.

Format developed in this publication:

Evans, Jack D., Volodymyr Bon, Irena Senkovska, and Stefan Kaskel.
‘A Universal Standard Archive File for Adsorption Data’. Langmuir, 2 April 2021,
acs.langmuir.1c00122. https://doi.org/10.1021/acs.langmuir.1c00122.

"""
import os
import pathlib
import warnings

import pandas
from gemmi import cif

from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.converter_mode import _MASS_UNITS
from pygaps.utilities.converter_mode import _MOLAR_UNITS
from pygaps.utilities.converter_mode import _VOLUME_UNITS

_parser_version = "1.0"

_FIELDS = {
    '_exptl_temperature': 'temperature',
    '_exptl_adsorptive': 'adsorbate',
    '_sample_material_id': 'material',
    '_exptl_operator': 'user',
    '_exptl_date': 'date',
    '_exptl_instrument': 'instrument',
    '_exptl_sample_mass': 'material_mass',
    '_exptl_activation_temperature': 'activation_temperature',
    '_sample_id': 'material_batch',
}


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
    for spec in _FIELDS:
        if _FIELDS[spec] in iso_dict:
            block.set_pair(spec, f"\'{iso_dict.pop(_FIELDS[spec])}\'")

    # units
    block.set_pair('_units_temperature', isotherm.temperature_unit)
    if isotherm.pressure_mode == 'absolute':
        block.set_pair('_units_pressure', isotherm.pressure_unit)
    else:
        block.set_pair('_units_pressure', isotherm.pressure_mode)

    block.set_pair(
        '_units_loading', f"{isotherm.loading_unit}/{isotherm.material_unit}"
    )
    for unit in [
        'pressure_mode',
        'pressure_unit',
        'loading_basis',
        'loading_unit',
        'material_basis',
        'material_unit',
        'temperature_unit',
    ]:
        iso_dict.pop(unit)

    # remaining metadata
    for meta in iso_dict:
        block.set_pair(f"_pygaps_{meta}", f"\'{iso_dict[meta]}\'")

    # data
    if isinstance(isotherm, PointIsotherm):

        columns = [
            isotherm.pressure_key, isotherm.loading_key
        ] + isotherm.other_keys

        # write adsorption data
        loop_ads = block.init_loop(
            '_adsorp_',
            ['pressure', 'loading'] + isotherm.other_keys,
        )
        loop_ads.set_all_values(
            isotherm.data(branch='ads'
                          )[columns].values.T.astype("|S10").tolist()
        )

        # write desorption data
        if isotherm.has_branch('des'):
            loop_des = block.init_loop(
                '_desorp_',
                ['pressure', 'loading'] + isotherm.other_keys,
            )
            loop_des.set_all_values(
                isotherm.data(branch='des'
                              )[columns].values.T.astype("|S10").tolist()
            )

    if path:
        aif.write_file(f"{os.path.splitext(path)[0]}.aif")
    else:
        return aif.as_string()


def isotherm_from_aif(str_or_path: str, **isotherm_parameters):
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
        aif = cif.read_file(str_or_path)
    else:
        try:
            aif = cif.read_string(str_or_path)
        except Exception:
            raise ParsingError(
                "Could not parse AIF isotherm. "
                "The `str_or_path` is invalid or does not exist. "
            )

    block = aif.sole_block()
    raw_dict = {}

    # read metadata
    version = block.find_value('_audit_aif_version')
    if not version or float(version) < float(_parser_version):
        warnings.warn(
            f"The file version is {version} while the parser uses version {_parser_version}. "
            "Strange things might happen, so double check your data."
        )

    # meta
    excluded = [
        "_audit_aif_version",
        "_audit_creation_method",
        "_units_temperature",
        "_units_pressure",
        "_units_loading",
        "_audit_creation_method",
    ]
    for item in block:
        if item.pair is not None:
            key, val = item.pair
            val = val.strip("'")
            if val == 'None':
                val = None
            if key in _FIELDS:
                raw_dict[_FIELDS[key]] = val
            elif key.startswith('_pygaps_'):
                raw_dict[key[8:]] = val
            elif key not in excluded:
                raw_dict[key] = val

    # dictionary
    type_dict = {
        'activation_temperature': float,
    }
    for key in type_dict:
        if key in raw_dict:
            raw_dict[key] = type_dict[key](raw_dict[key])

    # pressure units
    pressure_units = block.find_value('_units_pressure')
    if pressure_units == 'relative':
        raw_dict['pressure_mode'] = 'relative'
    else:
        raw_dict['pressure_mode'] = 'absolute'
        raw_dict['pressure_unit'] = pressure_units

    # loading units
    loading_units = block.find_value('_units_loading')
    comp = loading_units.split('/')
    if len(comp) != 2:
        raise ParsingError(
            "Isotherm cannot be parsed due to loading string format."
        )

    loading_unit = comp[0]
    if loading_unit in _MOLAR_UNITS:
        raw_dict['loading_basis'] = 'molar'
    elif loading_unit in _MASS_UNITS:
        raw_dict['loading_basis'] = 'mass'
    elif loading_unit in _VOLUME_UNITS:
        raw_dict['loading_basis'] = 'volume'
    else:
        raise ParsingError("Isotherm cannot be parsed due to loading unit.")
    raw_dict['loading_unit'] = loading_unit

    material_unit = comp[1]
    if material_unit in _MASS_UNITS:
        raw_dict['material_basis'] = "mass"
    elif material_unit in _VOLUME_UNITS:
        raw_dict['material_basis'] = "volume"
    elif material_unit in _MOLAR_UNITS:
        raw_dict['material_basis'] = "molar"
    else:
        raise ParsingError("Isotherm cannot be parsed due to material basis.")
    raw_dict['material_unit'] = material_unit

    # unit temperature
    raw_dict['temperature_unit'] = block.find_value('_units_temperature')

    # data
    ads_block = block.find([
        '_adsorp_pressure', '_adsorp_loading', '?_adsorp_enthalpy'
    ])
    columns = ['pressure', 'loading']
    other_keys = []
    if ads_block.width() == 3:
        columns.append('enthalpy')
        other_keys = ['enthalpy']

    adsorption = pandas.DataFrame(
        ads_block,
        columns=columns,
        dtype=float,
    )
    des_block = block.find([
        '_desorp_pressure', '_desorp_loading', '?_desorp_enthalpy'
    ])
    adsorption['branch'] = False
    desorption = pandas.DataFrame(
        des_block,
        columns=columns,
        dtype=float,
    )
    desorption['branch'] = True

    # generate the isotherm
    return PointIsotherm(
        isotherm_data=pandas.concat([adsorption, desorption],
                                    ignore_index=True),
        pressure_key='pressure',
        loading_key='loading',
        other_keys=other_keys,
        **raw_dict
    )
