"""
Parse to and from a Excel format for isotherms.

The _parser_version variable documents any changes to the format,
and is used to check for any deprecations.

"""

import ast

import pandas
import xlrd
import xlwt

from pygaps import logger
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.modelling import model_from_dict
from pygaps.utilities.exceptions import ParsingError

_parser_version = "3.0"

_META_DICT = {
    'material': {
        'text': ('Material name', ),
        'name': 'material',
        'row': 0,
        'column': 0,
    },
    'temperature': {
        'text': ('Experiment temperature (K)', ),
        'name': 'temperature',
        'row': 1,
        'column': 0,
    },
    'adsorbate': {
        'text': ('Adsorbate used', ),
        'name': 'adsorbate',
        'row': 2,
        'column': 0,
    },
    'pressure_mode': {
        'text': ('Pressure mode', ),
        'name': 'pressure_mode',
        'row': 3,
        'column': 0,
    },
    'pressure_unit': {
        'text': ('Pressure unit', ),
        'name': 'pressure_unit',
        'row': 4,
        'column': 0,
    },
    'loading_basis': {
        'text': ('Loading basis', ),
        'name': 'loading_basis',
        'row': 5,
        'column': 0,
    },
    'loading_unit': {
        'text': ('Loading unit', ),
        'name': 'loading_unit',
        'row': 6,
        'column': 0,
    },
    'material_basis': {
        'text': ('Material basis', ),
        'name': 'material_basis',
        'row': 7,
        'column': 0,
    },
    'material_unit': {
        'text': ('Material unit', ),
        'name': 'material_unit',
        'row': 8,
        'column': 0,
    },
    'isotherm_data': {
        'text': ('Isotherm type', ),
        'name': 'isotherm_data',
        'row': 9,
        'column': 0,
    },
}


def isotherm_to_xl(isotherm, path):
    """
    Save an isotherm to an excel file.

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
    iso_dict = isotherm.to_dict()
    iso_dict['file_version'] = _parser_version  # version

    # Parse material
    material = iso_dict['material']
    if isinstance(material, dict):
        iso_dict['material'] = material.pop('name')
        iso_dict.update({f"_material_{key}": val for key, val in material.items()})

    # Add the required named properties
    prop_style = xlwt.easyxf('align: horiz left; pattern: pattern solid, fore_colour grey25;')
    for field in _META_DICT.values():
        val = iso_dict.pop(field['name'], None)
        sht.write(field['row'], field['column'], field['text'][0], prop_style)
        if val:
            sht.write(field['row'], field['column'] + 1, val, prop_style)

    # Get the isotherm type header
    type_row = _META_DICT['isotherm_data']['row']
    type_col = _META_DICT['isotherm_data']['column']

    col_width = 256 * 25  # 25 characters wide (-ish)
    sht.col(type_col).width = col_width
    sht.col(type_col + 1).width = col_width

    if isinstance(isotherm, PointIsotherm):

        # Write the type
        sht.write(type_row, type_col + 1, 'data', prop_style)

        # Get the data row
        data_row = type_row + 1

        # We get data and replace adsorption terminology
        data = isotherm.data_raw.copy()
        data['branch'] = data['branch'].replace(0, 'ads').replace(1, 'des')

        columns = [isotherm.pressure_key, isotherm.loading_key, 'branch'] + isotherm.other_keys

        # Write data types
        for col_index, heading in enumerate(isotherm.other_keys):
            sht.write(data_row - 1, col_index + 3, data[heading].dtype.name)

        # Write all data
        for col_index, heading in enumerate(columns):
            sht.write(data_row, col_index, heading)
            for row_index, datapoint in enumerate(data[heading]):
                sht.write(data_row + row_index + 1, col_index, datapoint)

    elif isinstance(isotherm, ModelIsotherm):

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
        sht.write(
            model_row + 3, 1,
            f'({isotherm.model.pressure_range[0]}, {isotherm.model.pressure_range[1]})'
        )
        sht.write(model_row + 4, 0, 'Loading range')
        sht.write(
            model_row + 4, 1,
            f'({isotherm.model.loading_range[0]}, {isotherm.model.loading_range[1]})'
        )
        sht.write(model_row + 5, 0, 'Model parameters')
        model_row = model_row + 5
        for row_index, param in enumerate(isotherm.model.params):
            sht.write(model_row + row_index + 1, 0, param)
            sht.write(model_row + row_index + 1, 1, isotherm.model.params[param])

    elif isinstance(isotherm, BaseIsotherm):
        # Write the type
        sht.write(type_row, type_col + 1, 'metadata', prop_style)

    else:
        raise ParsingError("Could not determine isotherm type")

    # Now add the other keys
    sht = wb.add_sheet('otherdata')
    row = 0
    col = 0
    for prop in iso_dict:
        sht.write(row, col, prop)
        sht.write(row, col + 1, iso_dict[prop])
        row += 1

    wb.save(path)


def isotherm_from_xl(path, *isotherm_parameters):
    """
    Load an isotherm from a pyGAPS Excel file.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the excel file.

    """

    # isotherm type (point/model)
    isotype = 0

    raw_dict = {}

    # Get excel workbook and sheet
    wb = xlrd.open_workbook(path)
    if 'data' in wb.sheet_names():
        sht = wb.sheet_by_name('data')
    else:
        sht = wb.sheet_by_index(0)

    # read the main isotherm parameters
    for field in _META_DICT.values():
        valc = sht.cell(field['row'], field['column'] + 1)
        if valc.ctype == xlrd.XL_CELL_EMPTY:
            val = None
        else:
            val = valc.value
        raw_dict[field['name']] = val

    # find data/model limits
    type_row = _META_DICT['isotherm_data']['row']

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
        dtypes = {}
        experiment_data = {}
        while header_col < sht.ncols:
            header = sht.cell(header_row, header_col).value
            if header == '':
                break
            # read header, data, and dtype
            headers.append(header)
            experiment_data[header] = [
                sht.cell(i, header_col).value for i in range(start_row, final_row)
            ]
            # read the data type
            # only read the data type if it is not a pressure, loading or branch
            if header_col > 2:
                dtype = sht.cell(header_row - 1, header_col).value
                if dtype != '':
                    dtypes[header] = dtype
            header_col += 1
        data = pandas.DataFrame(experiment_data)
        data = data.astype(dtypes)

        raw_dict['pressure_key'] = headers[0]
        raw_dict['loading_key'] = headers[1]

        # process isotherm branches if they exist
        if 'branch' in data.columns:
            data['branch'] = data['branch'].apply(lambda x: 0 if x == 'ads' else 1)
        else:
            raw_dict['branch'] = 'guess'

    if sht.cell(type_row, 1).value.lower().startswith('model'):

        # Store isotherm type
        isotype = 2
        model = {
            "name": sht.cell(type_row + 1, 1).value,
            "rmse": sht.cell(type_row + 2, 1).value,
            "pressure_range": ast.literal_eval(sht.cell(type_row + 3, 1).value),
            "loading_range": ast.literal_eval(sht.cell(type_row + 4, 1).value),
            "parameters": {},
        }

        final_row = type_row + 6

        while final_row < sht.nrows:
            point = sht.cell(final_row, 0).value
            if point == '':
                break
            model["parameters"][point] = sht.cell(final_row, 1).value
            final_row += 1

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
    # version check
    version = raw_dict.pop("file_version", None)
    if not version or float(version) < float(_parser_version):
        logger.warning(
            f"The file version is {version} while the parser uses version {_parser_version}. "
            "Strange things might happen, so double check your data."
        )
    raw_dict.pop('isotherm_data')  # remove useless field
    raw_dict.pop('iso_id', None)  # make sure id is not passed

    # check if material needs parsing
    material = {}
    for key, val in raw_dict.items():
        if key.startswith("_material_"):
            material[key.replace("_material_", "")] = val
    if material:
        for key in material:
            raw_dict.pop("_material_" + key)
        material['name'] = raw_dict['material']
        raw_dict['material'] = material

    # Update dictionary with any user parameters
    raw_dict.update(isotherm_parameters)

    if isotype == 1:
        return PointIsotherm(isotherm_data=data, **raw_dict)

    if isotype == 2:
        return ModelIsotherm(model=model_from_dict(model), **raw_dict)

    return BaseIsotherm(**raw_dict)
