from pygaps import logger
from pygaps.utilities.exceptions import ParsingError

_META_DICT = {
    'material': {
        "text": ('comment1', 'コメント１'),
        'type': 'string',
        "xl_ref": (0, 2),
    },
    'adsorbate': {
        "text": ('adsorptive', '吸着質名称'),
        'type': 'string',
        "xl_ref": (0, 2),
    },
    'temperature': {
        "text": (
            'adsorption temperature',
            'adsorption temperature',
            "meas. temp",
            '吸着温度',
        ),
        'type': 'number',
        "unit": "temperature_unit",
        "xl_ref": (0, 2),
    },
    'operator': {
        "text": ('comment2', 'コメント２'),
        'type': 'string',
        "xl_ref": (0, 2),
    },
    'date': {
        "text": ('date of measurement', '測定日'),
        'type': 'date',
        "xl_ref": (0, 2),
    },
    'material_mass': {
        "text": ('sample weight', 'サンプル質量'),
        "unit": "material_unit",
        'type': 'number',
        "xl_ref": (0, 2),
    },
    'measurement_duration': {
        "text": ('time of measurement', '測定時間'),
        'type': 'time',
        "xl_ref": (0, 2),
    },
    'serialnumber': {
        "text": ('serial number', 's/n', "instrument", 'シリアルナンバー'),
        'type': 'string',
        "xl_ref": (0, 2),
    },
    'errors': {
        'text': ('primary data', ),
        'type': 'error',
        "xl_ref": (0, 2),
    },
    'comments': {
        'text': ('comment3', ),
        'name': 'comment',
        'type': 'string',
        "xl_ref": (0, 2),
    },
}

_DATA_DICT = {
    'no': 'measurement',
    'pi/': 'pressure_internal',
    'pe/': 'pressure',
    'pe2/': 'pressure2',
    'p0/': 'pressure_saturation',
    'p/p0': 'pressure_relative',
    'vd/': 'deadvolume',
    'v/': 'loading',
    'va/': 'loading',
    'n/': 'loading',
    'na/': 'loading',
}

_UNITS_DICT = {
    "p": {
        "torr": ('mmHg', 'torr'),
        "kPa": ('kPa'),
        "bar": ('bar'),
    },
    "l": {
        "mmol": ("mmol"),
        "mol": ("mol"),
        "cm3(STP)": ("ml(STP)", "cm3(STP)", "cm^3(STP)"),
    },
    "m": {
        "g": ("g-1", "g^-1"),
    },
}


def _parse_header(header_split):
    """Parse an adsorption/desorption header to get columns and units."""
    headers = ['branch']
    units = {}

    for h in header_split:
        header = next((_DATA_DICT[a] for a in _DATA_DICT if h.lower().startswith(a)), h)
        headers.append(header)

        if header in 'loading':
            unit = h.split('/')[1].strip()
            unit_l, unit_m = unit.split(' ')

            units['loading_basis'] = 'molar'
            units['loading_unit'] = _parse_unit(unit_l, 'l')

            units['material_basis'] = 'mass'
            units['material_unit'] = _parse_unit(unit_m, 'm')

        elif header == 'pressure':
            unit = h.split('/')[1].strip()

            units['pressure_mode'] = 'absolute'
            units['pressure_unit'] = _parse_unit(unit, 'p')

    return headers, units


def _parse_unit(unit, unit_type):
    for (k, v) in _UNITS_DICT[unit_type].items():
        if unit in v:
            return k
    raise ParsingError(f"Could not parse unit '{unit}'.")


def _check(meta, data, path):
    """
    Check keys in data and logs a warning if a key is empty.

    Also logs a warning for errors found in file.
    """
    if 'loading' in data:
        empties = (k for k, v in data.items() if not v)
        for empty in empties:
            logger.info(f"No data collected for {empty} in file {path}.")
    if 'errors' in meta:
        logger.warning('\n'.join(meta['errors']))
