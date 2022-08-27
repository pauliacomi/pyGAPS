"""Parse Quantachrome txt output files."""
import re

import dateutil.parser

from pygaps.parsing.unit_parsing import parse_temperature_unit

_META_DICT = {
    'adsorbate': {
        "text": ("analysis gas:", ),
        "type": "string",
    },
    'adsorbate_molecular_weight': {
        "text": ("molec. wt:", ),
        "type": "numeric",
    },
    'adsorbate_non_ideality': {
        "text": ("non-ideality:", ),
        "type": "numeric",
    },
    'material_mass': {
        "text": ("sample weight:", ),
        "type": "numeric",
    },
    'material_volume': {
        "text": ("sample volume:", ),
        "type": "numeric",
    },
    'temperature': {
        "text": ("bath temp:", "bath temp.:"),
        "type": "numeric",
    },
    'apparatus': {
        "text": ("instrument:", ),
        "type": "string",
    },
    'apparatus_version': {
        "text": ("instrument version:", ),
        "type": "string",
    },
    'measurement_duration': {
        "text": ("analysis time:", ),
        "type": "numeric",
    },
    'outgas_time': {
        "text": ("outgas time:", ),
        "type": "string",
    },
    'outgas_temperature': {
        "text": ("outgas temp:", "outgastemp:", "outgas temp.:"),
        "type": "numeric",
    },
    'pressure_tolerance': {
        "text": ("press. tolerance:", ),
        "type": "string",
    },
    'equilibration_time': {
        "text": ("equil time:", ),
        "type": "string",
    },
    'equilibration_timeout': {
        "text": ("equil timeout:", ),
        "type": "string",
    },
    'void_volume': {
        "text": ("void vol.:", ),
        "type": "numeric",
    },
    'cell': {
        "text": ("cell:", "celltype:"),
        "type": "string",
    },
    'cell_id': {
        "text": ("cell id:", ),
        "type": "string",
    },
    'run_mode': {
        "text": ("run mode:", ),
        "type": "string",
    },
    'end_of_run': {
        "text": ("end of run:", ),
        "type": "datetime",
    },
    'extended_info': {
        "text": ("extended info:", ),
        "type": "string",
    },
}

_DATA_DICT = {
    'pressure': {
        "text": ("press", )
    },
    'pressure_relative': {
        "text": ("p/p0", "p/po")
    },
    'pressure_saturation': {
        "text": ("p0", "po")
    },
    'loading': {
        "text": ("volume @ stp", )
    },
    'measurement_time': {
        "text": ("time", )
    },
    'pressure_tolerance': {
        "text": ("tol", )
    },
    'equilibration_timeout': {
        "text": ("timeout", )
    },
    'equilibration_time': {
        "text": ("equ", "equlibration")
    },
}


def find_key_vals_from_position(line, keys, poss):
    """Find keys of successive key-val pairs, knowing the key position"""
    vals = []
    for i, (key, pos) in enumerate(zip(keys, poss)):
        try:
            vals.append(line[pos + len(key):poss[i + 1]].strip())
        except IndexError:
            vals.append(line[pos + len(key):].strip())
    return vals


def find_key_vals_from_keys(line, keys):
    """Find keys of successive key-val pairs, not knowing the key position"""
    vals = []
    for key in keys:
        start = line.find(key)
        if start != 0:
            vals.append(line[:start].strip())
        line = line[start + len(key):]
    vals.append(line.strip())
    return vals


def parse(path):
    """
    Get the isotherm and sample data from a Quantachrome .txt file.
    Parameters
    ----------
    path : str
        Path to the file to be read.
    Returns
    -------
    meta : dict
        Isotherm metadata.
    data : dict
        Isotherm data.
    """

    meta = {}
    head = []
    data = []

    with open(path, 'r', encoding='cp1252') as file:

        # We skip the header
        for _ in range(6):
            file.readline()

        # metadata section
        #
        # first four lines are always the same
        line7 = file.readline()
        vals = find_key_vals_from_keys(line7, ["Operator:", "Date:", "Operator:", "Date:"])
        meta['operator'] = vals[0]
        meta['date'] = vals[1]
        meta['report_operator'] = vals[2]
        meta['report_date'] = vals[3]

        line8 = file.readline()
        vals = find_key_vals_from_keys(line8, ["Sample ID:", "Filename:"])
        meta['material'] = vals[0]
        meta['filename'] = vals[1]

        line9 = file.readline()
        vals = find_key_vals_from_keys(line9, ["Sample Desc:", "Comment:"])
        meta['material_description'] = vals[0]
        meta['comment'] = vals[1]

        # next lines are variable
        local_meta_dict = _META_DICT.copy()
        for line in file:
            # break if we reach the end of the metadata
            if line == "\n":
                break

            components = []
            line_lower = line.lower()
            for key, names in local_meta_dict.items():
                # pos = line_lower.find(names["text"])
                for text in names["text"]:
                    pos = line_lower.find(text)
                    if pos != -1:
                        components.append((pos, key, text))
                        break
            if components:
                components.sort(key=lambda x: x[0])
                vals = find_key_vals_from_position(
                    line,
                    [x[2] for x in components],
                    [x[0] for x in components],
                )
                for x, y in zip(components, vals):
                    meta[x[1]] = y
                    del local_meta_dict[x[1]]

        # data section
        #
        # data headers
        line = file.readline()
        file_headers = re.split(r"\s{2,}", line.strip())
        file_header_locations = [line.find(" " + header) + 1 for header in file_headers]
        for h in file_headers:
            txt = next((k for k, v in _DATA_DICT.items() if h.lower() in v["text"]), h)
            head.append(txt)

        # skip line
        file.readline()

        # data header units
        line = file.readline()
        all_units = []
        stated_units = re.split(r"\s{2,}", line.strip())
        for loc in file_header_locations:
            unit = None
            if loc < len(line):
                if not line[loc:loc + 8].isspace():
                    unit = stated_units.pop(0)
            all_units.append(unit)

        # skip line
        file.readline()

        # data
        line = file.readline()
        while line:
            data.append(list(map(float, line.split())))
            line = file.readline()

    # Elaborate and clarify some metadata
    mass, mass_unit = meta['material_mass'].split()
    temp, temp_unit = meta['temperature'].split()
    mass, temp = map(float, (mass, temp))

    meta['material_mass'] = mass
    meta['material_unit'] = mass_unit
    meta['temperature'] = temp
    meta['temperature_unit'] = parse_temperature_unit(temp_unit)

    # takes care of pressure, loading and other units
    for i, h in enumerate(head):
        if h == "pressure_relative":
            meta["pressure_unit"] = None
        else:
            meta[h + '_unit'] = all_units[i]

    if meta["loading_unit"] in ["cc"]:
        meta["loading_unit"] += "(STP)"

    if meta.get("date"):
        meta['date'] = dateutil.parser.parse(meta['date']).isoformat()

    # amount adsorbed from cc to cc/g
    data = dict(zip(head, map(lambda *x: list(x), *data)))
    data['loading'] = [ld / mass for ld in data["loading"]]

    return meta, data
