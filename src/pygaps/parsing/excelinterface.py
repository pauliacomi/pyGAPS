# %%

"""
This module contains the excel interface for returning data in all formats
used, such as the parser file.
"""

import os

import pandas
import xlrd
import xlwt

from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
from ..utilities.unit_converter import find_basis
from ..utilities.unit_converter import find_mode
from .excel_bel_parser import read_bel_report
from .excel_mic_parser import read_mic_report

_FIELDS = {
    'sample_name': {
        'text': ['Sample name', "Nom de l'échantillon"],
        'name': 'sample_name',
        'row': 0,
        'column': 0,
    },
    'sample_batch': {
        'text': ['Sample batch', "Lot de l'échantillon"],
        'name': 'sample_batch',
        'row': 1,
        'column': 0,
    },
    't_exp': {
        'text': ['Experiment temperature (K)', "Température de l'expérience (K))"],
        'name': 't_exp',
        'row': 2,
        'column': 0,
    },
    'adsorbate': {
        'text': ['Adsorbate used', "Formule chimique du gaz"],
        'name': 'adsorbate',
        'row': 3,
        'column': 0,
    },
    'pressure_mode': {
        'text': ['Pressure mode'],
        'name': 'adsorbate',
        'row': 4,
        'column': 0,
    },
    'pressure_unit': {
        'text': ['Pressure unit'],
        'name': 'adsorbate',
        'row': 5,
        'column': 0,
    },
    'loading_basis': {
        'text': ['Loading basis'],
        'name': 'adsorbate',
        'row': 6,
        'column': 0,
    },
    'loading_unit': {
        'text': ['Loading unit'],
        'name': 'adsorbate',
        'row': 7,
        'column': 0,
    },
    'adsorbent_basis': {
        'text': ['Adsorbent basis'],
        'name': 'adsorbate',
        'row': 8,
        'column': 0,
    },
    'adsorbent_unit': {
        'text': ['Adsorbent unit'],
        'name': 'adsorbate',
        'row': 9,
        'column': 0,
    },
    'isotherm data': {
        'text': ['Isotherm data'],
        'name': 'isotherm data',
        'row': 10,
        'column': 0,
    },
}

_FIELDS_MADIREL = {
    'exp_type': {
        'text': ['Experiment type', "Type manip"],
        'name': 'exp_type',
        'row': 0,
        'column': 0,
    },
    'is_real': {
        'text': ['Simulation or experiment', "Experience ou Simulation"],
        'name': 'is_real',
        'row': 1,
        'column': 0,
    },
    'date': {
        'text': ['Date', "Date de l'expérience"],
        'name': 'date',
        'row': 2,
        'column': 0,
    },
    'sample_name': {
        'text': ['Sample name', "Nom de l'échantillon"],
        'name': 'sample_name',
        'row': 3,
        'column': 0,
    },
    'sample_batch': {
        'text': ['Sample batch', "Lot de l'échantillon"],
        'name': 'sample_batch',
        'row': 4,
        'column': 0,
    },
    't_act': {
        'text': ['Activation temperature (°C)', "Température d'activation (°C)"],
        'name': 't_act',
        'row': 5,
        'column': 0,
    },
    'machine': {
        'text': ['Apparatus', "Surnom de l'appareil"],
        'name': 'machine',
        'row': 6,
        'column': 0,
    },
    't_exp': {
        'text': ['Experiment temperature (K)', "Température de l'expérience (K))"],
        'name': 't_exp',
        'row': 7,
        'column': 0,
    },
    'adsorbate': {
        'text': ['Adsorbate used', "Formule chimique du gaz"],
        'name': 'adsorbate',
        'row': 8,
        'column': 0,
    },
    'user': {
        'text': ['User', "Surnom du contact"],
        'name': 'user',
        'row': 9,
        'column': 0,
    },
    'lab': {
        'text': ['Sample source name', "Nom du labo"],
        'name': 'lab',
        'row': 10,
        'column': 0,
    },
    'project': {
        'text': ['Project name', "Nom du projet"],
        'name': 'project',
        'row': 11,
        'column': 0,
    },
    'comment': {
        'text': ['Comments', "Commentaires"],
        'name': 'comment',
        'row': 12,
        'column': 1,
    },
    'henry_constant':   {'col': 1, 'row': 0, 'text': ["Constante d'Henry"]},
    'langmuir_n1':      {'col': 1, 'row': 0, 'text': ["Langmuir N1"]},
    'langmuir_b1':      {'col': 1, 'row': 0, 'text': ["Langmuir B1"]},
    'langmuir_n2':      {'col': 1, 'row': 0, 'text': ["Langmuir N2"]},
    'langmuir_b2':      {'col': 1, 'row': 0, 'text': ["Langmuir B2"]},
    'langmuir_n3':      {'col': 1, 'row': 0, 'text': ["Langmuir N3"]},
    'langmuir_b3':      {'col': 1, 'row': 0, 'text': ["Langmuir B3"]},
    'langmuir_r2':      {'col': 1, 'row': 0, 'text': ["Langmuir R2"]},
    'c1':               {'col': 1, 'row': 0, 'text': ["C1"]},
    'c2':               {'col': 1, 'row': 0, 'text': ["C2"]},
    'c3':               {'col': 1, 'row': 0, 'text': ["C3"]},
    'c4':               {'col': 1, 'row': 0, 'text': ["C4"]},
    'c5':               {'col': 1, 'row': 0, 'text': ["C5"]},
    'c6':               {'col': 1, 'row': 0, 'text': ["C6"]},
    'c_m':              {'col': 1, 'row': 0, 'text': ["C_m"]},
}


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

    # create a new workbook and select first sheet
    wb = xlwt.Workbook()

    if fmt is None:
        sht = wb.add_sheet('Data')

        iso_dict = isotherm.to_dict()

        # Add the required named properties
        for field in _FIELDS:
            val = iso_dict.pop(field, None)
            sht.write(_FIELDS[field]['row'],
                      _FIELDS[field]['column'],
                      _FIELDS[field]['text'][0])
            sht.write(_FIELDS[field]['row'],
                      _FIELDS[field]['column'] + 1,
                      val)

        # Find the data row
        data_row = max([_FIELDS[f]['row'] for f in _FIELDS]) + 1

        # Generate the headings
        headings = [isotherm.loading_key, isotherm.pressure_key]
        headings.extend(isotherm.other_keys)

        # Write all data
        for col_index, heading in enumerate(headings):
            sht.write(data_row,
                      col_index,
                      heading)
            for row_index, datapoint in enumerate(isotherm.data()[heading]):
                sht.write(data_row + row_index + 1,
                          col_index,
                          datapoint)

        # Now add the other keys
        sht = wb.add_sheet('OtherData')
        row = 0
        col = 0
        for prop in iso_dict:
            sht.write(row, col, prop)
            sht.write(row, col + 1, iso_dict[prop])
            row += 1

    wb.save(path)

    return
    # try:
    #     # write the isotherm parameters
    #     if isotherm.is_real is True:
    #         is_real = "Experience"
    #     else:
    #         is_real = "Simulation"

    #     exp_type = isotherm.exp_type
    #     if fmt == 'MADIREL':
    #         if isotherm.exp_type == "isotherm":
    #             exp_type = 'Isotherme'
    #         elif isotherm.exp_type == "calorimetry":
    #             exp_type = 'Calorimetrie'
    #         else:
    #             raise ParsingError("Unknown experiment type")

    #     sht.range('A1').value = [
    #         ["Type manip", exp_type],
    #         ["Experience ou Simulation", is_real],
    #         ["Date de l'expérience", isotherm.date],
    #         ["Nom de l'échantillon", isotherm.sample_name],
    #         ["Lot de l'échantillon", isotherm.sample_batch],
    #         ["Température d'activation (°C)", isotherm.t_act],
    #         ["Surnom de l'appareil", isotherm.machine],
    #         ["Température de l'expérience (K)", isotherm.t_exp],
    #         ["Formule chimique du gaz", isotherm.adsorbate],
    #         ["Surnom du contact", isotherm.user],
    #         ["Nom du labo", isotherm.lab],
    #         ["Nom du projet", isotherm.project],
    #     ]
    #     sht.range('E1').value = 'Comments'
    #     sht.range('E2').value = isotherm.comment

    #     sht.range('E1').value = 'Properties'
    #     rng_prop = 4
    #     for index, prop in enumerate(isotherm.other_properties):
    #         sht.range((5, rng_prop + index)).value = prop
    #         sht.range((6, rng_prop + index)
    #                   ).value = isotherm.other_properties.get(prop)

    #     delimiter_colour = (217, 217, 217)
    #     user_cells = (255, 199, 206)
    #     xlwings.Range('A1:B2').column_width = 30
    #     xlwings.Range('B1:B12').color = user_cells
    #     xlwings.Range('A13:B13').color = delimiter_colour

    #     # Write data
    #     if fmt is None:
    #         rng_data = 14
    #     elif fmt == 'MADIREL':
    #         if exp_type == "Isotherme":
    #             rng_data = 30
    #         elif exp_type == "Calorimetrie":
    #             rng_data = 39
    #         else:
    #             raise ParsingError("Unknown experiment type")

    #     headings = [
    #         isotherm.loading_key,
    #         isotherm.pressure_key,
    #     ]
    #     headings.extend(isotherm.other_keys)

    #     # Gets the data sorted in the correct order
    #     data = isotherm.data()[headings]

    #     if fmt == 'MADIREL':
    #         headings[0] = 'adsorbed' + '(' + isotherm.loading_unit + ')'
    #         headings[1] = 'Pressure' + '(' + isotherm.pressure_unit + ')'
    #     else:
    #         headings[0] = headings[0] + '(' + isotherm.loading_unit + '/'\
    #                                         + isotherm.adsorbent_unit + ')'
    #         if isotherm.pressure_mode == 'absolute':
    #             headings[1] = headings[1] + '(' + isotherm.pressure_unit + ')'
    #         else:
    #             headings[1] = headings[1] + '(p/p0)'

    #     sht.range('A' + str(rng_data)).value = headings
    #     sht.range('A' + str(rng_data + 1)).value = data.as_matrix()

    #     # MADIREL specific
    #     if fmt == 'MADIREL':
    #         sht.range('A14').value = [
    #             ["Constante d'Henry", ],
    #             ["Langmuir N1", ],
    #             ["Langmuir B1", ],
    #             ["Langmuir N2", ],
    #             ["Langmuir B2", ],
    #             ["Langmuir N3", ],
    #             ["Langmuir B3", ],
    #             ["Langmuir R2", ],
    #             ["C1", ],
    #             ["C2", ],
    #             ["C3", ],
    #             ["C4", ],
    #             ["C5", ],
    #             ["C6", ],
    #             ["C_m", ],
    #         ]
    #         xlwings.Range('A29:B29').color = delimiter_colour

    #         if exp_type == "Calorimetrie":
    #             sht.range('A30').value = [
    #                 ["Enthalpie à zéro", ],
    #                 ["Polynome Enthalpie A", ],
    #                 ["Polynome Enthalpie B", ],
    #                 ["Polynome Enthalpie C", ],
    #                 ["Polynome Enthalpie D", ],
    #                 ["Polynome Enthalpie E", ],
    #                 ["Polynome Enthalpie F", ],
    #                 ["Polynome Enthalpie R2", ],
    #             ]
    #             xlwings.Range('A38:C38').color = delimiter_colour
    #         else:
    #             raise ParsingError("Unknown data type")


def isotherm_from_xl(path, fmt=None):
    """
    A function that will get the experiment and sample data from a excel parser
    file and return the isotherm object.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    fmt : {None, 'mic', 'bel', 'MADIREL'}, optional
        The format of the import for the isotherm.

    Returns
    -------
    PointIsotherm
        The isotherm contained in the excel file.
    """
    if xlrd is None:
        raise ParsingError(
            "Excel functionality disabled on this platform ( {0} )".format(os.name))

    sample_info = {}
    loading_key = 'loading'
    pressure_key = 'pressure'
    other_keys = []
    branch_data = 'guess'

    if fmt == 'mic':
        sample_info = read_mic_report(path)
        sample_info['sample_batch'] = 'mic'

        pressure_mode = 'relative'
        pressure_unit = 'kPa'
        loading_basis = 'molar'
        adsorbent_basis = 'mass'
        units = ['cm3(STP)', 'g']

        experiment_data_df = pandas.DataFrame({
            pressure_key: sample_info.pop(pressure_key)['relative'],
            loading_key: sample_info.pop(loading_key),
        })
    elif fmt == 'bel':
        sample_info = read_bel_report(path)
        sample_info['sample_batch'] = 'bel'

        pressure_mode = 'relative'
        pressure_unit = 'kPa'
        loading_basis = 'molar'
        adsorbent_basis = 'mass'
        units = sample_info.pop('units')

        experiment_data_df = pandas.DataFrame({
            pressure_key: sample_info.pop(pressure_key)['relative'],
            loading_key: sample_info.pop(loading_key),
        })

        branch_data = sample_info.pop('measurement')

    else:

        # Get excel workbook and sheet
        wb = xlrd.open_workbook(path)
        sht = wb.sheet_by_index(0)

        for field in _FIELDS.keys():
            sample_info[field] = sht.cell(_FIELDS[field]['row'],
                                          _FIELDS[field]['col']).value

        # read the isotherm parameters

        if fmt == 'MADIREL':
            if sample_info['exp_type'] == "Isotherme":
                sample_info["exp_type"] = 'isotherm'
            elif sample_info['exp_type'] == "Calorimetrie":
                sample_info["exp_type"] = 'calorimetry'
            else:
                raise ParsingError("Unknown experiment type")

        if sample_info['is_real'] == "Experience":
            sample_info['is_real'] = True
        if sample_info['is_real'] == "Simulation":
            sample_info['is_real'] = False

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
        branch=branch_data,

        **sample_info)

    return isotherm
