# -*- coding: utf-8 -*-
"""
Parse BEL CSV to AIF
Handles both western and JIS encoded text
Modified from https://github.com/AIF-development-team/adsorptioninformationformat
"""

import dateutil.parser

from pygaps.parsing.bel_common import _META_DICT
from pygaps.parsing.bel_common import _parse_header

from . import utils as util


def parse(path, separator=",", lang="ENG"):
    """
    Get the isotherm and sample data from a BEL Japan .csv file.
    Parameters
    ----------
    path : str
        Path to the file to be read.
    Returns
    -------
    dataDF
    """

    # set encoding
    if lang == 'ENG':
        encoding = 'ISO-8859-1'
    else:
        encoding = 'shift_jis'

    meta = {}
    head = []
    data = []

    # local for efficiency
    meta_dict = _META_DICT.copy()

    with open(path, 'r', encoding=encoding) as file:
        for line in file:
            values = line.strip().split(sep=separator)
            nvalues = len(values)

            if not line.startswith('No,') and nvalues > 1:  # key value section
                text, val = values[0], values[1]
                text = text.strip().lower()
                try:  # find the standard name in the metadata dictionary
                    key = util.search_key_in_def_dict(text, meta_dict)
                except StopIteration:  # Store unknown as is
                    key = text.replace(" ", "_")
                    if nvalues > 2:
                        val = val + " " + values[2].strip("[]")
                    meta[key] = val
                    continue

                meta[key] = val
                if nvalues > 2 and meta_dict[key].get("unit"):
                    meta[meta_dict[key]['unit']] = values[2].strip('[]')
                del meta_dict[key]  # delete for efficiency

            elif line.startswith('No,'):  # If "data" section

                header_list = line.replace('"', '').split(separator)
                head, units = _parse_header(header_list)  # header
                meta.update(units)
                file.readline()  # ADS - discard

                # read "adsorption" section
                line = file.readline()  # first ads line
                while not line.startswith('DES'):
                    data.append([0] + list(map(float, line.split(separator))))
                    line = file.readline()

                line = file.readline()  # first des line
                while line:
                    data.append([1] + list(map(float, line.split(separator))))
                    line = file.readline()

    # Format extra metadata
    meta['date'] = dateutil.parser.parse(meta['date']).isoformat()
    meta['apparatus'] = 'BEL ' + meta["serialnumber"]
    if not meta['material']:
        meta['material'] = meta['file_name']

    # Prepare data
    data = dict(zip(head, map(lambda *x: list(x), *data)))

    return meta, data
