# %%

"""
This module contains the excel interface for returning data in all formats
used, such as the parser file.
"""

import os
import os.path
import pandas
import numpy
# chose an implementation, depending on os
if os.name == 'nt':  # sys.platform == 'win32':
    import xlwings
else:
    print(
        "xlwings functionality disabled on this platform ( {0} )".format(os.name))


def xl_experiment_parser(path):
    '''

    A function that will get the experiment and sample data from a parser file.

    :param path: Path to the file being read

    '''

    if xlwings is None:
        raise Warning(
            "xlwings functionality disabled on this platform ( {0} )".format(os.name))
        return

    # get excel workbook, sheet and range
    wb = xlwings.Book(path)
    sht = wb.sheets[0]

    sample_info = {}

    sample_info["exp_type"] = sht.range('B1').value

    is_real = sht.range('B2').value

    if is_real == "Experience":
        sample_info['is_real'] = True
    if is_real == "Simulation":
        sample_info['is_real'] = False

    sample_info['id'] = ""
    sample_info['date'] = sht.range('B3').value
    sample_info['name'] = sht.range('B4').value
    sample_info['batch'] = sht.range('B5').value
    sample_info['t_act'] = sht.range('B6').value
    sample_info['machine'] = sht.range('B7').value
    sample_info['t_exp'] = sht.range('B8').value
    sample_info['gas'] = sht.range('B9').value
    sample_info['user'] = sht.range('B10').value
    sample_info['lab'] = sht.range('B11').value
    sample_info['project'] = sht.range('B12').value

    sample_info['comment'] = sht.range('E2').value

    if sample_info["exp_type"] == "Isotherme":
        experiment_data_arr = sht.range('A31').options(
            numpy.array, expand='table').value
        columns = ["Pressure (bar)", "Loading (mmol/g)"]
    elif sample_info["exp_type"] == "Calorimetrie":
        experiment_data_arr = sht.range('A41').options(
            numpy.array, expand='table').value
        columns = ["Pressure (bar)", "Loading (mmol/g)", "Enthalpy (kJ/mol)"]
    else:
        raise Exception("Unknown data type")

    experiment_data_df = pandas.DataFrame(experiment_data_arr, columns=columns)

    xlwings.apps[0].quit()

    return experiment_data_df, sample_info


def xl_experiment_parser_paths(folder):
    '''

    A function that will get the experiment and sample data from a parser file.

    :param folder: The folder where the function will look in

    '''

    if xlwings is None:
        raise Warning(
            "xlwings functionality disabled on this platform ( {0} )".format(os.name))
        return

    paths = []

    for root, _, files in os.walk(folder):
        for f in files:
            fullpath = os.path.join(root, f)
            ext = os.path.splitext(fullpath)[-1].lower()
            if ext == ".xlsx":
                paths.append(fullpath)

    return paths
