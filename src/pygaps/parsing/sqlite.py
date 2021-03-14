"""
This module contains the sql interface for data manipulation.
"""

import array
import functools
import json
import logging

logger = logging.getLogger('pygaps')
import sqlite3

import pandas

from pygaps.core.adsorbate import Adsorbate
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.material import Material
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.data import ADSORBATE_LIST
from pygaps.data import DATABASE
from pygaps.data import MATERIAL_LIST
from pygaps.modelling import model_from_dict
from pygaps.utilities.exceptions import ParsingError
from pygaps.utilities.python_utilities import checkSQLbool
from pygaps.utilities.python_utilities import grouped
from pygaps.utilities.sqlite_utilities import build_delete
from pygaps.utilities.sqlite_utilities import build_insert
from pygaps.utilities.sqlite_utilities import build_select
from pygaps.utilities.sqlite_utilities import build_update


def with_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        # If cursor exists we just move on
        if kwargs.get('cursor'):
            return func(*args, **kwargs)

        db_path = kwargs.get('db_path', DATABASE)
        db_path = db_path if db_path else DATABASE
        conn = sqlite3.connect(
            str(db_path)
        )  # TODO remove 'str' call when dropping P3.6
        conn.row_factory = sqlite3.Row

        try:
            # Get a cursor object
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')
            ret = func(*args, **kwargs, cursor=cursor)

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ParsingError(e)

        except sqlite3.InterfaceError as e:
            conn.rollback()
            raise ParsingError(e)

        else:
            conn.commit()

        finally:
            conn.close()

        return ret

    return wrapper


# ---------------------- General functions


def _upload_one_all_columns(
    cursor,
    table_name,
    table_id,
    columns,
    input_dict,
    overwrite,
    print_string,
    verbose,
    **kwargs,
):
    """Insert or overwrite a list of things in a table."""
    to_insert = [table_id] + columns

    if overwrite:
        sql_com = build_update(
            table=table_name, to_set=columns, where=[table_id]
        )
    else:
        sql_com = build_insert(table=table_name, to_insert=to_insert)

    # Upload or modify data
    insert_dict = {key: input_dict.get(key) for key in to_insert}
    try:
        cursor.execute(sql_com, insert_dict)
    except sqlite3.Error as e:
        raise type(e)(
            f"Error inserting dict {insert_dict}. Original error:\n {e}"
        )

    if verbose:
        # Print success
        logger.info(f"{print_string} uploaded {insert_dict.get(table_id)}")


def _get_all_no_id(
    cursor,
    table_name,
    table_id,
    print_string,
    verbose,
    **kwargs,
):
    """Get all elements from a table as a dictionary, excluding id."""
    try:
        cursor.execute("""SELECT * FROM """ + table_name)
    except sqlite3.Error as e:
        raise type(e)(
            f"Error getting data from {table_name}. Original error:\n {e}"
        )

    values = []
    for row in cursor:
        val = dict(zip(row.keys(), row))
        val.pop(table_id)
        values.append(val)

    return values


def _delete_by_id(
    cursor,
    table_name,
    table_id,
    element_id,
    print_string,
    verbose,
    **kwargs,
):
    """Delete elements in a table by using their ID."""

    # Check if exists
    ids = cursor.execute(
        build_select(table=table_name, to_select=[table_id], where=[table_id]),
        {
            table_id: element_id
        }
    ).fetchone()

    if ids is None:
        raise sqlite3.IntegrityError(
            f"Element to delete ({element_id}) does not exist in table {table_name}."
        )

    try:
        cursor.execute(
            build_delete(table=table_name, where=[table_id]),
            {table_id: element_id}
        )
    except sqlite3.Error as e:
        raise type(e)(
            f"Error deleting {element_id} from {table_name}. Original error:\n {e}"
        )

    if verbose:
        # Print success
        logger.info(f"Success, deleted {print_string}: {element_id}")


# ---------------------- Adsorbates


@with_connection
def adsorbate_to_db(
    adsorbate, db_path=None, overwrite=False, verbose=True, **kwargs
):
    """
    Upload an adsorbate to the database.

    If overwrite is set to true, the adsorbate is overwritten.
    Overwrite is done based on adsorbate.name

    Parameters
    ----------
    adsorbate : Adsorbate
        Adsorbate class to upload to the database.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    overwrite : bool
        Whether to upload the adsorbate or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Extra information printed to console.

    """
    cursor = kwargs['cursor']

    # If we need to overwrite, we find the id of existing adsorbate.
    if overwrite:
        ids = cursor.execute(
            build_select(table='adsorbates', to_select=['id'], where=['name']),
            {
                'name': adsorbate.name
            }
        ).fetchone()
        if ids is None:
            raise sqlite3.IntegrityError(
                f"Adsorbate to overwrite ({adsorbate.name}) does not exist in database."
            )
        ads_id = ids[0]
    # If overwrite is not specified, we upload it to the adsorbates table
    else:
        cursor.execute(
            build_insert(table="adsorbates", to_insert=['name']),
            {'name': adsorbate.name}
        )
        ads_id = cursor.lastrowid

    # Upload or modify data in the associated tables
    properties = adsorbate.to_dict()
    del properties['name']  # no need for this

    if properties:
        if overwrite:
            # Delete existing properties
            _delete_by_id(
                cursor,
                'adsorbate_properties',
                'ads_id',
                ads_id,
                'adsorbate properties',
                verbose,
            )

        for prop, val in properties.items():

            sql_insert = build_insert(
                table='adsorbate_properties',
                to_insert=['ads_id', 'type', 'value'],
            )

            if not isinstance(val, (list, set, tuple)):
                val = [val]

            for vl in val:
                try:
                    cursor.execute(
                        sql_insert, {
                            'ads_id': ads_id,
                            'type': prop,
                            'value': vl
                        }
                    )
                except sqlite3.InterfaceError as e:
                    raise type(e)(
                        f"Cannot process property {prop}: {vl}"
                        f"Original error:\n{e}"
                    )

    # Add to existing list
    if overwrite:
        if adsorbate in ADSORBATE_LIST:
            ADSORBATE_LIST.remove(adsorbate.name)
    ADSORBATE_LIST.append(adsorbate)

    if verbose:
        # Print success
        logger.info(f"Adsorbate uploaded: '{adsorbate.name}'")


@with_connection
def adsorbates_from_db(db_path=None, verbose=True, **kwargs):
    """
    Get database adsorbates and their properties.

    The number of adsorbates is usually small, so all can be
    loaded in memory at once.

    Parameters
    ----------
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    list
        list of Adsorbates
    """

    cursor = kwargs['cursor']

    # Execute the query
    cursor.execute("""SELECT * FROM 'adsorbates'""")
    rows = cursor.fetchall()

    # Get other data and create adsorbates
    adsorbates = []
    for row in rows:

        # Get all properties
        props = cursor.execute(
            build_select(
                table='adsorbate_properties',
                to_select=['type', 'value'],
                where=['ads_id']
            ), {
                'ads_id': row['id']
            }
        ).fetchall()

        # Iterate for props
        adsorbate_params = {}
        for prop in props:
            if prop[0] in adsorbate_params:
                o = adsorbate_params[prop[0]]
                adsorbate_params[
                    prop[0]] = (o if isinstance(o, list) else [o]) + [prop[1]]
            else:
                adsorbate_params[prop[0]] = prop[1]

        # Build adsorbate objects
        adsorbates.append(Adsorbate(row['name'], **adsorbate_params))

    # Print success
    if verbose:
        logger.info(f"Selected {len(adsorbates)} adsorbates")

    return adsorbates


@with_connection
def adsorbate_delete_db(adsorbate, db_path=None, verbose=True, **kwargs):
    """
    Delete adsorbate from the database.

    Parameters
    ----------
    adsorbate : Adsorbate or str
        The Adsorbate class to delete or its name.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """

    cursor = kwargs['cursor']

    # Get id of adsorbate
    ids = cursor.execute(
        build_select(table='adsorbates', to_select=['id'], where=['name']), {
            'name':
            adsorbate.name if isinstance(adsorbate, Adsorbate) else adsorbate
        }
    ).fetchone()
    if ids is None:
        raise sqlite3.IntegrityError(
            "Adsorbate to delete does not exist in database."
        )
    ads_id = ids[0]

    try:
        # Delete data from adsorbate_properties table
        cursor.execute(
            build_delete(table='adsorbate_properties', where=['ads_id']),
            {'ads_id': ads_id}
        )

        # Delete original name in adsorbates table
        cursor.execute(
            build_delete(table='adsorbates', where=['id']), {'id': ads_id}
        )
    except sqlite3.Error as e:
        raise type(e)(
            "Could not delete adsorbate, are there still isotherms referencing it?"
        ) from None

    # Remove from existing list
    if adsorbate in ADSORBATE_LIST:
        ADSORBATE_LIST.remove(adsorbate)

    if verbose:
        # Print success
        logger.info(f"Adsorbate deleted: '{adsorbate}'")


@with_connection
def adsorbate_property_type_to_db(
    type_dict, db_path=None, overwrite=False, verbose=True, **kwargs
):
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
    type_dict : dict
        A dictionary that contains property type.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    overwrite : bool
        Whether to upload the property type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Extra information printed to console.
    """
    _upload_one_all_columns(
        kwargs['cursor'],
        'adsorbate_properties_type',
        'type',
        ['unit', 'description'],
        type_dict,
        overwrite,
        'Property type',
        verbose,
    )


@with_connection
def adsorbate_property_types_from_db(db_path=None, verbose=True, **kwargs):
    """
    Get all adsorbate property types.

    Parameters
    ----------
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    dict
        dict of property types
    """
    return _get_all_no_id(
        kwargs['cursor'],
        'adsorbate_properties_type',
        'id',
        'adsorbate property types',
        verbose,
    )


@with_connection
def adsorbate_property_type_delete_db(
    property_type, db_path=None, verbose=True, **kwargs
):
    """
    Delete property type in the database.

    Parameters
    ----------
    property_type : str
        Name of the property type to delete.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """
    _delete_by_id(
        kwargs['cursor'],
        'adsorbate_properties_type',
        'type',
        property_type,
        'adsorbate property types',
        verbose,
    )


# ---------------------- Materials


@with_connection
def material_to_db(
    material,
    db_path=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):
    """
    Upload a material to the database.

    If overwrite is set to true, the material is overwritten.
    Overwrite is done based on material.name

    Parameters
    ----------
    material : Material
        Material class to upload to the database.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    overwrite : bool
        Whether to upload the material or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Extra information printed to console.

    """

    cursor = kwargs['cursor']

    # If we need to overwrite, we find the id of existing adsorbate.
    if overwrite:
        ids = cursor.execute(
            build_select(table='materials', to_select=['id'], where=['name']),
            {
                'name': material.name
            }
        ).fetchone()
        if ids is None:
            raise sqlite3.IntegrityError(
                f"Material to overwrite ({material.name}) does not exist in database."
            )
        mat_id = ids[0]
    # If overwrite is not specified, we upload it to the adsorbates table
    else:
        cursor.execute(
            build_insert(table="materials", to_insert=['name']),
            {'name': material.name}
        )
        mat_id = cursor.lastrowid

    # Upload or modify data in material_properties table
    properties = material.to_dict()
    del properties['name']  # no need for this

    if properties:
        if overwrite:
            # Delete existing properties
            _delete_by_id(
                cursor,
                'material_properties',
                'mat_id',
                mat_id,
                'material properties',
                verbose,
            )

        for prop, val in properties.items():

            sql_insert = build_insert(
                table='material_properties',
                to_insert=['mat_id', 'type', 'value'],
            )

            if not isinstance(val, (list, set, tuple)):
                val = [val]

            for vl in val:
                try:
                    cursor.execute(
                        sql_insert, {
                            'mat_id': mat_id,
                            'type': prop,
                            'value': vl
                        }
                    )
                except sqlite3.InterfaceError as e:
                    raise type(e)(
                        f"Cannot process property {prop}: {vl}"
                        f"Original error:\n{e}"
                    ) from None

    # Add to existing list
    if overwrite:
        if material in MATERIAL_LIST:
            MATERIAL_LIST.remove(material.name)

    MATERIAL_LIST.append(material)

    if verbose:
        # Print success
        logger.info(f"Material uploaded: '{material.name}'")


@with_connection
def materials_from_db(db_path=None, verbose=True, **kwargs):
    """
    Get all materials and their properties.

    The number of materials is usually small, so all can be loaded in memory at once.

    Parameters
    ----------
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    list
        list of Materials
    """

    cursor = kwargs['cursor']

    # Execute the query
    cursor.execute("""SELECT * FROM materials""")
    rows = cursor.fetchall()

    # Get other data and create materials
    materials = []
    for row in rows:

        material_params = dict(zip(row.keys(), row))

        # Get the extra data from the material_properties table
        cursor.execute(
            build_select(
                table='material_properties',
                to_select=['type', 'value'],
                where=['mat_id']
            ), {'mat_id': material_params.pop('id')}
        )

        material_params.update({row[0]: row[1] for row in cursor})

        # Build material objects
        materials.append(Material(**material_params))

    if verbose:
        # Print success
        logger.info(f"Selected {len(materials)} materials")

    return materials


@with_connection
def material_delete_db(material, db_path=None, verbose=True, **kwargs):
    """
    Delete material from the database.

    Parameters
    ----------
    material : Material or str
        Material class to upload to the database.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """

    cursor = kwargs['cursor']

    # Get id of material
    mat_id = cursor.execute(
        build_select(table='materials', to_select=['id'], where=['name']), {
            'name':
            material.name if isinstance(material, Material) else material,
        }
    ).fetchone()
    if mat_id is None:
        raise sqlite3.IntegrityError(
            "Material to delete does not exist in database."
        ) from None
    mat_id = mat_id[0]

    # Delete data from material_properties table
    cursor.execute(
        build_delete(table='material_properties', where=['mat_id']),
        {'mat_id': mat_id}
    )

    try:
        # Delete material info in materials table
        cursor.execute(
            build_delete(table='materials', where=['id']), {'id': mat_id}
        )
    except sqlite3.Error as e:
        raise type(e)(
            "Could not delete material, are there still isotherms referencing it?"
        ) from None

    # Remove from existing list
    if material in MATERIAL_LIST:
        MATERIAL_LIST.remove(material)

    if verbose:
        # Print success
        logger.info(
            f"Material deleted: '{material.name if isinstance(material, Material) else material}'"
        )


@with_connection
def material_property_type_to_db(
    type_dict, db_path=None, overwrite=False, verbose=True, **kwargs
):
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
    type_dict : dict
        A dictionary that contains property type.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    overwrite : bool
        Whether to upload the property type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Extra information printed to console.
    """
    _upload_one_all_columns(
        kwargs['cursor'],
        'material_properties_type',
        'type',
        ['unit', 'description'],
        type_dict,
        overwrite,
        'Material properties type',
        verbose,
    )


@with_connection
def material_property_types_from_db(db_path=None, verbose=True, **kwargs):
    """
    Get all material property types.

    Parameters
    ----------
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    dict
        dict of property types
    """
    return _get_all_no_id(
        kwargs['cursor'],
        'material_properties_type',
        'id',
        'material property types',
        verbose,
    )


@with_connection
def material_property_type_delete_db(
    material_prop_type, db_path=None, verbose=True, **kwargs
):
    """
    Delete material property type in the database.

    Parameters
    ----------
    material_prop_type : str
        The type to delete.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """
    _delete_by_id(
        kwargs['cursor'],
        'material_properties_type',
        'type',
        material_prop_type,
        'material property types',
        verbose,
    )


# ---------------------- Isotherms


@with_connection
def isotherm_to_db(
    isotherm,
    db_path=None,
    autoinsert_material=True,
    autoinsert_adsorbate=True,
    verbose=True,
    **kwargs
):
    """
    Uploads isotherm to the database.

    If overwrite is set to true, the isotherm is overwritten.
    Overwrite is done based on isotherm.iso_id

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm, PointIsotherm or ModelIsotherm to upload to the database.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    autoinsert_material: bool, True
        Whether to automatically insert an isotherm material if it is not found
        in the database.
    autoinsert_adsorbate: bool, True
        Whether to automatically insert an isotherm adsorbate if it is not found
        in the database.
    verbose : bool, True
        Extra information printed to console.
    """

    cursor = kwargs['cursor']
    # Checks
    if autoinsert_material:
        if isotherm.material not in MATERIAL_LIST:
            material_to_db(
                isotherm.material if isinstance(isotherm.material, Material)
                else Material(isotherm.material),
                db_path=db_path,
                cursor=cursor
            )
    if autoinsert_adsorbate:
        if isotherm.adsorbate not in ADSORBATE_LIST:
            adsorbate_to_db(
                isotherm.adsorbate
                if isinstance(isotherm.adsorbate, Adsorbate) else
                Adsorbate(isotherm.adsorbate),
                db_path=db_path,
                cursor=cursor
            )

    # The isotherm is going to be inserted into the database
    # Build upload dict
    iso_id = isotherm.iso_id
    upload_dict = {'id': iso_id}

    if isinstance(isotherm, PointIsotherm):
        upload_dict['iso_type'] = 'pointisotherm'
    elif isinstance(isotherm, ModelIsotherm):
        upload_dict['iso_type'] = 'modelisotherm'
    elif isinstance(isotherm, BaseIsotherm):
        upload_dict['iso_type'] = 'isotherm'
    else:
        raise ParsingError("Unknown isotherm type.")

    iso_dict = isotherm.to_dict()

    # attributes which are kept in the database
    upload_dict.update({
        param: iso_dict.pop(param, None)
        for param in BaseIsotherm._required_params
    })

    # Upload isotherm info to database
    db_columns = ["id", "iso_type"] + BaseIsotherm._required_params
    try:
        cursor.execute(
            build_insert(table='isotherms', to_insert=db_columns), upload_dict
        )
    except sqlite3.Error as e:
        raise type(e)(
            f"""Error inserting isotherm "{upload_dict["id"]}" base properties. """
            f"""Ensure material "{upload_dict["material"]}", and adsorbate "{upload_dict["adsorbate"]}" """
            f"""exist in the database already. Original error:\n {e}"""
        ) from None

    # TODO insert multiple
    # Upload the other isotherm parameters
    for key in iso_dict:
        if key not in isotherm._unit_params:
            # Deal with bools
            val = iso_dict[key]
            if isinstance(val, bool):
                val = 'TRUE' if val else 'FALSE'
            cursor.execute(
                build_insert(
                    table='isotherm_properties',
                    to_insert=['iso_id', 'type', 'value']
                ), {
                    'iso_id': iso_id,
                    'type': key,
                    'value': val
                }
            )

    # Then, the isotherm data/model will be uploaded into the data table

    # Build sql request
    sql_insert = build_insert(
        table='isotherm_data', to_insert=['iso_id', 'type', 'data']
    )

    if isinstance(isotherm, PointIsotherm):
        # Insert standard data fields:
        cursor.execute(
            sql_insert, {
                'iso_id': iso_id,
                'type': 'pressure',
                'data': isotherm.pressure().tobytes()
            }
        )
        cursor.execute(
            sql_insert, {
                'iso_id': iso_id,
                'type': 'loading',
                'data': isotherm.loading().tobytes()
            }
        )
        # Update or insert other fields:
        for key in isotherm.other_keys:
            cursor.execute(
                sql_insert, {
                    'iso_id': iso_id,
                    'type': key,
                    'data': isotherm.other_data(key).tobytes()
                }
            )
    elif isinstance(isotherm, ModelIsotherm):
        # Insert model parameters
        cursor.execute(
            sql_insert, {
                'iso_id': iso_id,
                'type': 'model',
                'data': json.dumps(isotherm.model.to_dict())
            }
        )

    if verbose:
        # Print success
        logger.info(f"Isotherm uploaded: '{isotherm.iso_id}'")


@with_connection
def isotherms_from_db(criteria=None, db_path=None, verbose=True, **kwargs):
    """
    Get isotherms with the selected criteria from the database.

    Parameters
    ----------
    criteria : dict, None
        Dictionary of isotherm parameters on which to filter database from
        base parameters ('material', 'adsorbate', 'temperature', 'type').
        For example {'material': 'm1', 'temperature': '77'}. Parameters
        must exist for the filtering to take place otherwise all
        results are returned.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    list
        list of Isotherms
    """

    cursor = kwargs['cursor']

    # Default value
    criteria = criteria if criteria else {}

    # Get isotherm info from database
    cursor.execute(
        build_select(table='isotherms', to_select="*", where=criteria.keys()),
        criteria
    )

    isotherms = []
    alldata = cursor.fetchall()

    for rows in grouped(alldata, 100):  # we are taking 100 isotherms at a time

        ids = tuple(row['id'] for row in rows)

        # Get isotherm properties from database
        cursor.execute(
            f"""SELECT iso_id, type, value FROM "isotherm_properties"
                WHERE iso_id IN ({','.join('?' * len(ids))});""", ids
        )
        isotherm_props = cursor.fetchall()

        # Get the properties from the data table
        cursor.execute(
            f"""SELECT iso_id, type, data FROM "isotherm_data"
                WHERE iso_id IN ({','.join('?' * len(ids))});""", ids
        )
        isotherm_data = cursor.fetchall()

        for row in rows:

            # Generate the isotherm parameters dictionary
            iso_params = dict(zip(row.keys(), row))
            iso_params.update({
                prop[1]: checkSQLbool(prop[2])
                for prop in isotherm_props
                if prop[0] == row['id']
            })
            iso_params.pop('id')

            # Generate the isotherm data/model
            if row['iso_type'] == 'pointisotherm':
                iso_data = pandas.DataFrame({
                    data[1]: array.array('d', data[2])
                    for data in isotherm_data
                    if data[0] == row['id']
                })
                other_keys = [
                    key for key in iso_data.columns
                    if key not in ('pressure', 'loading')
                ]
                iso_params.update({'other_keys': other_keys})

                # build isotherm object
                isotherms.append(
                    PointIsotherm(
                        isotherm_data=iso_data,
                        pressure_key="pressure",
                        loading_key="loading",
                        **iso_params
                    )
                )

            elif row['iso_type'] == 'modelisotherm':

                iso_model = model_from_dict(
                    next(
                        json.loads(data['data'])
                        for data in isotherm_data
                        if data[0] == row['id']
                    )
                )

                # build isotherm object
                isotherms.append(ModelIsotherm(model=iso_model, **iso_params))

            else:
                # build isotherm object
                isotherms.append(BaseIsotherm(**iso_params))

    if verbose:
        # Print success
        logger.info(f"Selected {len(isotherms)} isotherms")

    return isotherms


@with_connection
def isotherm_delete_db(iso_id, db_path=None, verbose=True, **kwargs):
    """
    Delete isotherm in the database.

    Parameters
    ----------
    isotherm : Isotherm or Isotherm.iso_id
        The Isotherm object to delete from the database or its ID.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """

    if isinstance(iso_id, BaseIsotherm):
        iso_id = iso_id.iso_id

    cursor = kwargs['cursor']

    # Check if isotherm exists
    ids = cursor.execute(
        build_select(table='isotherms', to_select=['id'], where=['id']), {
            'id': iso_id
        }
    ).fetchone()

    if ids is None:
        raise sqlite3.IntegrityError(
            "Isotherm to delete does not exist in database. Did you modify any parameters?"
        )

    # Delete data from isotherm_data table
    cursor.execute(
        build_delete(table='isotherm_data', where=['iso_id']),
        {'iso_id': iso_id}
    )

    # Delete properties from isotherm_properties table
    cursor.execute(
        build_delete(table='isotherm_properties', where=['iso_id']),
        {'iso_id': iso_id}
    )

    # Delete isotherm in isotherms table
    cursor.execute(
        build_delete(table='isotherms', where=['id']), {'id': iso_id}
    )

    if verbose:
        # Print success
        logger.info(f"Isotherm deleted: '{iso_id}'")


@with_connection
def isotherm_type_to_db(
    type_dict, db_path=None, overwrite=False, verbose=True, **kwargs
):
    """
    Upload an isotherm type.

    The type_dict takes the form of::

        {
            'type' : 'the_type',
            'unit': 'the_unit',
            'description': 'the_description'
        }

    Parameters
    ----------
    type_dict : dict
        A dictionary that contains isotherm type.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    overwrite : bool
        Whether to upload the isotherm type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Extra information printed to console.
    """
    _upload_one_all_columns(
        kwargs['cursor'],
        'isotherm_type',
        'type',
        ['description'],
        type_dict,
        overwrite,
        'Experiment type',
        verbose,
    )


@with_connection
def isotherm_types_from_db(db_path=None, verbose=True, **kwargs):
    """
    Get all isotherm types.

    Parameters
    ----------
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    dict
        dict of isotherm types
    """
    return _get_all_no_id(
        kwargs['cursor'],
        'isotherm_type',
        'id',
        'isotherm types',
        verbose,
    )


@with_connection
def isotherm_type_delete_db(iso_type, db_path=None, verbose=True, **kwargs):
    """
    Delete isotherm type in the database.

    Parameters
    ----------
    data_type : str
        The type to delete.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """
    _delete_by_id(
        kwargs['cursor'],
        'isotherm_type',
        'type',
        iso_type,
        'isotherm types',
        verbose,
    )


@with_connection
def isotherm_property_type_to_db(
    type_dict, db_path=None, overwrite=False, verbose=True, **kwargs
):
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
    type_dict : dict
        A dictionary that contains property type.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    overwrite : bool
        Whether to upload the property type or overwrite it.
        WARNING: Overwrite is done on ALL fields.
    verbose : bool
        Extra information printed to console.
    """
    _upload_one_all_columns(
        kwargs['cursor'],
        'isotherm_properties_type',
        'type',
        ['unit', 'description'],
        type_dict,
        overwrite,
        'Experiment property type',
        verbose,
    )


@with_connection
def isotherm_property_types_from_db(db_path=None, verbose=True, **kwargs):
    """
    Get all isotherm property types.

    Parameters
    ----------
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.

    Returns
    -------
    dict
        dict of property types
    """
    return _get_all_no_id(
        kwargs['cursor'],
        'isotherm_properties_type',
        'id',
        'isotherm property types',
        verbose,
    )


@with_connection
def isotherm_property_type_delete_db(
    property_type, db_path=None, verbose=True, **kwargs
):
    """
    Delete isotherm property type in the database.

    Parameters
    ----------
    property_type : str
        Property type to delete.
    db_path : str, None
        Path to the database. If none is specified, internal database is used.
    verbose : bool
        Extra information printed to console.
    """
    _delete_by_id(
        kwargs['cursor'],
        'isotherm_properties_type',
        'type',
        property_type,
        'isotherm property types',
        verbose,
    )
