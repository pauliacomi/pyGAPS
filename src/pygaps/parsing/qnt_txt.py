"""Parse Quantachrome txt output files."""

import re

import dateutil.parser
import numpy as np
import pandas

from ..core.pointisotherm import PointIsotherm

_FIELDS = {
    'material': {
        'text': ['Sample ID'],
        'name': 'material',
    },
    'adsorbate': {
        'text': ['Analysis gas'],
        'name': 'adsorbate',
    },
    'temperature': {
        'text': ['Bath temp.'],
        'name': 'temperature',
    },
    'user': {
        'text': ['Operator'],
        'name': 'user',
    },
    'apparatus': {
        'text': ['Instrument:'],
        'name': 'apparatus',
    },
    'mass': {
        'text': ['Sample Weight'],
        'name': 'mass',
    },
    'date': {
        'text': ['Date'],
        'name': 'date',
    },
    'sample_description': {
        'text': ['Sample Desc'],
        'name': 'sample_description',
    },
    'analysis_time': {
        'text': ['Analysis Time'],
        'name': 'analysis_time',
    },
    'comment': {
        'text': ['Comment'],
        'name': 'comment',
    },
    'time_outgas': {
        'text': ['Outgas Time'],
        'name': 'time_outgas',
    },
    'nonideality': {
        'text': ['Non-ideality'],
        'name': 'nonideality',
    },
    'isotherm_data': {
        'press': 'pressure',
        'p0': 'pressure_saturation',
        'volume': 'loading',
        'time': 'measurement_time',
        'tol': 'tolerance',
        'equ': 'equilibrium',
    }
}


def parse(path):

    # load datafile
    with open(path, "r", encoding="ISO-8859-1") as fp:
        lines = fp.readlines()

    # get experimental and material parameters

    meta = {}
    columns = []
    raw_data = []

    for index, line in enumerate(lines):

        if any(
            v for k, v in _FIELDS.items()
            if any(t in line for t in v.get('text', []))
        ):
            data = re.split(r"\s{2,}|(?<=\D:)", line.strip())

            # TODO Are quantachrome files always saved with these mistakes?
            for i, d in enumerate(data):
                for mistake in ["Operator:", "Filename:", "Comment:"]:
                    if re.search(r"\w+" + mistake, d):
                        data[i] = d.split(mistake)[0]
                        data.insert(i + 1, mistake)

            for i, d in enumerate(data):
                name = next((
                    v.get('name', None)
                    for k, v in _FIELDS.items()
                    if any(t in d for t in v.get('text', []))
                ), None)
                if name not in meta:
                    if not data[i + 1].endswith(":"):
                        meta[name] = data[i + 1]
                    else:
                        meta[name] = ' '

        if "Press" in line:
            ads_start = (index + 4)

    # get the adsorption data

    for index, line in enumerate(lines):
        if index == ads_start - 4:
            file_headers = re.split(r"\s{2,}", line.strip())
            print(file_headers)
            for h in file_headers:
                txt = next((
                    _FIELDS['isotherm_data'][a]
                    for a in _FIELDS['isotherm_data']
                    if h.lower().startswith(a)
                ), h)
                print(txt)
                columns.append(txt)

        elif index == ads_start - 2:
            units = re.split(r"\s{2,}", line)
            # TODO handle units
            print(f"Units are {units}")

        elif index >= ads_start:
            raw_data.append(list(map(float, line.split())))

    data_df = pandas.DataFrame(np.array(raw_data).T, columns=data)

    # Set extra metadata
    meta['mass'] = meta['mass'].split()[0]
    meta['temperature'] = meta['temperature'].split()[0]
    meta['temperature_unit'] = "K"
    meta['pressure_unit'] = "torr"
    meta['loading_unit'] = "mmol"
    meta['material_unit'] = "g"
    meta['date'] = dateutil.parser.parse(meta['date']).isoformat()

    # amount adsorbed from cc to mmol/g
    data_df['loading'] = data_df['loading'] / float(meta['mass']) / 22.414

    return PointIsotherm(isotherm_data=data_df, **meta)
