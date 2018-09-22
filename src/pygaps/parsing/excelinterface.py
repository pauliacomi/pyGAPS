# %%

"""
This module contains the excel interface for returning data in all formats
used, such as the parser file.
"""

import pandas
import xlrd
import xlwt

from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
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
        'name': 'pressure_mode',
        'row': 4,
        'column': 0,
    },
    'pressure_unit': {
        'text': ['Pressure unit'],
        'name': 'pressure_unit',
        'row': 5,
        'column': 0,
    },
    'loading_basis': {
        'text': ['Loading basis'],
        'name': 'loading_basis',
        'row': 6,
        'column': 0,
    },
    'loading_unit': {
        'text': ['Loading unit'],
        'name': 'loading_unit',
        'row': 7,
        'column': 0,
    },
    'adsorbent_basis': {
        'text': ['Adsorbent basis'],
        'name': 'adsorbent_basis',
        'row': 8,
        'column': 0,
    },
    'adsorbent_unit': {
        'text': ['Adsorbent unit'],
        'name': 'adsorbent_unit',
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
    'sample_name': {'row': 3, 'column': 0},
    'sample_batch': {'row': 4, 'column': 0},
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
    't_exp': {'row': 7, 'column': 0},
    'adsorbate': {'row': 8, 'column': 0},
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
    'pressure_mode':    {'row': 0, 'column': 2},
    'pressure_unit':    {'row': 1, 'column': 2},
    'loading_basis':    {'row': 2, 'column': 2},
    'loading_unit':     {'row': 3, 'column': 2},
    'adsorbent_basis':  {'row': 4, 'column': 2},
    'adsorbent_unit':   {'row': 5, 'column': 2},
    'henry_constant':   {'row': 13, 'column': 0, 'text': ["Constante d'Henry"]},
    'langmuir_n1':      {'row': 14, 'column': 0, 'text': ["Langmuir N1"]},
    'langmuir_b1':      {'row': 15, 'column': 0, 'text': ["Langmuir B1"]},
    'langmuir_n2':      {'row': 16, 'column': 0, 'text': ["Langmuir N2"]},
    'langmuir_b2':      {'row': 17, 'column': 0, 'text': ["Langmuir B2"]},
    'langmuir_n3':      {'row': 18, 'column': 0, 'text': ["Langmuir N3"]},
    'langmuir_b3':      {'row': 19, 'column': 0, 'text': ["Langmuir B3"]},
    'langmuir_r2':      {'row': 20, 'column': 0, 'text': ["Langmuir R2"]},
    'c1':               {'row': 21, 'column': 0, 'text': ["C1"]},
    'c2':               {'row': 22, 'column': 0, 'text': ["C2"]},
    'c3':               {'row': 23, 'column': 0, 'text': ["C3"]},
    'c4':               {'row': 24, 'column': 0, 'text': ["C4"]},
    'c5':               {'row': 25, 'column': 0, 'text': ["C5"]},
    'c6':               {'row': 26, 'column': 0, 'text': ["C6"]},
    'c_m':              {'row': 27, 'column': 0, 'text': ["C_m"]},
    'isotherm data':    {'row': 28, 'column': 0},
}
_FIELDS_MADIREL_ENTH = {
    'enth_0':           {'row': 29, 'column': 0, 'text': ["Enthalpie à zéro"]},
    'enth_a':           {'row': 30, 'column': 0, 'text': ["Polynome Enthalpie A"]},
    'enth_b':           {'row': 31, 'column': 0, 'text': ["Polynome Enthalpie B"]},
    'enth_c':           {'row': 32, 'column': 0, 'text': ["Polynome Enthalpie C"]},
    'enth_d':           {'row': 33, 'column': 0, 'text': ["Polynome Enthalpie D"]},
    'enth_e':           {'row': 34, 'column': 0, 'text': ["Polynome Enthalpie E"]},
    'enth_f':           {'row': 35, 'column': 0, 'text': ["Polynome Enthalpie F"]},
    'enth_r2':          {'row': 36, 'column': 0, 'text': ["Polynome Enthalpie R2"]},
    'isotherm data':    {'row': 37, 'column': 0},
}

_FORMATS = ['bel', 'mic', 'MADIREL']


def _update_recurs(dict1, dict2):
    "Update a dictionary with one level down"
    for f in dict2:
        if f in dict1:
            dict1[f].update(dict2[f])
        else:
            dict1[f] = dict2[f]


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

    if fmt:
        if fmt not in _FORMATS:
            raise ParsingError('Format not supported')

    # create a new workbook and select first sheet
    wb = xlwt.Workbook()
    sht = wb.add_sheet('data')

    # get the required dictionaries
    fields = _FIELDS.copy()
    iso_dict = isotherm.to_dict()
    iso_dict.pop('id', None)         # make sure id is not passed

    if fmt == 'MADIREL':
        _update_recurs(fields, _FIELDS_MADIREL)

        if 'exp_type' in fields:
            if isotherm.exp_type.lower() == "isotherm":
                iso_dict['exp_type'] = 'Isotherme'
            elif isotherm.exp_type.lower() == "calorimetry":
                iso_dict['exp_type'] = 'Calorimetrie'
                _update_recurs(fields, _FIELDS_MADIREL_ENTH)
        if 'is_real' in fields:
            if isotherm.is_real is True:
                iso_dict['is_real'] = 'Experience'
            elif isotherm.is_real is False:
                iso_dict['is_real'] = 'Simulation'

    # Add the required named properties
    prop_style = xlwt.easyxf(
        'align: horiz left; pattern: pattern solid, fore_colour grey25;')
    for field in fields:
        val = iso_dict.pop(field, None)
        sht.write(fields[field]['row'],
                  fields[field]['column'],
                  fields[field]['text'][0],
                  prop_style)
        sht.write(fields[field]['row'],
                  fields[field]['column'] + 1,
                  val, prop_style)

    # Find the data row
    data_row = max([fields[f]['row'] for f in fields]) + 1

    # Generate the headings
    headings = [isotherm.loading_key, isotherm.pressure_key]
    headings.extend(isotherm.other_keys)

    # if fmt == 'MADIREL':
    #     headings = ['Pressure(bar)', 'Qte adsorbed(mmol/g)']
    #     if any(x.lower().startswith('enthalpy') for x in isotherm.other_keys):
    #         headings.append('Enthalpy(kJ/mol)')

    # Write all data
    col_width = 256 * 25              # 25 characters wide (-ish)
    for col_index, heading in enumerate(headings):
        sht.write(data_row,
                  col_index,
                  heading)
        sht.col(col_index).width = col_width
        for row_index, datapoint in enumerate(isotherm.data()[heading]):
            sht.write(data_row + row_index + 1,
                      col_index,
                      datapoint)

    # Now add the other keys
    sht = wb.add_sheet('otherdata')
    row = 0
    col = 0
    for prop in iso_dict:
        sht.write(row, col, prop)
        sht.write(row, col + 1, iso_dict[prop])
        row += 1

    wb.save(path)

    return


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

    if fmt:
        if fmt not in _FORMATS:
            raise ParsingError('Format not supported')

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

        experiment_data_df = pandas.DataFrame({
            pressure_key: sample_info.pop(pressure_key)['relative'],
            loading_key: sample_info.pop(loading_key),
        })

        branch_data = sample_info.pop('measurement')

    else:
        # Get excel workbook and sheet
        wb = xlrd.open_workbook(path)
        sht = wb.sheet_by_name('data')

        # get the required dictionaries
        fields = _FIELDS.copy()

        if fmt == 'MADIREL':
            _update_recurs(fields, _FIELDS_MADIREL)

            if sht.cell(fields['exp_type']['row'],
                        fields['exp_type']['column'] + 1).value == 'Calorimetrie':
                _update_recurs(fields, _FIELDS_MADIREL_ENTH)

        # read the main isotherm parameters
        for field in fields:
            sample_info[field] = sht.cell(fields[field]['row'],
                                          fields[field]['column'] + 1).value

        # find data limits
        header_row = fields['isotherm data']['row'] + 1
        start_row = header_row + 1
        final_row = start_row

        while final_row < sht.nrows:
            point = sht.cell(final_row, 0).value
            if not point:
                break
            final_row += 1

        # read the data in
        header_col = 0
        headers = []
        experiment_data = {}
        while header_col < sht.ncols:
            header = sht.cell(header_row, header_col).value
            if not header:
                break
            headers.append(header)
            experiment_data[header] = [sht.cell(i, header_col).value for i in range(start_row, final_row)]
            header_col += 1
        loading_key = headers[0]
        pressure_key = headers[1]
        other_keys = headers[2:]

        experiment_data_df = pandas.DataFrame(experiment_data)

        # read the secondary isotherm parameters
        sht = wb.sheet_by_name('otherdata')
        if sht:
            row_index = 0
            while row_index < sht.nrows:
                prop = sht.cell(row_index, 0).value
                if not prop:
                    break
                sample_info[prop] = sht.cell(row_index, 1).value
                row_index += 1

        # Put data in order
        sample_info.pop('isotherm data')    # remove useless field
        sample_info.pop('id', None)         # make sure id is not passed
        pressure_mode = sample_info.pop('pressure_mode')
        pressure_unit = sample_info.pop('pressure_unit')
        loading_basis = sample_info.pop('loading_basis')
        adsorbent_basis = sample_info.pop('adsorbent_basis')

        if fmt == 'MADIREL':
            if sample_info['is_real'] == "Experience":
                sample_info['is_real'] = True
            elif sample_info['is_real'] == "Simulation":
                sample_info['is_real'] = False
            if sample_info['exp_type'] == 'Isotherme':
                sample_info['exp_type'] = 'isotherm'
            elif sample_info['exp_type'] == 'Calorimetrie':
                sample_info['exp_type'] = 'calorimetry'

    isotherm = PointIsotherm(
        experiment_data_df,
        loading_key=loading_key,
        pressure_key=pressure_key,
        other_keys=other_keys,

        pressure_unit=pressure_unit,
        pressure_mode=pressure_mode,
        loading_basis=loading_basis,
        adsorbent_basis=adsorbent_basis,
        branch=branch_data,

        **sample_info)

    return isotherm
