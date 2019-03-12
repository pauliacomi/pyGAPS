"""
This module contains the sql interface for data manipulation.
"""

import array
import functools
import sqlite3

import pandas

from ..classes.adsorbate import Adsorbate
from ..classes.material import Material
from ..classes.pointisotherm import Isotherm
from ..classes.pointisotherm import PointIsotherm
from ..utilities.exceptions import ParsingError
from ..utilities.python_utilities import grouped
from ..utilities.sqlite_utilities import build_delete
from ..utilities.sqlite_utilities import build_insert
from ..utilities.sqlite_utilities import build_select
from ..utilities.sqlite_utilities import build_update


def with_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        path = args[0]
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row

        try:
            # Get a cursor object
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            ret = func(*args, **kwargs, cursor=cursor)

        except sqlite3.IntegrityError as e:
            conn.rollback()
            if kwargs.get('verbose', False):
                print("Error")
            raise ParsingError from e
        else:
            conn.commit()
        finally:
            conn.close()

        return ret

    return wrapper

# ---------------------- General functions


def _upload_one_all_columns(cursor, table_name, table_id, columns, input_dict,
                            overwrite, print_string, verbose, **kwargs):
    """Gets all elements from a table as a dictionary, excluding id"""

    to_insert = [table_id] + columns

    if overwrite:
        sql_com = build_update(table=table_name,
                               to_set=columns,
                               where=[table_id])
    else:
        sql_com = build_insert(table=table_name,
                               to_insert=to_insert)

    # Upload or modify data in machines table
    insert_dict = {key: input_dict.get(key) for key in to_insert}
    cursor.execute(sql_com, insert_dict)

    if verbose:
        # Print success
        print(print_string, "uploaded", insert_dict.get(table_id))


def _get_all_no_id(cursor, table_name, table_id, print_string, verbose, **kwargs):
    """Gets all elements from a table as a dictionary, excluding id"""

    cursor.execute("""SELECT * FROM """ + table_name)

    values = []
    for row in cursor:
        val = dict(zip(row.keys(), row))
        val.pop(table_id)
        values.append(val)

    return values


def _delete_by_id(cursor, table_name, table_id, element_id, print_string, verbose, **kwargs):
    """Deletes elements in a database by using their ID"""

    # Check if exists
    ids = cursor.execute(
        build_select(table=table_name,
                     to_select=[table_id],
                     where=[table_id]),
        {table_id:        element_id}
    ).fetchone()

    if ids is None:
        raise sqlite3.IntegrityError(
            "Element to delete does not exist in database")

    sql_com = build_delete(table=table_name,
                           where=[table_id])

    cursor.execute(sql_com, {table_id: element_id})

    if verbose:
        # Print success
        print("Success, deleted", print_string, element_id)


# ---------------------- Materials


@with_connection
def db_upload_material(path, material, overwrite=False, verbose=True, **kwargs):
    """
    Uploads materials to the database.
    If overwrite is set to true, the material is overwritten.
    Overwrite is done based on material.name + material.batch

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    material : Material
        Material class to upload to the database.
    overwrite : bool
        Whether to upload the material or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.

    """

    cursor = kwargs.pop('cursor', None)

    if not overwrite:
        cursor.execute(build_insert(table="materials",
                                    to_insert=['name', 'batch']),
                       {'name': material.name, 'batch': material.batch})

    # Upload or modify data in material_properties table
    if material.properties:
        # Get id of material
        material_ids = cursor.execute(
            build_select(table='materials',
                         to_select=['id'],
                         where=['name', 'batch']), {
                'name':        material.name,
                'batch':       material.batch,
            }
        ).fetchone()

        if material_ids is None:
            raise sqlite3.IntegrityError(
                "Material to overwrite does not exist in database")
        mat_id = material_ids[0]

        # Sql of update routine
        sql_update = build_update(table='material_properties',
                                  to_set=['value'],
                                  where=['material_id', 'type'])
        # Sql of insert routine
        sql_insert = build_insert(table='material_properties',
                                  to_insert=['material_id', 'type', 'value'])
        # Sql of delete routine
        sql_delete = build_delete(table='material_properties',
                                  where=['material_id'])

        updates = []

        if overwrite:
            # Find existing properties
            cursor.execute(
                build_select(table='material_properties',
                             to_select=['type'],
                             where=['material_id']), {
                    'material_id':        mat_id,
                }
            )
            updates = [elt[0] for elt in cursor.fetchall()]

        for prop in material.properties:
            if prop is not None:
                if prop in updates:
                    updates.remove(prop)
                    sql_com_prop = sql_update
                else:
                    sql_com_prop = sql_insert

                cursor.execute(sql_com_prop, {
                    'material_id':      mat_id,
                    'type':             prop,
                    'value':            material.properties[prop]
                })

        for prop in updates:
            cursor.execute(sql_delete, {'material_id': mat_id})

    if verbose:
        # Print success
        print("Material uploaded", material.name, material.batch)

    return


@with_connection
def db_get_materials(path, verbose=True, **kwargs):
    """
    Gets all materials and their properties.

    The number of materials is usually small, so all can be loaded in memory at once.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    list
        list of Materials
    """

    cursor = kwargs.pop('cursor', None)

    # Execute the query
    cursor.execute("""SELECT * FROM materials""")
    rows = cursor.fetchall()

    materials = []

    # Create the materials
    for row in rows:

        material_params = dict(zip(row.keys(), row))

        # Get the extra data from the material_properties table
        cursor.execute(build_select(table='material_properties',
                                    to_select=['type', 'value'],
                                    where=['material_id']),
                       {
            'material_id':        material_params.pop('id')
        })

        material_params.update({
            row[0]: row[1] for row in cursor})

        # Build material objects
        materials.append(Material(**material_params))

    if verbose:
        # Print success
        print("Selected", len(materials), "materials")

    return materials


@with_connection
def db_delete_material(path, material, verbose=True, **kwargs):
    """
    Delete material from the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    material : Material
        Material class to upload to the database.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)

    # Get id of material
    material_ids = cursor.execute(
        build_select(table='materials',
                     to_select=['id'],
                     where=['name', 'batch']),
        {
            'name':        material.name,
            'batch':       material.batch,
        }
    ).fetchone()

    if material_ids is None:
        raise sqlite3.IntegrityError(
            "Material to delete does not exist in database")
    mat_id = material_ids[0]

    # Delete data from material_properties table
    cursor.execute(build_delete(table='material_properties',
                                where=['material_id']), {'material_id': mat_id})

    # Delete material info in materials table
    cursor.execute(build_delete(table='materials',
                                where=['id']), {'id': mat_id})

    if verbose:
        # Print success
        print("Success", material.name, material.batch)

    return


@with_connection
def db_upload_material_property_type(path, type_dict, overwrite=False, verbose=True, **kwargs):
    """
    Uploads a material property type.

    The type_dict takes the form of::

        {
            'type' : 'the_type',
            'unit': 'the_unit',
            'description': 'the_description'
        }

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    type_dict : dict
        A dictionary that contains property type.
    overwrite : bool
        Whether to upload the property type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _upload_one_all_columns(cursor, 'material_properties_type', 'type', ['unit', 'description'],
                            type_dict, overwrite, 'Material properties type', verbose)


@with_connection
def db_get_material_property_types(path, verbose=True, **kwargs):
    """
    Gets all material property types.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    dict
        dict of property types
    """

    cursor = kwargs.pop('cursor', None)
    return _get_all_no_id(cursor, 'material_properties_type', 'id',
                          'material property types', verbose)


@with_connection
def db_delete_material_property_type(path, material_prop_type, verbose=True, **kwargs):
    """
    Delete material property type in the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    material_prop_type : str
        The type to delete.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _delete_by_id(cursor, 'material_properties_type', 'type', material_prop_type,
                  'material property types', verbose)


# ---------------------- Experiments


@with_connection
def db_upload_isotherm(path, isotherm, verbose=True, **kwargs):
    """
    Uploads isotherm to the database.

    If overwrite is set to true, the isotherm is overwritten.
    Overwrite is done based on isotherm.iso_id

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    isotherm : Isotherm
        Isotherm class to upload to the database.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)

    # The isotherm is going to be inserted into the database
    # Build upload dict
    upload_dict = {}
    iso_dict = isotherm.to_dict()
    iso_id = isotherm.iso_id
    for param in Isotherm._db_columns:
        upload_dict.update({param: iso_dict.pop(param, None)})
    upload_dict['id'] = iso_id

    # Upload isotherm info to database
    cursor.execute(build_insert(table='isotherms',
                                to_insert=Isotherm._db_columns), upload_dict)

    # Then, the isotherm data will be uploaded into the isotherm_data table

    # Build sql request
    sql_insert = build_insert(table='isotherm_data',
                              to_insert=['iso_id', 'type', 'data'])

    # Insert standard data fields:
    cursor.execute(sql_insert,
                   {'iso_id': iso_id, 'type': 'pressure',
                    'data': isotherm.pressure().tobytes()}
                   )

    cursor.execute(sql_insert,
                   {'iso_id': iso_id, 'type': 'loading',
                    'data': isotherm.loading().tobytes()}
                   )

    # Update or insert other fields:
    for key in isotherm.other_keys:
        cursor.execute(sql_insert,
                       {'iso_id': iso_id, 'type': key,
                        'data': isotherm.other_data(key).tobytes()}
                       )

    # Upload the remaining data from the isotherm
    for key in iso_dict:
        if key not in isotherm._unit_params:
            cursor.execute(build_insert(table='isotherm_properties',
                                        to_insert=['iso_id', 'type', 'value']),
                           {'iso_id': iso_id,
                            'type': key,
                            'value': iso_dict[key]
                            })

    if verbose:
        # Print success
        print("Success:", isotherm)


@with_connection
def db_get_isotherms(path, criteria, verbose=True, **kwargs):
    """
    Gets isotherms with the selected criteria from the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    criteria : dict
        Dictionary of isotherm parameters on which to filter database.
        For example {'name': 'a_name', 'date': 'a_date'}. Parameters
        must exist for the filtering to take place.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    list
        list of Isotherms
    """

    cursor = kwargs.pop('cursor', None)

    # Get isotherm info from database
    cursor.execute(
        build_select(table='isotherms',
                           to_select=Isotherm._db_columns,
                           where=criteria.keys()), criteria)

    isotherms = []
    alldata = cursor.fetchall()

    for rows in grouped(alldata, 100):  # we are taking 100 isotherms at a time

        ids = tuple(row['id'] for row in rows)

        # Get isotherm properties from database
        cursor.execute("""
                SELECT iso_id, type, value FROM "isotherm_properties"
                WHERE iso_id IN (%s);
                """ % ','.join('?' * len(ids)), ids)
        isotherm_props = cursor.fetchall()

        # Get the properties from the data table
        cursor.execute("""
                SELECT iso_id, type, data FROM "isotherm_data"
                WHERE iso_id IN (%s);
                """ % ','.join('?' * len(ids)), ids)
        isotherm_data = cursor.fetchall()

        for row in rows:

            # Generate the isotherm data
            data_dict = {data[1]: array.array('d', data[2])
                         for data in isotherm_data if data[0] == row['id']}
            other_keys = [key for key in data_dict.keys()
                          if key not in ('pressure', 'loading')]
            exp_data = pandas.DataFrame(data_dict)

            # Generate the isotherm parameters dictionary
            exp_params = dict(zip(row.keys(), row))
            exp_params.update(
                {prop[1]: prop[2]
                    for prop in isotherm_props if prop[0] == row['id']})
            exp_params.update({'other_keys': other_keys})
            exp_params.pop('id')

            # build isotherm object
            isotherms.append(PointIsotherm(isotherm_data=exp_data,
                                           pressure_key="pressure",
                                           loading_key="loading",
                                           ** exp_params))

    if verbose:
        # Print success
        print("Selected", len(isotherms), "isotherms")

    return isotherms


@with_connection
def db_delete_isotherm(path, iso_id, verbose=True, **kwargs):
    """
    Delete isotherm in the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    isotherm : Isotherm or Isotherm.iso_id
        The Isotherm object to delete from the database or its ID.
    verbose : bool
        Print to console on success or error.
    """

    if isinstance(iso_id, Isotherm):
        iso_id = iso_id.iso_id

    cursor = kwargs.pop('cursor', None)

    # Check if isotherm exists
    ids = cursor.execute(
        build_select(table='isotherms',
                     to_select=['id'],
                     where=['id']),
        {'id':        iso_id}
    ).fetchone()

    if ids is None:
        raise sqlite3.IntegrityError(
            "Isotherm to delete does not exist in database. Did you modify any parameters?")

    # Delete data from isotherm_data table
    cursor.execute(build_delete(table='isotherm_data',
                                where=['iso_id']), {'iso_id': iso_id})

    # Delete data from isotherm_data table
    cursor.execute(build_delete(table='isotherm_properties',
                                where=['iso_id']), {'iso_id': iso_id})

    # Delete isotherm in isotherms table
    cursor.execute(build_delete(table='isotherms',
                                where=['id']), {'id': iso_id})

    if verbose:
        # Print success
        print("Success:", iso_id)


@with_connection
def db_upload_isotherm_type(path, type_dict, overwrite=False, verbose=True, **kwargs):
    """
    Uploads a isotherm type.

    The type_dict takes the form of::

        {
            'type' : 'the_type',
            'unit': 'the_unit',
            'description': 'the_description'
        }

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    type_dict : dict
        A dictionary that contains isotherm type.
    overwrite : bool
        Whether to upload the isotherm type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _upload_one_all_columns(cursor, 'isotherm_type', 'type', ['description'],
                            type_dict, overwrite, 'Experiment type', verbose)


@with_connection
def db_get_isotherm_types(path, verbose=True, **kwargs):
    """
    Gets all isotherm types.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    dict
        dict of isotherm types
    """

    cursor = kwargs.pop('cursor', None)
    return _get_all_no_id(cursor, 'isotherm_type', 'id',
                          'isotherm types', verbose)


@with_connection
def db_delete_isotherm_type(path, iso_type, verbose=True, **kwargs):
    """
    Delete isotherm type in the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    data_type : str
        The type to delete.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _delete_by_id(cursor, 'isotherm_type', 'type', iso_type,
                  'isotherm types', verbose)


@with_connection
def db_upload_isotherm_property_type(path, type_dict, overwrite=False, verbose=True, **kwargs):
    """
    Uploads a property type.

    The type_dict takes the form of::

        {
            'type' : 'the_type',
            'unit': 'the_unit',
            'description': 'the_description'
        }

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    type_dict : dict
        A dictionary that contains property type.
    overwrite : bool
        Whether to upload the property type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _upload_one_all_columns(cursor, 'isotherm_properties_type', 'type', ['unit', 'description'],
                            type_dict, overwrite, 'Experiment property type', verbose)


@with_connection
def db_get_isotherm_property_types(path, verbose=True, **kwargs):
    """
    Gets all isotherm property types.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    dict
        dict of property types
    """

    cursor = kwargs.pop('cursor', None)
    return _get_all_no_id(cursor, 'isotherm_properties_type', 'id',
                          'isotherm property types', verbose)


@with_connection
def db_delete_isotherm_property_type(path, property_type, verbose=True, **kwargs):
    """
    Delete isotherm property type in the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    property_type : str
        Property type to delete.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _delete_by_id(cursor, 'isotherm_properties_type', 'type', property_type,
                  'isotherm property types', verbose)


@with_connection
def db_upload_isotherm_data_type(path, type_dict, overwrite=False, verbose=True, **kwargs):
    """
    Uploads a data type.

    The type_dict takes the form of::

        {
            'type' : 'the_type',
            'unit': 'the_unit',
            'description': 'the_description'
        }

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    type_dict : dict
        A dictionary that contains data type.
    overwrite : bool
        Whether to upload the data type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _upload_one_all_columns(cursor, 'isotherm_data_type', 'type', ['unit', 'description'],
                            type_dict, overwrite, 'Experiment data type', verbose)


@with_connection
def db_get_isotherm_data_types(path, verbose=True, **kwargs):
    """
    Gets all isotherm data types.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    dict
        dict of data types
    """

    cursor = kwargs.pop('cursor', None)
    return _get_all_no_id(cursor, 'isotherm_data_type', 'id',
                          'isotherm data types', verbose)


@with_connection
def db_delete_isotherm_data_type(path, data_type, verbose=True, **kwargs):
    """
    Delete isotherm data type in the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    data_type : str
        The type to delete.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _delete_by_id(cursor, 'isotherm_data_type', 'type', data_type,
                  'isotherm data types', verbose)


# ---------------------- Adsorbates

@with_connection
def db_upload_adsorbate(path, adsorbate, overwrite=False, verbose=True, **kwargs):
    """
    Uploads adsorbates to the database.

    If overwrite is set to true, the isotherm is overwritten.
    Overwrite is done based on adsorbate.name

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    adsorbate : Adsorbate
        Adsorbate class to upload to the database.
    overwrite : bool
        Whether to upload the adsorbate or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)

    if not overwrite:
        # Upload in material table
        cursor.execute(build_insert(table="adsorbates", to_insert=['name']),
                       {'name': adsorbate.name})

    # Get id of adsorbate
    ids = cursor.execute(
        build_select(table='adsorbates',
                     to_select=['id'],
                     where=['name']),
        {'name': adsorbate.name}
    ).fetchone()

    if ids is None:
        raise sqlite3.IntegrityError(
            "Adsorbate to overwrite does not exist in database")
    ads_id = ids[0]

    # Upload or modify data in the associated tables
    if adsorbate.properties:

        # Sql of update routine
        sql_update = build_update(table='adsorbate_properties',
                                  to_set=['value'],
                                  where=['ads_id', 'type'])
        # Sql of insert routine
        sql_insert = build_insert(table='adsorbate_properties',
                                  to_insert=['ads_id', 'type', 'value'])
        # Sql of delete routine
        sql_delete = build_delete(table='adsorbate_properties',
                                  where=['ads_id'])

        updates = []

        if overwrite:
            # Find existing properties
            cursor.execute(
                build_select(table='adsorbate_properties',
                             to_select=['type'],
                             where=['ads_id']),
                {'ads_id': ads_id}
            )
            updates = [elt[0] for elt in cursor.fetchall()]

        for prop in adsorbate.properties:
            if prop in updates:
                updates.remove(prop)
                sql_com_prop = sql_update
            else:
                sql_com_prop = sql_insert

            cursor.execute(sql_com_prop, {
                'ads_id':           ads_id,
                'type':             prop,
                'value':            adsorbate.properties[prop]
            })

        # delete the rest
        for prop in updates:
            cursor.execute(sql_delete, {'ads_id': ads_id})

    if adsorbate.alias:

        if overwrite:
            # Delete existing names
            cursor.execute(
                build_delete(table='adsorbate_names',
                             where=['ads_id']),
                {'ads_id': ads_id}
            )

        # Sql of insert routine
        sql_insert = build_insert(table='adsorbate_names',
                                  to_insert=['ads_id', 'name'])

        for alias in adsorbate.alias:
            cursor.execute(sql_insert, {
                'ads_id':           ads_id,
                'name':             alias,
            })

    if verbose:
        # Print success
        print("Adsorbate uploaded", adsorbate.name)


@with_connection
def db_get_adsorbates(path, verbose=True, **kwargs):
    """
    Gets all adsorbates and their properties.

    The number of adsorbates is usually small, so all can be
    loaded in memory at once.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    list
        list of Adsorbates
    """

    cursor = kwargs.pop('cursor', None)

    # Get required adsorbate from database
    cursor.execute("""SELECT * FROM adsorbates""")

    rows = cursor.fetchall()

    # Create the adsorbates
    adsorbates = []
    for row in rows:

        cursor.execute(
            build_select(table='adsorbate_properties',
                         to_select=['type', 'value'],
                         where=['ads_id']),
            {'ads_id': row['id']}
        )

        adsorbate_params = {r[0]: r[1] for r in cursor}

        cursor.execute(
            build_select(table='adsorbate_names',
                         to_select=['name'],
                         where=['ads_id']),
            {'ads_id': row['id']}
        )
        alias = [r[0] for r in cursor]

        # Build adsorbate objects
        adsorbates.append(
            Adsorbate(row['name'], alias=alias, **adsorbate_params))

    # Print success
    if verbose:
        print("Selected", len(adsorbates), "adsorbates")

    return adsorbates


@with_connection
def db_delete_adsorbate(path, adsorbate, verbose=True, **kwargs):
    """
    Delete adsorbate from the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    adsorbate : Adsorbate
        The Adsorbate class to delete.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)

    # Get id of adsorbate
    ids = cursor.execute(
        build_select(table='adsorbates',
                     to_select=['id'],
                     where=['name']),
        {'name': adsorbate.name}
    ).fetchone()

    if ids is None:
        raise sqlite3.IntegrityError(
            "Adsorbate to delete does not exist in database")
    ads_id = ids[0]

    # Delete data from adsorbate_properties table
    cursor.execute(
        build_delete(table='adsorbate_properties',
                     where=['ads_id']),
        {'ads_id': ads_id})

    # Delete names from adsorbate_names table
    cursor.execute(
        build_delete(table='adsorbate_names',
                     where=['ads_id']),
        {'ads_id': ads_id})

    # Delete material in adsorbates table
    cursor.execute(
        build_delete(table='adsorbates',
                     where=['id']),
        {'id': ads_id})

    if verbose:
        # Print success
        print("Success", adsorbate.name)


@with_connection
def db_upload_adsorbate_property_type(path, type_dict, overwrite=False, verbose=True, **kwargs):
    """
    Uploads an adsorbate property type.

    The type_dict takes the form of::

        {
            'type' : 'the_type',
            'unit': 'the_unit',
            'description': 'the_description'
        }

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    type_dict : dict
        A dictionary that contains property type.
    overwrite : bool
        Whether to upload the property type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _upload_one_all_columns(cursor, 'adsorbate_properties_type', 'type', ['unit', 'description'],
                            type_dict, overwrite, 'Property type', verbose)


@with_connection
def db_get_adsorbate_property_types(path, verbose=True, **kwargs):
    """
    Gets all adsorbate property types.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    dict
        dict of property types
    """

    cursor = kwargs.pop('cursor', None)
    return _get_all_no_id(cursor, 'adsorbate_properties_type', 'id',
                          'adsorbate property types', verbose)


@with_connection
def db_delete_adsorbate_property_type(path, property_type, verbose=True, **kwargs):
    """
    Delete property type in the database.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    property_type : str
        Name of the property type to delete.
    verbose : bool
        Print to console on success or error.
    """

    cursor = kwargs.pop('cursor', None)
    _delete_by_id(cursor, 'adsorbate_properties_type', 'type', property_type,
                  'adsorbate property types', verbose)


@with_connection
def db_get_adsorbate_names(path, verbose=True, **kwargs):
    """
    Gets all adsorbate aliases.

    Parameters
    ----------
    path : str
        Path to the database. Use pygaps.DATABASE for internal access.
    verbose : bool
        Print to console on success or error.

    Returns
    -------
    dict
        dict of aliases
    """

    cursor = kwargs.pop('cursor', None)
    return _get_all_no_id(cursor, 'adsorbate_names', 'id', '', verbose)
