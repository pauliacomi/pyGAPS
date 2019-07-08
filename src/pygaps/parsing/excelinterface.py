"""Parse to and from an Excel file format for isotherms."""

import ast

import pandas
import xlrd
import xlwt

from ..core.isotherm import Isotherm
from ..core.modelisotherm import ModelIsotherm
from ..core.pointisotherm import PointIsotherm
from ..modelling import get_isotherm_model
from ..utilities.exceptions import ParsingError
from .excel_bel_parser import read_bel_report
from .excel_mic_parser import read_mic_report

_FIELDS = {
    'material': {
        'text': ['Material name'],
        'name': 'material',
        'row': 0,
        'column': 0,
    },
    'material_batch': {
        'text': ['Material batch'],
        'name': 'material_batch',
        'row': 1,
        'column': 0,
    },
    'temperature': {
        'text': ['Experiment temperature (K)'],
        'name': 'temperature',
        'row': 2,
        'column': 0,
    },
    'adsorbate': {
        'text': ['Adsorbate used'],
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
    'isotherm_data': {
        'text': ['Isotherm type'],
        'name': 'isotherm_data',
        'row': 10,
        'column': 0,
    },
}


_FORMATS = ['bel', 'mic']


def _update_recurs(dict1, dict2):
    """Update a dictionary with one level down."""
    for f in dict2:
        if f in dict1:
            dict1[f].update(dict2[f])
        else:
            dict1[f] = dict2[f]


def isotherm_to_xl(isotherm, path):
    """
    Convert an isotherm into an excel file.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm to be written to excel.
    path : str
        Path to the file to be written.

    """
    # create a new workbook and select first sheet
    wb = xlwt.Workbook()
    sht = wb.add_sheet('data')

    # get the required dictionaries
    fields = _FIELDS.copy()
    iso_dict = isotherm.to_dict()

    # Add the required named properties
    prop_style = xlwt.easyxf(
        'align: horiz left; pattern: pattern solid, fore_colour grey25;')
    for field in fields:
        val = iso_dict.pop(field, None)
        sht.write(fields[field]['row'],
                  fields[field]['column'],
                  fields[field]['text'][0],
                  prop_style)
        if val:
            sht.write(fields[field]['row'],
                      fields[field]['column'] + 1,
                      val, prop_style)

    # Get the isotherm type header
    type_row = fields['isotherm_data']['row']
    type_col = fields['isotherm_data']['column']

    col_width = 256 * 25              # 25 characters wide (-ish)
    sht.col(type_col).width = col_width
    sht.col(type_col + 1).width = col_width

    if isinstance(isotherm, PointIsotherm):

        # Write the type
        sht.write(type_row, type_col + 1, 'data', prop_style)

        # Get the data row
        data_row = type_row + 1

        # Generate the headings
        headings = [isotherm.loading_key, isotherm.pressure_key]
        headings.extend(isotherm.other_keys)

        # We also write the branch data
        headings.append('branch')
        data = isotherm.data(raw=True)[headings]
        data['branch'] = data['branch'].replace(False, 'ads').replace(True, 'des')

        # Write all data
        for col_index, heading in enumerate(headings):
            sht.write(data_row,
                      col_index,
                      heading)
            for row_index, datapoint in enumerate(data[heading]):
                sht.write(data_row + row_index + 1,
                          col_index,
                          datapoint)

    if isinstance(isotherm, ModelIsotherm):

        # Write the type
        sht.write(type_row, type_col + 1, 'model', prop_style)

        # Get the model row
        model_row = type_row

        # Generate the headings (i know it's a lame way to do it)
        sht.write(model_row + 1, 0, 'Model name')
        sht.write(model_row + 1, 1, isotherm.model.name)
        sht.write(model_row + 2, 0, 'RMSE')
        sht.write(model_row + 2, 1, isotherm.model.rmse)
        sht.write(model_row + 3, 0, 'Pressure range')
        sht.write(model_row + 3, 1, str(isotherm.model.pressure_range))
        sht.write(model_row + 4, 0, 'Loading range')
        sht.write(model_row + 4, 1, str(isotherm.model.loading_range))
        sht.write(model_row + 5, 0, 'Model parameters')
        model_row = model_row + 5
        for row_index, param in enumerate(isotherm.model.params):
            sht.write(model_row + row_index + 1, 0, param)
            sht.write(model_row + row_index + 1, 1, isotherm.model.params[param])

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


def isotherm_from_xl(path, fmt=None, **isotherm_parameters):
    """
    Load an isotherm from an Excel file.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    fmt : {None, 'mic', 'bel'}, optional
        The format of the import for the isotherm.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the excel file.

    """
    if fmt:
        if fmt not in _FORMATS:
            raise ParsingError('Format not supported')

    # isotherm type
    isotype = 0

    raw_dict = {
        'pressure_key': 'pressure',
        'loading_key': 'loading',
        'branch': 'guess',
    }

    if fmt == 'mic':
        isotype = 1
        raw_dict.update(read_mic_report(path))

        # Add required props
        raw_dict['material_batch'] = 'mic'
        raw_dict['pressure_mode'] = 'relative'
        raw_dict['pressure_unit'] = 'kPa'
        raw_dict['loading_basis'] = 'molar'
        raw_dict['adsorbent_basis'] = 'mass'

        data = pandas.DataFrame({
            raw_dict['pressure_key']: raw_dict.pop(raw_dict['pressure_key'])['relative'],
            raw_dict['loading_key']: raw_dict.pop(raw_dict['loading_key']),
        })

    elif fmt == 'bel':
        isotype = 1
        raw_dict.update(read_bel_report(path))

        # Add required props
        raw_dict['material_batch'] = 'bel'
        raw_dict['pressure_mode'] = 'relative'
        raw_dict['pressure_unit'] = None
        raw_dict['loading_basis'] = 'molar'
        raw_dict['adsorbent_basis'] = 'mass'
        raw_dict['branch'] = raw_dict.pop('measurement')

        data = pandas.DataFrame({
            raw_dict['pressure_key']: raw_dict.pop(raw_dict['pressure_key'])['relative'],
            raw_dict['loading_key']: raw_dict.pop(raw_dict['loading_key']),
        })

    else:
        # Get excel workbook and sheet
        wb = xlrd.open_workbook(path)
        if 'data' in wb.sheet_names():
            sht = wb.sheet_by_name('data')
        else:
            sht = wb.sheet_by_index(0)

        # get the required dictionaries
        fields = _FIELDS.copy()

        # read the main isotherm parameters
        for field in fields:
            raw_dict[field] = sht.cell(fields[field]['row'],
                                       fields[field]['column'] + 1).value

        # find data/model limits
        type_row = fields['isotherm_data']['row']

        if sht.cell(type_row, 1).value.lower().startswith('data'):

            # Store isotherm type
            isotype = 1

            header_row = type_row + 1
            start_row = header_row + 1
            final_row = start_row

            while final_row < sht.nrows:
                point = sht.cell(final_row, 0).value
                if point == '':
                    break
                final_row += 1

            # read the data in
            header_col = 0
            headers = []
            experiment_data = {}
            while header_col < sht.ncols:
                header = sht.cell(header_row, header_col).value
                if header == '':
                    break
                headers.append(header)
                experiment_data[header] = [sht.cell(i, header_col).value for i in range(start_row, final_row)]
                header_col += 1
            data = pandas.DataFrame(experiment_data)

            raw_dict['loading_key'] = headers[0]
            raw_dict['pressure_key'] = headers[1]
            raw_dict['other_keys'] = [column for column in data.columns.values
                                      if column not in [raw_dict['loading_key'], raw_dict['pressure_key'], 'branch']]

            # process isotherm branches if they exist
            if 'branch' in data.columns:
                raw_dict['branch'] = data['branch'].replace('ads', False).replace('des', True).values

        if sht.cell(type_row, 1).value.lower().startswith('model'):

            # Store isotherm type
            isotype = 2

            new_mod = get_isotherm_model(sht.cell(type_row + 1, 1).value)
            new_mod.rmse = sht.cell(type_row + 2, 1).value
            new_mod.pressure_range = ast.literal_eval(sht.cell(type_row + 3, 1).value)
            new_mod.loading_range = ast.literal_eval(sht.cell(type_row + 4, 1).value)

            final_row = type_row + 6

            model_param = {}

            while final_row < sht.nrows:
                point = sht.cell(final_row, 0).value
                if point == '':
                    break
                model_param[point] = sht.cell(final_row, 1).value
                final_row += 1

            for param in new_mod.params:
                try:
                    new_mod.params[param] = model_param[param]
                except KeyError as err:
                    raise KeyError("The JSON is missing parameter '{0}'".format(param)) from err

        # read the secondary isotherm parameters
        if 'otherdata' in wb.sheet_names():
            sht = wb.sheet_by_name('otherdata')
            row_index = 0
            while row_index < sht.nrows:
                namec = sht.cell(row_index, 0)
                valc = sht.cell(row_index, 1)
                if namec.ctype == xlrd.XL_CELL_EMPTY:
                    break
                if valc.ctype == xlrd.XL_CELL_BOOLEAN:
                    val = bool(valc.value)
                elif valc.ctype == xlrd.XL_CELL_EMPTY:
                    val = None
                else:
                    val = valc.value
                raw_dict[namec.value] = val
                row_index += 1

        # Put data in order
        raw_dict.pop('isotherm_data')                      # remove useless field
        raw_dict.pop('iso_id', None)                       # make sure id is not passed

    # Update dictionary with any user parameters
    raw_dict.update(isotherm_parameters)

    if isotype == 1:
        return PointIsotherm(isotherm_data=data, **raw_dict)

    if isotype == 2:
        return ModelIsotherm(model=new_mod, **raw_dict)

    return Isotherm(**raw_dict)
