"""Interface with BEL-generated DAT files."""

import dateutil.parser

from pygaps.parsing.bel_common import _META_DICT
from pygaps.parsing.bel_common import _parse_header
from pygaps.utilities.exceptions import ParsingError


def parse(path):
    """
    Get the isotherm and sample data from a BEL Japan .dat file.
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

    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            values = line.strip().split(sep='\t')
            nvalues = len(values)

            if nvalues == 2:  # If value pair
                key, val = [v.strip('"').replace(',', ' ') for v in values]
                key = key.lower()
                try:  # find the standard name in the _META_DICT dictionary
                    name = next(
                        k for k, v in _META_DICT.items()
                        if any(key.startswith(n) for n in v.get('text', []))
                    )
                except StopIteration:  # Store unknown as is
                    key = key.lower().replace(" ", "_")
                    meta[key] = val
                    continue
                meta[name] = val

                if name == "temperature":
                    if "/k" in key:
                        meta['temperature_unit'] = 'K'  # TODO, find a better way to handle units

            elif nvalues < 2:  # If "section title"
                title = values[0].strip().lower()

                # read "adsorption" section
                if title.startswith('adsorption data'):
                    file.readline()  # ====== - discard
                    header_line = file.readline().rstrip()  # header
                    header_list = header_line.replace('"', '').split("\t")
                    head, units = _parse_header(header_list)  # header
                    meta.update(units)

                    line = file.readline()  # first ads line
                    while not line.startswith('0'):
                        data.append([0] + list(map(float, line.split())))
                        line = file.readline()

                # read "desorption" section
                elif title.startswith('desorption data'):
                    file.readline()  # ====== - discard
                    file.readline()  # header - discard

                    line = file.readline()  # first des line
                    while not line.startswith('0'):
                        data.append([1] + list(map(float, line.split())))
                        line = file.readline()

                else:  # other section titles
                    continue

            else:
                raise ParsingError(f"Unknown line format: {line}")

    # Format extra metadata
    meta['date'] = dateutil.parser.parse(meta['date']).isoformat()
    meta['apparatus'] = 'BEL ' + meta["serialnumber"]

    # Prepare data
    data = dict(zip(head, map(lambda *x: list(x), *data)))

    return meta, data
