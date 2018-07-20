"""
This module contains the csv interface.
"""

import pandas

from io import StringIO

from ..classes.pointisotherm import PointIsotherm

_DATA = {
    'adsorptive': 'adsorbent',
    'meas. temp': 't_exp',
    'sample weight': 'mass',
    'comment1': 'sample_name',
    'comment2': 'user',
    'comment3': 'comment',
    'comment4': 'exp_param',
    'date of measurement': 'date',
    'time of measurement': 'time',
}


def isotherm_from_bel(path):
    """
    A function that will get the experiment and sample data
    from a BEL Japan .dat file and return the isotherm object.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    separator : str, optional
        Separator used int the csv file. Defaults to '',''.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the csv file.
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
                    while not line.startswith('0'):
                        adsdata.write(line)
                        line = file.readline()
                if values[0].strip().lower().startswith('desorption data'):
                    file.readline()                 # header - discard
                    line = file.readline()          # firstline
                    while not line.startswith('0'):
                        adsdata.write(line)
                        line = file.readline()
                else:
                    continue
            else:
                values = [v.strip('"') for v in values]
                for n in _DATA:
                    if values[0].lower().startswith(n):
                        sample_info.update({_DATA[n]: values[1]})

        sample_info['date'] = (sample_info['date']
                               + ' ' +
                               sample_info['time'])

        with open('./data.txt', 'w') as file:
            file.write(adsdata.getvalue())
        data_df = pandas.read_table(adsdata, sep='\t')

    isotherm = PointIsotherm(
        data_df,
        loading_key=data_df.columns[0],
        pressure_key=data_df.columns[1],
        other_keys=list(data_df.columns[2:]),
        **sample_info)

    return isotherm
