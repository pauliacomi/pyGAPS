"""
This module contains the bel interface.
"""

from io import StringIO

import pandas

from ..classes.pointisotherm import PointIsotherm

_DATA = {
    'adsorptive': 'adsorbate',
    'meas. temp': 't_exp',
    'sample weight': 'mass',
    'comment1': 'sample_name',
    'comment2': 'user',
    'comment3': 'comment',
    'comment4': 'exp_param',
    'date of measurement': 'date',
    'time of measurement': 'time',
    'vs/': 'cell_volume',
    'isotherm_data': {
        'no.': 'measurement',
        'pe/': 'pressure',
        'p0/': 'saturation',
        'vd/': 'deadvolume',
        'v/': 'loading',
        'n/': 'loading',
    }
}


def isotherm_from_bel(path):
    """
    A function that will get the experiment and sample data
    from a BEL Japan .dat file and return the isotherm object.

    Parameters
    ----------
    path : str
        Path to the file to be read.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the dat file.
    """

    with open(path) as file:
        line = file.readline().rstrip()
        sample_info = {}
        adsdata = StringIO()

        while line != '':
            values = line.split(sep='\t')
            line = file.readline().rstrip()
            if len(values) < 2:
                if values[0].strip().lower().startswith('adsorption data'):
                    line = file.readline()          # header
                    line = line.replace('"', '')    # remove quotes
                    line = line.replace('\n', '')   # remove endline
                    headers = line.split('\t')
                    new_headers = ['br']

                    for h in headers:
                        txt = next((_DATA['isotherm_data'][a]
                                    for a in _DATA['isotherm_data']
                                    if h.lower().startswith(a)), h)
                        new_headers.append(txt)

                        if txt == 'loading':
                            sample_info['loading_basis'] = 'molar'
                            for (u, c) in (('/mmol', 'mmol'),
                                           ('/mol', 'mol'),
                                           ('/ml(STP)', 'cm3(STP)'),
                                           ('/cm3(STP)', 'cm3(STP)')):
                                if u in h:
                                    sample_info['loading_unit'] = c
                            sample_info['adsorbent_basis'] = 'mass'
                            for (u, c) in (('g-1', 'g'),
                                           ('kg-1', 'kg')):
                                if u in h:
                                    sample_info['adsorbent_unit'] = c

                        if txt == 'pressure':
                            sample_info['pressure_mode'] = 'absolute'
                            for (u, c) in (('/kPa', 'kPa'),
                                           ('/Pa', 'Pa')):
                                if u in h:
                                    sample_info['pressure_unit'] = c

                    adsdata.write('\t'.join(new_headers) + '\n')

                    line = file.readline()          # firstline
                    while not line.startswith('0'):
                        adsdata.write('False\t' + line)
                        line = file.readline()

                if values[0].strip().lower().startswith('desorption data'):
                    file.readline()                 # header - discard
                    line = file.readline()          # firstline
                    while not line.startswith('0'):
                        adsdata.write('True\t' + line)
                        line = file.readline()
                else:
                    continue
            else:
                values = [v.strip('"') for v in values]
                for n in _DATA:
                    if values[0].lower().startswith(n):
                        sample_info.update({_DATA[n]: values[1]})

        adsdata.seek(0)                 # Reset string buffer to 0
        data_df = pandas.read_table(adsdata,
                                    sep='\t')
        data_df.dropna(inplace=True, how='all', axis='columns')
        sample_info['date'] = (sample_info['date']
                               + ' ' +
                               sample_info.pop('time'))
        sample_info['sample_batch'] = 'bel'
        sample_info['loading_key'] = 'loading'
        sample_info['pressure_key'] = 'pressure'
        sample_info['other_keys'] = sorted([a for a in data_df.columns
                                            if a != 'loading'
                                            and a != 'pressure'
                                            and a != 'measurement'
                                            and a != 'br'])

        isotherm = PointIsotherm(
            data_df,
            branch=data_df['br'].tolist(),
            **sample_info)

    return isotherm
