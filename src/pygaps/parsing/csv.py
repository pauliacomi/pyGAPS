"""The csv parsing interface."""

import ast
from io import StringIO

import pandas

from pygaps.core.modelisotherm import Isotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.modelling import model_from_dict
from pygaps.utilities.exceptions import ParsingError


def _is_float(s):
    """Check if a value is a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_bool(s):
    """Check a value is a CSV bool."""
    if s == 'True' or s == 'False':
        return True
    else:
        return False


def _to_bool(s):
    """Convert a value into a CSV bool."""
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError('String cannot be converted to bool')


def _is_list(s):
    """Check a value is a CSV list."""
    if s[0] == '[' and s[-1] == ']':
        return True
    else:
        return False


def _from_list(s):
    """Convert a value into a CSV list."""
    # note that the function will fail if the list has other spaces
    return ast.literal_eval(s.replace(' ', ","))


def _to_string(s):
    """Convert a value into a CSV-safe string."""
    if isinstance(s, list):
        return '[' + ' '.join([str(x) for x in s]) + "]"
    return str(s)


def isotherm_to_csv(isotherm, path=None, separator=','):
    """
    Convert isotherm into a CSV representation.

    If the path is specified, the isotherm is saved as a file,
    otherwise it is returned as a string.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm to be written to csv.
    path : str, None
        Path to the file to be written.
    separator : str, optional
        Separator used int the csv file. Defaults to '',''.

    """
    output = StringIO()

    isotherm_data = isotherm.to_dict()

    output.writelines([
        x + separator + _to_string(y) + '\n'
        for (x, y) in isotherm_data.items()
    ])

    if isinstance(isotherm, PointIsotherm):

        # get headings in an ordered way
        headings = [
            isotherm.pressure_key,
            isotherm.loading_key,
        ]
        if isotherm.other_keys:
            headings.extend(isotherm.other_keys)

        # also get the branch data in a regular format
        headings.append('branch')
        data = isotherm.data_raw[headings]
        data['branch'] = data['branch'].replace(False,
                                                'ads').replace(True, 'des')

        output.write('data:[pressure,loading,[otherdata],branch data]\n')
        data.to_csv(output, sep=separator, index=False, header=True)

    elif isinstance(isotherm, ModelIsotherm):

        output.write('model:[name and parameters]\n')
        output.write(('name' + separator + isotherm.model.name + '\n'))
        output.write(
            ('rmse' + separator + _to_string(isotherm.model.rmse) + '\n')
        )
        output.write((
            'pressure range' + separator +
            _to_string(isotherm.model.pressure_range) + '\n'
        ))
        output.write((
            'loading range' + separator +
            _to_string(isotherm.model.loading_range) + '\n'
        ))
        output.writelines([
            param + separator + str(isotherm.model.params[param]) + '\n'
            for param in isotherm.model.params
        ])

    if path:
        with open(path, mode='w', newline='\n') as file:
            print(output.getvalue(), file=file)
    else:
        return output.getvalue()


def isotherm_from_csv(str_or_path, separator=',', **isotherm_parameters):
    """
    Load an isotherm from a CSV file.

    Parameters
    ----------
    str_or_path : str
        The isotherm in a CSV string format or a path
        to where one can be read.
    separator : str, optional
        Separator used int the csv file. Defaults to `,`.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the csv string or file.

    """
    try:
        with open(str_or_path) as f:
            raw_csv = StringIO(f.read())
    except OSError:
        try:
            raw_csv = StringIO(str_or_path)
        except Exception:
            raise ParsingError(
                "Could not parse JSON isotherm. "
                "The `str_or_path` is invalid or does not exist. "
            )

    line = raw_csv.readline().rstrip()
    raw_dict = {}

    try:
        while not (
            line.startswith('data') or line.startswith('model') or line == ""
        ):
            values = line.split(sep=separator)

            if _is_bool(values[1]):
                val = _to_bool(values[1])
            elif _is_float(values[1]):
                val = float(values[1])
            elif _is_list(values[1]):
                val = _from_list(values[1])
            else:
                val = values[1]
            raw_dict.update({values[0]: val})
            line = raw_csv.readline().rstrip()
    except:
        raise ParsingError(
            "Could not parse JSON isotherm. "
            "The `str_or_path` is invalid or does not exist. "
        )

    # Update dictionary with any user parameters
    raw_dict.update(isotherm_parameters)

    # Now read specific type of isotherm (Point, Model, Base)
    if line.startswith('data'):
        data = pandas.read_csv(raw_csv, sep=separator)

        # process isotherm branches if they exist
        if 'branch' in data.columns:
            data['branch'] = data['branch'].apply(
                lambda x: False if x == 'ads' else True
            )
        else:
            raw_dict['branch'] = 'guess'

        # generate other keys
        other_keys = [
            column for column in data.columns.values
            if column not in [data.columns[0], data.columns[1], 'branch']
        ]

        isotherm = PointIsotherm(
            isotherm_data=data,
            pressure_key=data.columns[0],
            loading_key=data.columns[1],
            other_keys=other_keys,
            **raw_dict
        )

    elif line.startswith('model'):

        model = {}
        line = raw_csv.readline().rstrip()
        model['name'] = line.split(sep=separator)[1]
        line = raw_csv.readline().rstrip()
        model['rmse'] = line.split(sep=separator)[1]
        line = raw_csv.readline().rstrip()
        model['pressure_range'] = _from_list(line.split(sep=separator)[1])
        line = raw_csv.readline().rstrip()
        model['loading_range'] = _from_list(line.split(sep=separator)[1])
        line = raw_csv.readline().rstrip()
        model['parameters'] = {}
        while line != "":
            values = line.split(sep=separator)
            model['parameters'][values[0]] = float(values[1])
            line = raw_csv.readline().rstrip()

        isotherm = ModelIsotherm(
            model=model_from_dict(model),
            **raw_dict,
        )

    else:
        isotherm = Isotherm(**raw_dict)

    return isotherm
