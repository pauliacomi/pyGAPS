"""
This module contains the sql interface for data manipulation.
"""

import array
import sqlite3

import numpy
import pandas

from ..classes.adsorbate import Adsorbate
from ..classes.pointisotherm import Isotherm
from ..classes.pointisotherm import PointIsotherm
from ..classes.sample import Sample
from ..utilities.exceptions import ParsingError
from ..utilities.sqlite_utilities import build_delete
from ..utilities.sqlite_utilities import build_insert
from ..utilities.sqlite_utilities import build_select
from ..utilities.sqlite_utilities import build_select_unnamed
from ..utilities.sqlite_utilities import build_update

# ---------------------- General functions


def _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, input_dict, name_string):

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

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

        # Print success
        print(name_string, "uploaded", insert_dict.get(table_id))

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on:", "\n",
              input_dict.get(table_id),
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()


def _get_all_no_id(pth, table_id, table_name, name_string):
    """Gets all elements from a table as a dictionary, excluding id"""
    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM ''' + table_name)

        # Get the types
        types = []
        for row in cursor:
            unit = dict(zip(row.keys(), row))
            unit.pop(table_id)
            types.append(unit)

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(types), name_string)
    return types


def _delete_one_by_id(pth, table_name, table_id, element_id, name_string):
    """Gets all elements from a table as a dictionary, excluding id"""
    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

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

            # Print success
            print("Success, deleted", name_string, element_id)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on:", "\n",
              element_id,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

# ---------------------- Samples


def db_upload_sample(pth, sample, overwrite=False):
    """
    Uploads samples to the database.
    If overwrite is set to true, the sample is overwritten
    Overwrite is done based on sample.name + sample.batch
    WARNING: Overwrite is done on ALL fields.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            if overwrite:
                sql_com = build_update(table="samples",
                                       to_set=Sample._named_params,
                                       where=['name', 'batch'])
            else:
                to_insert = ['name', 'batch'] + Sample._named_params
                sql_com = build_insert(table="samples",
                                       to_insert=to_insert)

            sample_dict = sample.to_dict()
            upload_dict = {'name': sample.name, 'batch': sample.batch}
            for prop in Sample._named_params:
                if prop in sample_dict:
                    upload_dict.update({prop: sample_dict[prop]})
                else:
                    upload_dict.update({prop: ""})

            # Upload or modify data in sample table
            cursor.execute(sql_com, upload_dict)

            # Upload or modify data in sample_properties table
            if sample.properties and len(sample.properties) > 0:
                # Get id of sample
                sample_id = cursor.execute(
                    build_select(table='samples',
                                 to_select=['id'],
                                 where=['name', 'batch']), {
                        'name':        sample.name,
                        'batch':       sample.batch,
                    }
                ).fetchone()[0]

                # Sql of update routine
                sql_update = build_update(table='sample_properties',
                                          to_set=['type', 'value'],
                                          where=['sample_id'])
                # Sql of insert routine
                sql_insert = build_insert(table='sample_properties',
                                          to_insert=['sample_id', 'type', 'value'])

                updates = []

                if overwrite:
                    # Find existing properties
                    cursor.execute(
                        build_select(table='sample_properties',
                                     to_select=['type'],
                                     where=['sample_id']), {
                            'sample_id':        sample_id,
                        }
                    )
                    updates = [elt[0] for elt in cursor.fetchall()]

                for prop in sample.properties:
                    if prop is not None:
                        if prop in updates:
                            sql_com_prop = sql_update
                        else:
                            sql_com_prop = sql_insert

                        cursor.execute(sql_com_prop, {
                            'sample_id':        sample_id,
                            'type':             prop,
                            'value':            sample.properties[prop]
                        })

        # Print success
        print("Sample uploaded", sample.name, sample.batch)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample:", "\n",
              sample.name,
              sample.batch,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_get_samples(pth):
    """
    Gets all samples and their properties.

    The number of samples is usually small, so all can be loaded in memory at once.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM samples''')

        samples = []

        # Create the samples
        for row in cursor:

            sample_params = dict(zip(row.keys(), row))

            # Get the extra data from the sample_properties table
            cur_inner = db.cursor()

            cur_inner.execute(build_select(table='sample_properties',
                                           to_select=['type', 'value'],
                                           where=['sample_id']), {
                'sample_id':        sample_params.pop('id')
            })

            sample_params.update({
                row[0]: row[1] for row in cur_inner})

            # Build sample objects
            samples.append(Sample(**sample_params))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(samples), "samples")

    return samples


def db_delete_sample(pth, sample):
    """
    Delete sample from the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Get id of sample
            sample_ids = cursor.execute(
                build_select(table='samples',
                             to_select=['id'],
                             where=['name', 'batch']), {
                    'name':        sample.name,
                    'batch':       sample.batch,
                }
            ).fetchone()

            if sample_ids is None:
                raise sqlite3.IntegrityError(
                    "Sample to delete does not exist in database")

            # Delete data from sample_properties table
            # Build sql request
            sql_com = build_delete(table='sample_properties',
                                   where=['sample_id'])

            cursor.execute(sql_com, {'sample_id': sample_ids[0]})

            # Delete sample info in samples table
            sql_com = build_delete(table='samples',
                                   where=['id'])

            cursor.execute(sql_com, {'id': sample_ids[0]})

            # Print success
            print("Success", sample.name, sample.batch)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample:", "\n",
              sample.name,
              sample.batch,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_upload_sample_type(pth, type_dict, overwrite=False):
    """
    Uploads a sample type.
    """

    table_name = 'sample_type'
    name_string = 'Sample type'
    table_id = 'type'
    columns = ['name']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, type_dict, name_string)

    return


def db_get_sample_types(pth):
    """
    Gets all sample types.
    """

    table = 'sample_type'
    name_string = 'sample types'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_sample_type(pth, sample_type):
    """
    Delete sample type in the database.
    """

    table_id = 'type'
    table_name = 'sample_type'
    name_string = 'sample types'

    _delete_one_by_id(pth, table_name, table_id, sample_type, name_string)

    return


def db_upload_sample_property_type(pth, type_dict, overwrite=False):
    """
    Uploads a sample property type.
    """

    table_name = 'sample_properties_type'
    name_string = 'Sample properties type'
    table_id = 'type'
    columns = ['unit']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, type_dict, name_string)

    return


def db_get_sample_property_types(pth):
    """
    Gets all sample property types.
    """

    table = 'sample_properties_type'
    name_string = 'sample property types'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_sample_property_type(pth, sample_prop_type):
    """
    Delete sample property type in the database.
    """

    table_id = 'type'
    table_name = 'sample_properties_type'
    name_string = 'sample property types'

    _delete_one_by_id(pth, table_name, table_id, sample_prop_type, name_string)

    return


# ---------------------- Experiments


def db_upload_experiment(pth, isotherm, overwrite=None):
    """
    Uploads experiment to the database.

    Overwrite is the isotherm id where the data will be overwritten.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # First, if the goal was to overwrite an isotherm, must delete old data
            if overwrite:
                db_delete_experiment(pth, overwrite)

            # Then, the sample is going to be inserted into the database
            # Build SQL request
            sql_com = build_insert(table='experiments',
                                   to_insert=Isotherm._db_columns)

            # Build upload dict
            upload_dict = {}
            iso_dict = isotherm.to_dict()
            for param in Isotherm._db_columns:
                upload_dict.update({param: iso_dict.pop(param, None)})

            # Upload experiment info to database
            cursor.execute(sql_com, upload_dict)

            # Then, the isotherm data will be uploaded
            # into the experiment_data table

            # Build sql request
            sql_insert = build_insert(table='experiment_data',
                                      to_insert=['exp_id', 'type', 'data'])

            # Insert standard data fields:
            cursor.execute(sql_insert,
                           {'exp_id': isotherm.id, 'type': 'pressure',
                            'data': isotherm.pressure().tobytes()}
                           )

            cursor.execute(sql_insert,
                           {'exp_id': isotherm.id, 'type': 'loading',
                            'data': isotherm.loading().tobytes()}
                           )

            # Update or insert other fields:
            for key in isotherm.other_keys:
                cursor.execute(sql_insert,
                               {'exp_id': isotherm.id, 'type': key,
                                'data': isotherm.other_data(key).tobytes()}
                               )

            # Upload the remaining data from the isotherm
            # Build sql request
            sql_insert = build_insert(table='experiment_properties',
                                      to_insert=['exp_id', 'type', 'value'])
            for key in iso_dict:
                cursor.execute(sql_insert,
                               {'exp_id': isotherm.id,
                                'type': key,
                                'value': iso_dict[key]
                                })

        # Print success
        print("Success:", isotherm)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on isotherm:", "\n",
              isotherm.exp_type,
              isotherm.sample_name,
              isotherm.sample_batch,
              isotherm.user,
              isotherm.adsorbate,
              isotherm.machine,
              isotherm.t_act,
              isotherm.t_exp,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_get_experiments(pth, criteria):
    """
    Gets experiments with the selected criteria from the database.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Get experiment info from database
        sql_exp = build_select(table='experiments',
                               to_select=Isotherm._db_columns,
                               where=criteria.keys())

        cursor.execute(sql_exp, criteria)
        experiments = cursor.fetchall()

        # Create the isotherm list
        isotherms = []

        if len(experiments) > 0:

            ids = tuple(exp['id'] for exp in experiments)

            # Get experiment properties from database
            sql_exp_props = build_select_unnamed(table='experiment_properties',
                                                 to_select=[
                                                     'exp_id', 'type', 'value'],
                                                 where=['exp_id' for exp_id in ids], join='OR')

            cursor.execute(sql_exp_props, ids)
            experiment_props = cursor.fetchall()

            # Get the properties from the experiment_properties table
            sql_exp_data = build_select_unnamed(table='experiment_data',
                                                to_select=[
                                                    'exp_id', 'type', 'data'],
                                                where=['exp_id' for exp_id in ids], join='OR')
            cursor.execute(sql_exp_data, ids)
            experiment_data = cursor.fetchall()

            for exp in experiments:

                # Generate the array for the pandas dataframe
                columns = []
                other_keys = []
                data_arr = None
                for data in experiment_data:
                    if data[0] == exp['id']:

                        columns.append(data[1])
                        raw = array.array('d', data[2])
                        if data_arr is None:
                            data_arr = numpy.expand_dims(
                                numpy.array(raw), axis=1)
                        else:
                            data_arr = numpy.hstack(
                                (data_arr, numpy.expand_dims(numpy.array(raw), axis=1)))

                        if data[1] not in ('pressure', 'loading'):
                            other_keys.append(data[1])

                exp_data = pandas.DataFrame(data_arr, columns=columns)

                # Generate the experiment parameters dictionary
                exp_params = dict(zip(exp.keys(), exp))
                exp_params.update(
                    {prop[1]: prop[2]
                        for prop in experiment_props if prop[0] == exp['id']})
                exp_params.update({'other_keys': other_keys})
                exp_params.pop('id')

                # build isotherm object
                isotherms.append(PointIsotherm(exp_data,
                                               pressure_key="pressure",
                                               loading_key="loading",
                                               ** exp_params))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(isotherms), "isotherms")

    return isotherms


def db_delete_experiment(pth, isotherm):
    """
    Delete experiment in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if sample exists
            ids = cursor.execute(
                build_select(table='experiments',
                             to_select=['id'],
                             where=['id']),
                {'id':        isotherm.id}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Experiment to delete does not exist in database")

            # Delete data from experiment_data table
            cursor.execute(build_delete(table='experiment_data',
                                        where=['exp_id']), {'exp_id': isotherm.id})

            # Delete data from experiment_data table
            cursor.execute(build_delete(table='experiment_properties',
                                        where=['exp_id']), {'exp_id': isotherm.id})

            # Delete experiment info in experiments table
            cursor.execute(build_delete(table='experiments',
                                        where=['id']), {'id': isotherm.id})

            # Print success
            print("Success:", isotherm)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on isotherm:", "\n",
              isotherm.exp_type,
              isotherm.sample_name,
              isotherm.sample_batch,
              isotherm.user,
              isotherm.adsorbate,
              isotherm.machine,
              isotherm.t_act,
              isotherm.t_exp,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_upload_experiment_type(pth, type_dict, overwrite=False):
    """
    Uploads a experiment type.
    """

    table_name = 'experiment_type'
    name_string = 'Experiment type'
    table_id = 'type'
    columns = ['name']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, type_dict, name_string)

    return


def db_get_experiment_types(pth):
    """
    Gets all sample types.
    """

    table = 'experiment_type'
    name_string = 'experiment types'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_experiment_type(pth, exp_type):
    """
    Delete experiment type in the database.
    """

    table_id = 'type'
    table_name = 'experiment_type'
    name_string = 'experiment types'

    _delete_one_by_id(pth, table_name, table_id, exp_type, name_string)

    return


def db_upload_experiment_property_type(pth, type_dict, overwrite=False):
    """
    Uploads a property type.
    """

    table_name = 'experiment_properties_type'
    name_string = 'Experiment property type'
    table_id = 'type'
    columns = ['unit']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, type_dict, name_string)

    return


def db_get_experiment_property_types(pth):
    """
    Gets all experiment property types.
    """

    table = 'experiment_properties_type'
    name_string = 'experiment property types'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_experiment_property_type(pth, property_type):
    """
    Delete experiment property type in the propertybase.
    """

    table_id = 'type'
    table_name = 'experiment_properties_type'
    name_string = 'experiment property types'

    _delete_one_by_id(pth, table_name, table_id, property_type, name_string)

    return


def db_upload_experiment_data_type(pth, type_dict, overwrite=False):
    """
    Uploads a data type.
    """

    table_name = 'experiment_data_type'
    name_string = 'Experiment data type'
    table_id = 'type'
    columns = ['unit']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, type_dict, name_string)

    return


def db_get_experiment_data_types(pth):
    """
    Gets all experiment data types.
    """

    table = 'experiment_data_type'
    name_string = 'experiment data types'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_experiment_data_type(pth, data_type):
    """
    Delete experiment data type in the database.
    """

    table_id = 'type'
    table_name = 'experiment_data_type'
    name_string = 'experiment data types'

    _delete_one_by_id(pth, table_name, table_id, data_type, name_string)

    return


# ---------------------- Adsorbates


def db_upload_adsorbate(pth, adsorbate, overwrite=False):
    """
    Uploads adsorbates to the database.

    If overwrite is set to true, the adsorbate is overwritten
    Overwrite is done based on adsorbate.name
    WARNING: Overwrite is done on ALL fields
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            if overwrite:
                sql_com = build_update(table="adsorbates",
                                       to_set=['formula'],
                                       where=['nick'])
            else:
                sql_com = build_insert(table="adsorbates",
                                       to_insert=['nick', 'formula'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'nick':         adsorbate.name,
                'formula':      adsorbate.formula,
            }
            )

            # Upload or modify data in the table
            if len(adsorbate.properties) > 0:
                # Get id of adsorbate
                ads_id = cursor.execute(
                    build_select(table='adsorbates',
                                 to_select=['id'],
                                 where=['nick']), {
                        'nick':         adsorbate.name,
                        'formula':      adsorbate.formula,
                    }
                ).fetchone()[0]

                # Sql of update routine
                sql_update = build_update(table='adsorbate_properties',
                                          to_set=['type', 'value'],
                                          where=['ads_id'])
                # Sql of insert routine
                sql_insert = build_insert(table='adsorbate_properties',
                                          to_insert=['ads_id', 'type', 'value'])

                updates = []

                if overwrite:
                    # Find existing properties
                    cursor.execute(
                        build_select(table='adsorbate_properties',
                                     to_select=['type'],
                                     where=['ads_id']), {
                            'ads_id':        ads_id,
                        }
                    )
                    updates = [elt[0] for elt in cursor.fetchall()]

                for prop in adsorbate.properties:
                    if prop in updates:
                        sql_com_prop = sql_update
                    else:
                        sql_com_prop = sql_insert

                    cursor.execute(sql_com_prop, {
                        'ads_id':           ads_id,
                        'type':             prop,
                        'value':            adsorbate.properties[prop]
                    })

        # Print success
        print("Adsorbate uploaded", adsorbate.name)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on adsorbate:", "\n",
              adsorbate.name,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_get_adsorbates(pth):
    """
    Gets all adsorbates and their properties.

    The number of adsorbates is usually small, so all can be
    loaded in memory at once.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Get required adsorbate from database
        cursor.execute('''SELECT * FROM adsorbates''')

        adsorbates = []

        # Create the adsorbates
        for row in cursor:

            adsorbate_params = dict(zip(row.keys(), row))

            # Get the extra data from the adsorbate_properties table
            cur_inner = db.cursor()

            cur_inner.execute(
                build_select(table='adsorbate_properties',
                             to_select=['type', 'value'],
                             where=['ads_id']),
                {'ads_id': adsorbate_params.pop('id')}
            )

            adsorbate_params.update({
                row[0]: row[1] for row in cur_inner})

            # Build adsorbate objects
            adsorbates.append(Adsorbate(**adsorbate_params))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(adsorbates), "adsorbates")

    return adsorbates


def db_delete_adsorbate(pth, adsorbate):
    """
    Delete adsorbate from the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Get id of adsorbate
            ids = cursor.execute(
                build_select(table='adsorbates',
                             to_select=['id'],
                             where=['nick']),
                {'nick':        adsorbate.name}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Adsorbate to delete does not exist in database")
            ads_id = ids[0]

            # Delete data from adsorbate_properties table
            # Build sql request
            sql_com = build_delete(table='adsorbate_properties',
                                   where=['ads_id'])

            cursor.execute(sql_com, {'ads_id': ads_id})

            # Delete sample info in adsorbate table
            sql_com = build_delete(table='adsorbates',
                                   where=['id'])

            cursor.execute(sql_com, {'id': ads_id})

            # Print success
            print("Success", adsorbate.name)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample:", "\n",
              adsorbate.name,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_upload_adsorbate_property_type(pth, type_dict, overwrite=False):
    """
    Uploads an adsorbate property type.
    """

    table_name = 'adsorbate_properties_type'
    name_string = 'Property type'
    table_id = 'type'
    columns = ['unit']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, type_dict, name_string)

    return


def db_get_adsorbate_property_types(pth):
    """
    Gets all adsorbate property types.
    """

    table = 'adsorbate_properties_type'
    name_string = 'adsorbate property types'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_adsorbate_property_type(pth, property_type):
    """
    Delete property type in the database.
    """

    table_id = 'type'
    table_name = 'adsorbate_properties_type'
    name_string = 'adsorbate property types'

    _delete_one_by_id(pth, table_name, table_id, property_type, name_string)

    return


# ---------------------- Contacts


def db_upload_contact(pth, contact_dict, overwrite=False):
    """
    Uploads comtact to the database.

    If overwrite is set to true, the contact is overwritten.
    WARNING: Overwrite is done on ALL fields.
    """

    table_name = 'contacts'
    name_string = 'Contact'
    table_id = 'nick'
    columns = ['name', 'email', 'phone']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, contact_dict, name_string)

    return


def db_get_contacts(pth):
    """
    Gets all contacts.
    """

    table = 'contacts'
    name_string = 'contacts'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_contact(pth, contact_nick):
    """
    Delete contact in the database.
    """

    table_id = 'nick'
    table_name = 'contacts'
    name_string = 'contact'

    _delete_one_by_id(pth, table_name, table_id, contact_nick, name_string)

    return

# ---------------------- Sources


def db_upload_source(pth, source_dict, overwrite=False):
    """
    Uploads source to the database.

    If overwrite is set to true, the source is overwritten.
    WARNING: Overwrite is done on ALL fields.
    """

    table_name = 'sources'
    name_string = 'Source'
    table_id = 'nick'
    columns = ['name']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, source_dict, name_string)

    return


def db_get_sources(pth):
    """
    Gets all sources.
    """

    table = 'sources'
    name_string = 'sources'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_source(pth, source_nick):
    """
    Delete source in the database.
    """

    table_id = 'nick'
    table_name = 'sources'
    name_string = 'source'

    _delete_one_by_id(pth, table_name, table_id, source_nick, name_string)

    return


# ---------------------- Machines


def db_upload_machine(pth, machine_dict, overwrite=False):
    """
    Uploads machine to the database.

    If overwrite is set to true, the machine is overwritten.
    WARNING: Overwrite is done on ALL fields.
    """

    table_name = 'machines'
    name_string = 'Machine'
    table_id = 'nick'
    columns = ['name', 'type']

    _upload_one_all_columns(pth, table_id, columns, overwrite,
                            table_name, machine_dict, name_string)

    return


def db_get_machines(pth):
    """
    Gets all machines.
    """

    table = 'machines'
    name_string = 'machines'
    table_id = 'id'

    return _get_all_no_id(pth, table_id, table, name_string)


def db_delete_machine(pth, machine_nick):
    """
    Delete machine in the database.
    """

    table_id = 'nick'
    table_name = 'machines'
    name_string = 'machine'

    _delete_one_by_id(pth, table_name, table_id, machine_nick, name_string)

    return
