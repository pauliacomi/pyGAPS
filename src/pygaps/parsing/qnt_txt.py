"""Parse Quantachrome txt output files."""

import re

import dateutil.parser

_META_DICT = {
    'material': {
        'text': "sample id",
    },
    'adsorbate': {
        'text': "analysis gas",
    },
    'temperature': {
        'text': "bath temp.",
    },
    'operator': {
        'text': "operator",
    },
    'date': {
        'text': "date",
    },
    'apparatus': {
        'text': "instrument",
    },
    'material_mass': {
        'text': "sample weight",
    },
    'measurement_duration': {
        'text': "analysis time",
    },
    'sample_description': {
        'text': "sample desc",
    },
    'comment': {
        'text': "comment",
    },
    'time_outgas': {
        'text': "outgas time",
    },
    'filename': {
        'text': "filename",
    },
    'nonideality': {
        'text': "non-ideality",
    },
}

_DATA_DICT = {
    'press': 'pressure',
    'p0': 'pressure_saturation',
    'volume': 'loading',
    'time': 'measurement_time',
    'tol': 'tolerance',
    'equ': 'equilibrium',
}


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

        for line in file:

            if ":" in line:  # this means a line with key/val pairs

                # we can only count on :
                line_clean = line.strip()
                sep_location = line_clean.find(":")

                while sep_location != -1:

                    try:  # find the standard name in the _META_DICT dictionary
                        name = next(k for k, v in _META_DICT.items() if k == v.get('text', None))
                    except StopIteration:  # Discard unknown pairs
                        continue

                    line_clean = line_clean[sep_location:]
                    sep_location = line_clean.find(":")

                # TODO Are quantachrome files always saved with these mistakes?
                # for i, d in enumerate(data):
                #     for mistake in ["Operator:", "Filename:", "Comment:"]:
                #         if re.search(r"\w+" + mistake, d):
                #             data[i] = d.split(mistake)[0]
                #             data.insert(i + 1, mistake)

                data_dict = {data[i][:-1].lower(): data[i + 1] for i in range(0, len(data), 2)}

                for key, val in data_dict.items():
                    try:  # find the standard name in the _META_DICT dictionary
                        name = next(k for k, v in _META_DICT.items() if key == v.get('text', None))
                    except StopIteration:  # Discard unknown pairs
                        continue
                    meta[name] = val

            elif "Press" in line:
                # get the adsorption data

                file_headers = re.split(r"\s{2,}", line.strip())
                print(file_headers)
                for h in file_headers:
                    txt = next((_DATA_DICT[a] for a in _DATA_DICT if h.lower().startswith(a)), h)
                    print(txt)
                    head.append(txt)

                # skip line
                file.readline()
                file.readline()

                units = re.split(r"\s{2,}", line)
                # TODO handle units
                print(f"Units are {units}")

                # skip line
                file.readline()
                file.readline()

                while line:
                    data.append(list(map(float, line.split())))
                    line = file.readline()

    # Set extra metadata
    meta['mass'] = meta['mass'].split()[0]
    meta['temperature'] = meta['temperature'].split()[0]
    meta['temperature_unit'] = "K"
    meta['pressure_unit'] = "torr"
    meta['loading_unit'] = "mmol"
    meta['material_unit'] = "g"
    meta['date'] = dateutil.parser.parse(meta['date']).isoformat()

    # amount adsorbed from cc to mmol/g
    data = dict(zip(head, map(lambda *x: list(x), *data)))
    data['loading'] = data['loading'] / float(meta['mass']) / 22.414

    return meta, data
