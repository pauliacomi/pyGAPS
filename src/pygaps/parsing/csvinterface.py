"""
This module contains the csv interface.
"""

import pandas

from ..classes.pointisotherm import PointIsotherm


def isotherm_to_csv(isotherm, path, separator=','):
    '''

    A function that turns the isotherm into a csv
    file with the data and properties.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to be written to csv.
    path : str
        Path to the file to be written.
    separator : str, optional
        Separator used int the csv file. Defaults to '',''.

    '''

    with open(path, mode='w') as file:

        isotherm_data = isotherm.to_dict()
        isotherm_data.pop('id', None)         # make sure id is not passed

        file.writelines([x + separator + str(y) + '\n'
                         for (x, y) in isotherm_data.items()])

        file.write('data\n')

        # get headings in an ordered way
        headings = [
            isotherm.loading_key,
            isotherm.pressure_key,
        ]
        headings.extend(isotherm.other_keys)
        data = isotherm.data()[headings]

        file.write(data.to_csv(None, sep=separator, index=False, header=True))

    return


def isotherm_from_csv(path, separator=','):
    """
    A function that will get the experiment and sample data from a csv file
    file and return the isotherm object.

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

        while line != 'data':
            values = line.split(sep=separator)
            sample_info.update({values[0]: values[1]})
            line = file.readline().rstrip()

        data_df = pandas.read_csv(file, sep=separator)

        loading_key = 'loading'
        pressure_key = 'pressure'
        other_keys = []

        for column in data_df.columns:
            if loading_key in column:
                data_df.rename(
                    index=str, columns={column: loading_key}, inplace=True)
            elif pressure_key in column:
                data_df.rename(
                    index=str, columns={column: pressure_key}, inplace=True)
            else:
                other_keys.append(column)

    isotherm = PointIsotherm(
        data_df,
        loading_key=loading_key,
        pressure_key=pressure_key,
        other_keys=other_keys,
        **sample_info)

    return isotherm
