# %%

"""
This module contains the excel interface for returning data in all formats
used, such as the parser file.
"""

import os

import pandas

from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
from ..utilities.unit_converter import find_basis
from ..utilities.unit_converter import find_mode
from excel_mic_parser import read_mic_report
from excel_bel_parser import read_bel_report

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
        raise ParsingError(
            "xlwings functionality disabled on this platform ( {0} )".format(os.name))

    # create a new workbook and select first sheet
    try:
        wb = xlwings.Book()
    except Exception as e_info:
        raise SystemError(
            "Failed to connect to excel. Is it available?") from e_info

    wb.app.screen_updating = False
    sht = wb.sheets[0]

    try:
        # write the isotherm parameters
        if isotherm.is_real is True:
            is_real = "Experience"
        else:
            is_real = "Simulation"

        exp_type = isotherm.exp_type
        if fmt == 'MADIREL':
            if isotherm.exp_type == "isotherm":
                exp_type = 'Isotherme'
            elif isotherm.exp_type == "calorimetry":
                exp_type = 'Calorimetrie'
            else:
                raise ParsingError("Unknown experiment type")

        sht.range('A1').value = [
            ["Type manip", exp_type],
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
            if exp_type == "Isotherme":
                rng_data = 30
            elif exp_type == "Calorimetrie":
                rng_data = 39
            else:
                raise ParsingError("Unknown experiment type")

        headings = [
            isotherm.loading_key,
            isotherm.pressure_key,
        ]
        headings.extend(isotherm.other_keys)

        # Gets the data sorted in the correct order
        data = isotherm.data()[headings]

        if fmt == 'MADIREL':
            headings[0] = 'adsorbed' + '(' + isotherm.loading_unit + ')'
            headings[1] = 'Pressure' + '(' + isotherm.pressure_unit + ')'
        else:
            headings[0] = headings[0] + '(' + isotherm.loading_unit + '/'\
                                            + isotherm.adsorbent_unit + ')'
            if isotherm.pressure_mode == 'absolute':
                headings[1] = headings[1] + '(' + isotherm.pressure_unit + ')'
            else:
                headings[1] = headings[1] + '(p/p0)'

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

            if exp_type == "Calorimetrie":
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
                raise ParsingError("Unknown data type")

    finally:
        wb.save(path=path)
        wb.app.screen_updating = True
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
    fmt : {None, 'micromeritics', 'bel', 'MADIREL'}, optional
        The format of the import for the isotherm.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the excel file.
    """

    sample_info = {}

    if fmt == 'micromeritics':
        sample_info = read_mic_report(path)
        sample_info['sample_batch'] = 'mic'

        experiment_data_df = pandas.DataFrame({
            'pressure': sample_info.pop('pressure')['relative'],
            'loading': sample_info.pop('uptake'),
            'time': sample_info.pop('time')
        })
    elif fmt == 'bel':
        pass
    else:
        if xlwings is None:
            raise ParsingError(
                "xlwings functionality disabled on this platform ( {0} )".format(os.name))

        # Get excel workbook, sheet and range
        wb = xlwings.Book(path)
        wb.app.screen_updating = False
        sht = wb.sheets[0]

        try:

            # read the isotherm parameters
            exp_type = sht.range('B1').value
            sample_info["exp_type"] = exp_type

            if fmt == 'MADIREL':
                if exp_type == "Isotherme":
                    sample_info["exp_type"] = 'isotherm'
                elif exp_type == "Calorimetrie":
                    sample_info["exp_type"] = 'calorimetry'
                else:
                    raise ParsingError("Unknown experiment type")

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
                if exp_type == "Isotherme":
                    rng_data = 30
                elif exp_type == "Calorimetrie":
                    rng_data = 39
                else:
                    raise ParsingError("Unknown data type")

            experiment_data_df = sht.range('A' + str(rng_data)).options(
                pandas.DataFrame, expand='table', index=0).value

            loading_key = 'loading'
            pressure_key = 'pressure'
            s_loading_key = loading_key
            s_pressure_key = pressure_key
            if fmt == 'MADIREL':
                s_loading_key = 'adsorbed'
                s_pressure_key = 'pressure'
            other_keys = []

            for column in experiment_data_df.columns:
                if s_loading_key in column.lower():

                    # Rename with standard name
                    experiment_data_df.rename(
                        index=str, columns={column: loading_key}, inplace=True)

                    if not fmt:
                        # Get units
                        units = column[column.find(
                            '(') + 1:column.rfind(')')].split('/')
                        loading_basis = find_basis(units[0])
                        adsorbent_basis = find_basis(units[1])
                    elif fmt == 'MADIREL':
                        units = ['mmol', 'g']
                        loading_basis = 'molar'
                        adsorbent_basis = 'mass'

                elif s_pressure_key in column.lower():

                    # Rename with standard name
                    experiment_data_df.rename(
                        index=str, columns={column: pressure_key}, inplace=True)

                    if not fmt:
                        # Get units
                        pressure_unit = column[column.find(
                            '(') + 1:column.rfind(')')]
                        pressure_mode = find_mode(pressure_unit)
                    elif fmt == 'MADIREL':
                        pressure_unit = 'bar'
                        pressure_mode = 'absolute'

                else:
                    other_keys.append(column)
        finally:
            wb.app.screen_updating = True
            wb.app.quit()

    isotherm = PointIsotherm(
        experiment_data_df,
        loading_key=loading_key,
        pressure_key=pressure_key,
        other_keys=other_keys,

        pressure_unit=pressure_unit,
        pressure_mode=pressure_mode,
        loading_unit=units[0],
        loading_basis=loading_basis,
        adsorbent_unit=units[1],
        adsorbent_basis=adsorbent_basis,

        **sample_info)

    return isotherm
