# %%

"""
This module contains the excel interface for returning data in all formats
used, such as the parser file.
"""

import os

import pandas

from ..classes.pointisotherm import PointIsotherm

# chose an implementation, depending on os
if os.name == 'nt':  # sys.platform == 'win32':
    import xlwings
else:
    print(
        "xlwings functionality disabled on this platform ( {0} )".format(os.name))


def isotherm_to_xl(isotherm, path, fmt=None):
    '''

    A function that turns the isotherm into an excel file with the data and properties.

    Parameters
    ----------
    isotherm : PointIsotherm
        Isotherm to be written to excel.
    path : str
        Path to the file to be written.
    fmt : {None, 'MADIREL'}, optional
        If the format is set to MADIREL, then the excel file is a specific version
        used by the MADIREL lab for internal processing.
    '''

    if xlwings is None:
        raise Warning(
            "xlwings functionality disabled on this platform ( {0} )".format(os.name))

    # create a new workbook and select first sheet
    wb = xlwings.Book()
    wb.app.screen_updating = False
    sht = wb.sheets[0]

    # write the isotherm paramterers
    if isotherm.is_real is True:
        is_real = "Experience"
    else:
        is_real = "Simulation"

    sht.range('A1').value = [
        ["Type manip", isotherm.exp_type],
        ["Experience ou Simulation", is_real],
        ["Date de l'expérience", isotherm.date],
        ["Nom de l'échantillon", isotherm.sample_name],
        ["Lot de l'échantillon", isotherm.sample_batch],
        ["Température d'activation (°C)", isotherm.t_act],
        ["Surnom de l'appareil", isotherm.machine],
        ["Température de l'expérience (K)", isotherm.t_exp],
        ["Formule chimique du gaz", isotherm.adsorbate],
        ["Surnom du contact", isotherm.user],
        ["Nom du labo", isotherm.lab],
        ["Nom du projet", isotherm.project],
    ]
    sht.range('E1').value = 'Comments'
    sht.range('E2').value = isotherm.comment

    sht.range('E1').value = 'Properties'
    rng_prop = 4
    for index, prop in enumerate(isotherm.other_properties):
        sht.range((5, rng_prop + index)).value = prop
        sht.range((6, rng_prop + index)
                  ).value = isotherm.other_properties.get(prop)

    delimiter_colour = (217, 217, 217)
    user_cells = (255, 199, 206)
    xlwings.Range('A1:B2').column_width = 30
    xlwings.Range('B1:B12').color = user_cells
    xlwings.Range('A13:B13').color = delimiter_colour

    # Write data
    if fmt is None:
        rng_data = 14
    elif fmt == 'MADIREL':
        if isotherm.exp_type == "isotherm":
            rng_data = 30
        elif isotherm.exp_type == "calorimetry":
            rng_data = 39
        else:
            raise Exception("Unknown data type")

    headings = [
        isotherm.loading_key,
        isotherm.pressure_key,
    ]
    headings.extend(isotherm.other_keys)

    data = isotherm.data()[headings]

    headings[0] = isotherm.loading_key + \
        '(' + isotherm.unit_loading + ')'
    headings[1] = isotherm.pressure_key + \
        '(' + isotherm.unit_pressure + ')'

    sht.range('A' + str(rng_data)).value = headings
    sht.range('A' + str(rng_data + 1)).value = data.as_matrix()

    # MADIREL specific
    if fmt == 'MADIREL':
        sht.range('A14').value = [
            ["Constante d'Henry", ],
            ["Langmuir N1", ],
            ["Langmuir B1", ],
            ["Langmuir N2", ],
            ["Langmuir B2", ],
            ["Langmuir N3", ],
            ["Langmuir B3", ],
            ["Langmuir R2", ],
            ["C1", ],
            ["C2", ],
            ["C3", ],
            ["C4", ],
            ["C5", ],
            ["C6", ],
            ["C_m", ],
        ]
        xlwings.Range('A29:B29').color = delimiter_colour

        if isotherm.exp_type == "calorimetry":
            sht.range('A30').value = [
                ["Enthalpie à zéro", ],
                ["Polynome Enthalpie A", ],
                ["Polynome Enthalpie B", ],
                ["Polynome Enthalpie C", ],
                ["Polynome Enthalpie D", ],
                ["Polynome Enthalpie E", ],
                ["Polynome Enthalpie F", ],
                ["Polynome Enthalpie R2", ],
            ]
            xlwings.Range('A38:C38').color = delimiter_colour
        else:
            raise Exception("Unknown data type")

    wb.save(path=path)
    wb.app.quit()

    return


def isotherm_from_xl(path, fmt=None):
    """
    A function that will get the experiment and sample data from a excel parser
    file and return the isotherm object.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    fmt : {None, 'MADIREL'}, optional
        If the format is set to MADIREL, then the excel file is a specific version
        used by the MADIREL lab for internal processing.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the excel file
    """

    if xlwings is None:
        raise Warning(
            "xlwings functionality disabled on this platform ( {0} )".format(os.name))

    # Get excel workbook, sheet and range
    wb = xlwings.Book(path)
    wb.app.screen_updating = False
    sht = wb.sheets[0]

    sample_info = {}

    # read the isotherm paramterers
    sample_info["exp_type"] = sht.range('B1').value

    is_real = sht.range('B2').value

    if is_real == "Experience":
        sample_info['is_real'] = True
    if is_real == "Simulation":
        sample_info['is_real'] = False

    sample_info['date'] = sht.range('B3').value
    sample_info['sample_name'] = sht.range('B4').value
    sample_info['sample_batch'] = sht.range('B5').value
    sample_info['t_act'] = sht.range('B6').value
    sample_info['machine'] = sht.range('B7').value
    sample_info['t_exp'] = sht.range('B8').value
    sample_info['adsorbate'] = sht.range('B9').value
    sample_info['user'] = sht.range('B10').value
    sample_info['lab'] = sht.range('B11').value
    sample_info['project'] = sht.range('B12').value

    sample_info['comment'] = sht.range('E2').value

    rng_prop = 4
    while True:
        prop = sht.range((5, rng_prop)).value
        if prop is None:
            break
        sample_info[prop] = sht.range((6, rng_prop)).value
        rng_prop += 1

    # read the data in

    if fmt is None:
        rng_data = 14
    elif fmt == 'MADIREL':
        if sample_info["exp_type"] == "isotherm":
            rng_data = 30
        elif sample_info["exp_type"] == "calorimetry":
            rng_data = 39
        else:
            raise Exception("Unknown data type")

    experiment_data_df = sht.range('A' + str(rng_data)).options(
        pandas.DataFrame, expand='table', index=0).value

    loading_key = 'loading'
    pressure_key = 'pressure'
    other_keys = []

    for column in experiment_data_df.columns:
        if loading_key in column:
            experiment_data_df.rename(
                index=str, columns={column: loading_key}, inplace=True)
        elif pressure_key in column:
            experiment_data_df.rename(
                index=str, columns={column: pressure_key}, inplace=True)
        else:
            other_keys.append(column)

    wb.app.quit()

    isotherm = PointIsotherm(
        experiment_data_df,
        loading_key=loading_key,
        pressure_key=pressure_key,
        other_keys=other_keys,
        **sample_info)

    return isotherm
