"""
This module contains the sql interface for data manipulation.
"""

import array
import sqlite3

import numpy
import pandas

from ..classes.adsorbate import Adsorbate
from ..classes.pointisotherm import PointIsotherm
from ..classes.sample import Sample
from ..utilities.exceptions import ParsingError
from ..utilities.sqlite_utilities import build_delete
from ..utilities.sqlite_utilities import build_insert
from ..utilities.sqlite_utilities import build_select
from ..utilities.sqlite_utilities import build_update


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
                                       to_set=['project', 'struct', 'type',
                                               'contact', 'form', 'source', 'comment'],
                                       where=['name', 'batch'])
            else:
                sql_com = build_insert(table="samples",
                                       to_insert=['name', 'batch', 'project', 'struct', 'type',
                                                  'contact', 'form', 'source', 'comment'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'name':         sample.name,
                'batch':        sample.batch,

                'contact':      sample.contact,
                'source':       sample.source,
                'type':         sample.type,

                'project':      sample.project,
                'struct':       sample.struct,
                'form':         sample.form,
                'comment':      sample.comment,
            }
            )

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
                'sample_id':        sample_params.get('id')
            })

            sample_params['properties'] = {
                row[0]: row[1] for row in cur_inner}

            # Build sample objects
            samples.append(Sample(sample_params))

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


def db_upload_sample_type(pth, sample_type):
    """
    Uploads a sample type.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            sql_com = build_insert(table="sample_type",
                                   to_insert=['type', 'name'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'type':         sample_type.get('type'),
                'name':         sample_type.get('name'),
            }
            )

        # Print success
        print("Sample type uploaded", sample_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample type:", "\n",
              sample_type['type'],
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()


def db_get_sample_types(pth):
    """
    Gets all sample types.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM sample_type''')

        # Get the types
        types = []
        for row in cursor:
            types.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(types), "sample types")

    return types


def db_delete_sample_type(pth, sample_type):
    """
    Delete sample type in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if source exists
            ids = cursor.execute(
                build_select(table='sample_type',
                             to_select=['type'],
                             where=['type']),
                {'type':        sample_type}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Property type to delete does not exist in database")

            sql_com = build_delete(table='sample_type',
                                   where=['type'])

            cursor.execute(sql_com, {'type': sample_type})

            # Print success
            print("Success", sample_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample type:", "\n",
              sample_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_upload_sample_property_type(pth, property_type):
    """
    Uploads a sample property type.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            sql_com = build_insert(table="sample_properties_type",
                                   to_insert=['type', 'unit'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'type':         property_type.get('type'),
                'unit':         property_type.get('unit'),
            }
            )

        # Print success
        print("Property type uploaded", property_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample property type:", "\n",
              property_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()


def db_get_sample_property_types(pth):
    """
    Gets all sample property types.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM sample_properties_type''')

        # Get the types
        types = []
        for row in cursor:
            types.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(types), "sample property types")

    return types


def db_delete_sample_property_type(pth, sample_type):
    """
    Delete sample property type in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if source exists
            ids = cursor.execute(
                build_select(table='sample_properties_type',
                             to_select=['type'],
                             where=['type']),
                {'type':        sample_type}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Property type to delete does not exist in database")

            sql_com = build_delete(table='sample_properties_type',
                                   where=['type'])

            cursor.execute(sql_com, {'type': sample_type})

            # Print success
            print("Success", sample_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample property type:", "\n",
              sample_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


# ---------------------- Experiments


EXP_NAMED_PARAMS = [
                'id',
                'sample_name',
                'sample_batch',
                't_exp',
                'adsorbate',
                'user',
                'machine',
                'exp_type',
                'date',
                'is_real',
                't_act',
                'lab',
                'project',
                'comment',
]


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
                                   to_insert=EXP_NAMED_PARAMS)

            # Build upload dict
            upload_dict = {}
            iso_dict = isotherm.to_dict()
            for param in EXP_NAMED_PARAMS:
                upload_dict.update({param: iso_dict.get(param)})

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

        # Build SQL request
        sql_com = build_select(table='experiments',
                               to_select=EXP_NAMED_PARAMS,
                               where=criteria.keys())

        # Get experiment info from database
        cursor.execute(sql_com, criteria)

        # Create the isotherms
        isotherms = []

        for row in cursor:
            exp_params = dict(zip(row.keys(), row))

            # Get the extra data from the experiment_data table
            cur_inner = db.cursor()

            cur_inner.execute(build_select(table='experiment_data',
                                           to_select=['type', 'data'],
                                           where=['exp_id']),
                              {'exp_id': str(exp_params['id'])}
                              )

            # Generate the array for the pandas dataframe
            columns = []
            other_keys = []
            data_arr = None
            for row in cur_inner:
                columns.append(row[0])

                raw = array.array('d', row[1])
                if data_arr is None:
                    data_arr = numpy.expand_dims(numpy.array(raw), axis=1)
                else:
                    data_arr = numpy.hstack(
                        (data_arr, numpy.expand_dims(numpy.array(raw), axis=1)))

            if row[0] not in ('pressure', 'loading'):
                other_keys.append(row[0])

            exp_data = pandas.DataFrame(data_arr, columns=columns)

            # build isotherm object
            isotherms.append(PointIsotherm(exp_data,
                                           pressure_key="pressure",
                                           loading_key="loading",
                                           other_keys=other_keys,
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


def db_upload_experiment_type(pth, experiment_type):
    """
    Uploads a experiment type.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            sql_com = build_insert(table="experiment_type",
                                   to_insert=['type', 'name'])

            # Upload or modify data in experiment table
            cursor.execute(sql_com, {
                'type':         experiment_type.get('type'),
                'name':         experiment_type.get('name'),
            }
            )

        # Print success
        print("Experiment type uploaded", experiment_type['type'])

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on experiment type:", "\n",
              experiment_type['type'],
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()


def db_get_experiment_types(pth):
    """
    Gets all sample types.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM experiment_type''')

        # Get the types
        types = []
        for row in cursor:
            types.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(types), "experiment types")

    return types


def db_delete_experiment_type(pth, exp_type):
    """
    Delete experiment type in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if source exists
            ids = cursor.execute(
                build_select(table='experiment_type',
                             to_select=['type'],
                             where=['type']),
                {'type':        exp_type}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Property type to delete does not exist in database")

            sql_com = build_delete(table='experiment_type',
                                   where=['type'])

            cursor.execute(sql_com, {'type': exp_type})

            # Print success
            print("Success", exp_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on experiment type:", "\n",
              exp_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_upload_experiment_data_type(pth, data_type):
    """
    Uploads a data type.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            sql_com = build_insert(table="experiment_data_type",
                                   to_insert=['type', 'unit'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'type':         data_type.get('type'),
                'unit':         data_type.get('unit'),
            }
            )

        # Print success
        print("Data type uploaded", data_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample:", "\n",
              data_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()


def db_get_experiment_data_types(pth):
    """
    Gets all experiment data types.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM experiment_data_type''')

        # Get the types
        types = []
        for row in cursor:
            types.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(types), "experiment data types")

    return types


def db_delete_experiment_data_type(pth, data_type):
    """
    Delete experiment data type in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if source exists
            ids = cursor.execute(
                build_select(table='experiment_data_type',
                             to_select=['type'],
                             where=['type']),
                {'type':        data_type}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Property type to delete does not exist in database")

            sql_com = build_delete(table='experiment_data_type',
                                   where=['type'])

            cursor.execute(sql_com, {'type': data_type})

            # Print success
            print("Success", data_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on experiment data type:", "\n",
              data_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

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

            # Upload or modify data in sample_properties table
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
        print("Error on sample:", "\n",
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

            cur_inner.execute(build_select(table='adsorbate_properties',
                                           to_select=['type', 'value'],
                                           where=['ads_id']), {
                'ads_id': adsorbate_params.get('id')
            })

            adsorbate_params['properties'] = {
                row[0]: row[1] for row in cur_inner}

            # Build adsorbate objects
            adsorbates.append(Adsorbate(adsorbate_params))

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


def db_upload_adsorbate_property_type(pth, property_type):
    """
    Uploads an adsorbate property type.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            sql_com = build_insert(table="adsorbate_properties_type",
                                   to_insert=['type', 'unit'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'type':         property_type.get('type'),
                'unit':         property_type.get('unit'),
            }
            )

        # Print success
        print("Property type uploaded", property_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample:", "\n",
              property_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()


def db_get_adsorbate_property_types(pth):
    """
    Gets all adsorbate property types.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM adsorbate_properties_type''')

        # Get the types
        types = []
        for row in cursor:
            types.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(types), "adsorbate property types")

    return types


def db_delete_adsorbate_property_type(pth, property_type):
    """
    Delete property type in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if source exists
            ids = cursor.execute(
                build_select(table='adsorbate_properties_type',
                             to_select=['type'],
                             where=['type']),
                {'type':        property_type}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Property type to delete does not exist in database")

            sql_com = build_delete(table='adsorbate_properties_type',
                                   where=['type'])

            cursor.execute(sql_com, {'type': property_type})

            # Print success
            print("Success", property_type)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on type:", "\n",
              property_type,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


# ---------------------- Contacts


def db_upload_contact(pth, contact_dict, overwrite=False):
    """
    Uploads comtact to the database.

    If overwrite is set to true, the contact is overwritten.
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
                sql_com = build_update(table="contacts",
                                       to_set=['name', 'email', 'phone'],
                                       where=['nick'])
            else:
                sql_com = build_insert(table="contacts",
                                       to_insert=['nick', 'name', 'email', 'phone'])

            # Upload or modify data in sample table
            cursor.execute(sql_com, {
                'nick':          contact_dict.get('nick'),
                'name':          contact_dict.get('name'),
                'email':         contact_dict.get('email'),
                'phone':         contact_dict.get('phone'),
            }
            )

        # Print success
        print("Contact uploaded", contact_dict.get('nick'))

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on contact:", "\n",
              contact_dict.get('nick'),
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_get_contacts(pth):
    """
    Gets all contacts.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM contacts''')

        # Get the contacts
        contacts = []
        for row in cursor:
            contacts.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(contacts))

    return contacts


def db_delete_contact(pth, contact_nick):
    """
    Delete contact in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if contact exists
            ids = cursor.execute(
                build_select(table='contacts',
                             to_select=['nick'],
                             where=['nick']),
                {'nick':        contact_nick}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Contact to delete does not exist in database")

            sql_com = build_delete(table='contacts',
                                   where=['nick'])

            cursor.execute(sql_com, {'nick': contact_nick})

            # Print success
            print("Success", contact_nick)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on sample:", "\n",
              contact_nick,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return

# ---------------------- Sources


def db_upload_source(pth, source_dict, overwrite=False):
    """
    Uploads source to the database.

    If overwrite is set to true, the source is overwritten.
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
                sql_com = build_update(table="sources",
                                       to_set=['name'],
                                       where=['nick'])
            else:
                sql_com = build_insert(table="sources",
                                       to_insert=['nick', 'name'])

            # Upload or modify data in sources table
            cursor.execute(sql_com, {
                'nick':         source_dict.get('nick'),
                'name':         source_dict.get('name'),
            }
            )

        # Print success
        print("Source uploaded", source_dict.get('nick'))

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on source:", "\n",
              source_dict.get('nick'),
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_get_sources(pth):
    """
    Gets all sources.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM sources''')

        # Get the sources
        sources = []
        for row in cursor:
            sources.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(sources))

    return sources


def db_delete_source(pth, source_nick):
    """
    Delete source in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if source exists
            ids = cursor.execute(
                build_select(table='sources',
                             to_select=['nick'],
                             where=['nick']),
                {'nick':        source_nick}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Source to delete does not exist in database")

            sql_com = build_delete(table='sources',
                                   where=['nick'])

            cursor.execute(sql_com, {'nick': source_nick})

            # Print success
            print("Success", source_nick)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on source:", "\n",
              source_nick,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return

# ---------------------- Machines


def db_upload_machine(pth, machine_dict, overwrite=False):
    """
    Uploads machine to the database.

    If overwrite is set to true, the machine is overwritten.
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
                sql_com = build_update(table="machines",
                                       to_set=['name', 'type'],
                                       where=['nick'])
            else:
                sql_com = build_insert(table="machines",
                                       to_insert=['nick', 'name', 'type'])

            # Upload or modify data in machines table
            cursor.execute(sql_com, {
                'nick':         machine_dict.get('nick'),
                'name':         machine_dict.get('name'),
                'type':         machine_dict.get('type'),
            }
            )

        # Print success
        print("Machine uploaded", machine_dict.get('nick'))

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on machine:", "\n",
              machine_dict.get('nick'),
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return


def db_get_machines(pth):
    """
    Gets all machines.
    """

    # Connect to database
    with sqlite3.connect(pth) as db:

        # Set row factory
        db.row_factory = sqlite3.Row
        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM machines''')

        # Get the machines
        machines = []
        for row in cursor:
            machines.append(dict(zip(row.keys(), row)))

    # Close the db connection
    if db:
        db.close()

    # Print success
    print("Selected", len(machines))

    return machines


def db_delete_machine(pth, machine_nick):
    """
    Delete machine in the database.
    """

    # Connect to database
    db = sqlite3.connect(pth)
    try:
        with db:
            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if machine exists
            ids = cursor.execute(
                build_select(table='machines',
                             to_select=['nick'],
                             where=['nick']),
                {'nick':        machine_nick}
            ).fetchone()

            if ids is None:
                raise sqlite3.IntegrityError(
                    "Machine to delete does not exist in database")

            sql_com = build_delete(table='machines',
                                   where=['nick'])

            cursor.execute(sql_com, {'nick': machine_nick})

            # Print success
            print("Success", machine_nick)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        print("Error on machine:", "\n",
              machine_nick,
              "\n", e)
        raise ParsingError from e

    # Close the db connection
    if db:
        db.close()

    return
