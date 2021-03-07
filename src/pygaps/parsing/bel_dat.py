"""Interface with BEL-generated DAT files."""

from datetime import datetime
from io import StringIO

import pandas

from ..core.pointisotherm import PointIsotherm

_FIELDS = {
    'material': {
        # TODO Are we sure that comment1 is always the material?
        'text': ['comment1'],
        'name': 'material',
    },
    'adsorbate': {
        'text': ['adsorptive'],
        'name': 'adsorbate',
    },
    'temperature': {
        'text': ['meas. temp'],
        'name': 'temperature',
    },
    'user': {
        'text': ['comment2'],
        'name': 'user',
    },
    'serialnumber': {
        'text': ['instrument'],
        'name': 'serialnumber',
    },
    'mass': {
        'text': ['sample weight'],
        'name': 'mass',
    },
    'exp_param1': {
        'text': ['comment3'],
        'name': 'exp_param1',
    },
    'exp_param2': {
        'text': ['comment4'],
        'name': 'exp_param2',
    },
    'date': {
        'text': ['date of measurement'],
        'name': 'date',
    },
    'time': {
        'text': ['time of measurement'],
        'name': 'time',
    },
    'cell_volume': {
        'text': ['vs/'],
        'name': 'cell_volume',
    },
    'isotherm_data': {
        'no.': 'measurement',
        'pe/': 'pressure',
        'p0/': 'pressure_saturation',
        'vd/': 'deadvolume',
        'v/': 'loading',
        'n/': 'loading',
    }
}


def isotherm_from_bel(path):
    """
    Get the isotherm and sample data from a BEL Japan .dat file.
    Parameters
    ----------
    path : str
        Path to the file to be read.
    Returns
    -------
    dataDF
    """
    with open(path) as file:
        line = file.readline().rstrip()
        meta = {}
        data = StringIO()

        while line != '':
            values = line.split(sep='\t')
            line = file.readline().rstrip()
            if len(values) < 2:  # If "title" section

                # read adsorption section
                if values[0].strip().lower().startswith('adsorption data'):
                    line = file.readline().rstrip()  # header
                    file_headers = line.replace('"', '').split('\t')
                    new_headers = ['branch']

                    for h in file_headers:
                        txt = next((
                            _FIELDS['isotherm_data'][a]
                            for a in _FIELDS['isotherm_data']
                            if h.lower().startswith(a)
                        ), h)
                        new_headers.append(txt)

                        if txt == 'loading':
                            meta['loading_basis'] = 'molar'
                            for (u, c) in (
                                ('/mmol', 'mmol'),
                                ('/mol', 'mol'),
                                ('/ml(STP)', 'cm3(STP)'),
                                ('/cm3(STP)', 'cm3(STP)'),
                            ):
                                if u in h:
                                    meta['loading_unit'] = c
                            meta['material_basis'] = 'mass'
                            for (u, c) in (
                                ('g-1', 'g'),
                                ('kg-1', 'kg'),
                            ):
                                if u in h:
                                    meta['material_unit'] = c

                        if txt == 'pressure':
                            meta['pressure_mode'] = 'absolute'
                            for (u, c) in (
                                ('/mmHg', 'torr'),
                                ('/torr', 'torr'),
                                ('/kPa', 'kPa'),
                                ('/bar', 'bar'),
                            ):
                                if u in h:
                                    meta['pressure_unit'] = c

                    data.write('\t'.join(new_headers) + '\n')

                    line = file.readline()  # firstline
                    while not line.startswith('0'):
                        data.write('False\t' + line)
                        line = file.readline()

                # read desorption section
                elif values[0].strip().lower().startswith('desorption data'):
                    file.readline()  # header - discard
                    line = file.readline()  # firstline
                    while not line.startswith('0'):
                        data.write('True\t' + line)
                        line = file.readline()

                else:
                    continue

            else:
                values = [v.strip('"') for v in values]
                key = values[0].lower()
                try:
                    field = next(
                        v for k, v in _FIELDS.items()
                        if any([key.startswith(n) for n in v.get('text', [])])
                    )
                except StopIteration:
                    continue
                meta[field['name']] = values[1]

    # Read prepared table
    data.seek(0)  # Reset string buffer to 0
    data_df = pandas.read_csv(data, sep='\t')
    data_df.dropna(inplace=True, how='all', axis='columns')

    # Set extra metadata
    meta['date'] = datetime.strptime(meta['date'], r'%y/%m/%d').isoformat()
    meta['apparatus'] = 'BEL ' + meta["serialnumber"]
    meta['loading_key'] = 'loading'
    meta['pressure_key'] = 'pressure'
    meta['other_keys'] = sorted([
        a for a in data_df.columns
        if a not in ['loading', 'pressure', 'measurement', 'branch']
    ])

    return PointIsotherm(isotherm_data=data_df, **meta)
