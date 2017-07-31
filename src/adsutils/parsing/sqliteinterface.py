# %%
"""
This module contains the sql interface for data manipulation
"""

__author__ = 'Paul A. Iacomi'

import array
import sqlite3

import numpy
import pandas

from ..classes.gas import Gas
from ..classes.pointisotherm import PointIsotherm
from ..classes.sample import Sample

# %%


def db_upload_sample(pth, sample, overwrite=False):
    """
    Uploads samples to the database
    If overwrite is set to true, the sample is overwritten
    Overwrite is done based on sample.name + sample.batch
    WARNING: Overwrite is done on ALL fields
    """
    if overwrite:
        sql_com = """
            UPDATE "samples"
            SET
                project = :project,
                struct = :struct,
                owner = :owner,
                family = :family,
                contact = :contact,
                form = :form,
                source_lab = :source_lab,
                comment = :comment
            WHERE
                name = :name
                AND
                batch = :batch
            """
    else:
        sql_com = """
            INSERT INTO "samples"(
                name,       project,
                batch,      struct,
                owner,      family,
                contact,    form,
                source_lab, comment)
            VALUES (
                :name,       :project,
                :batch,      :struct,
                :owner,      :family,
                :contact,    :form,
                :source_lab, :comment)
            """

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Upload or modify data in sample table
        cursor.execute(sql_com, {
            'name':         sample.name,
            'batch':        sample.batch,
            'owner':        sample.owner,
            'contact':      sample.contact,
            'source_lab':   sample.source_lab,
            'project':      sample.project,
            'struct':       sample.struct,
            'family':       sample.family,
            'form':         sample.form,
            'comment':      sample.comment,
        }
        )

        # Upload or modify data in sample_properties table
        if len(sample.properties) > 0:
            # Get id of modification
            sample_id = cursor.execute(
                """
                    SELECT id
                    FROM "samples"
                    WHERE
                        name = :name
                        AND
                        batch = :batch;
                    """, {
                    'name':        sample.name,
                    'batch':       sample.batch,
                }
            ).fetchone()[0]

            # Sql of update routine
            sql_update = """
                    UPDATE "sample_properties"
                    SET
                        type = :type,
                        value = :value
                    WHERE
                        sample_id = :sample_id;
                    """

            # Sql of insert routine
            sql_insert = """
                    INSERT INTO "sample_properties"(
                        sample_id,
                        type,
                        value )
                    VALUES (
                        :sample_id,
                        :type,
                        :value )
                    """

            if overwrite:
                # Find existing properties
                cursor.execute(
                    """
                    SELECT type
                    FROM "sample_properties"
                    WHERE sample_id = ?;
                    """, (str(sample_id),)
                )
                column = [elt[0] for elt in cursor.fetchall()]

                for prop in sample.properties:
                    if prop in column:
                        sql_com = sql_update
                    else:
                        sql_com = sql_insert

                    # Insert or update properties individually
                    cursor.execute(sql_com, {
                        'sample_id':        sample_id,
                        'type':             prop,
                        'value':            sample.properties[prop]
                    })

            else:
                for prop in sample.properties:
                    cursor.execute(sql_insert, {
                        'sample_id':        sample_id,
                        'type':             prop,
                        'value':            sample.properties[prop]
                    })

        # Commit the change
        db.commit()

        # Print success
        print("Sample uploaded", sample.name, sample.batch)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        print("Error on sample:", "\n",
              sample.name,
              sample.batch,
              "\n", e)

    finally:
        # Close the db connection
        db.close()

    return


# %%
def db_get_samples(pth):
    """
    Gets all samples in sample table
    """
    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Execute the query
        cursor.execute('''SELECT * FROM samples''')

        samples = []
        sample_infos = []
        # Create the samples
        for row in cursor:
            # row[0] returns the first column in the query (name), row[1] returns email column.
            info = {}
            info['id'] = row[0]
            info['name'] = row[1]
            info['batch'] = row[2]
            info['owner'] = row[3]
            info['contact'] = row[4]
            info['source_lab'] = row[5]
            info['project'] = row[6]
            info['struct'] = row[7]
            info['family'] = row[8]
            info['form'] = row[9]
            info['comment'] = row[11]

            sample_infos.append(info)

        # Get the extra data from the sample_properties table
        for info in sample_infos:
            cursor.execute(
                """
                SELECT type, value
                FROM "sample_properties"
                WHERE sample_id = ?;
                """, (str(info['id']),)
            )

            info['properties'] = dict()

            for row in cursor:
                prop = {row[0]: row[1]}
                info['properties'].update(prop)

            # Build sample objects
            samples.append(Sample(info))

        # Print success
        print("Selected", len(samples), "samples")

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    finally:
        # Close the db connection
        db.close()

    return samples


# %%
def db_upload_experiment(pth, isotherm, overwrite=False):
    """
    Uploads experiment to the database
    """

    # Build SQL request
    if overwrite:
        if isotherm.id is None or not isotherm.id:
            raise ValueError("Cannot overwrite an isotherm without an id")
        # get id of the experiment that needs to be overwritten
        sql_com = """
            UPDATE "experiments"
            SET
                date        = :date,
                is_real     = :is_real,
                exp_type    = :exp_type,
                sname       = :sname,
                sbatch      = :sbatch,
                t_act       = :t_act,
                t_exp       = :t_exp,
                machine     = :machine,
                gas         = :gas,
                user        = :user,
                lab         = :lab,
                project     = :project,
                comment     = :comment
            WHERE
                id = :id
            """
    else:
        sql_com = """
            INSERT INTO "experiments"(
                date,       is_real,
                exp_type,   sname,
                sbatch,     t_act,
                t_exp,      machine,
                gas,        user,
                lab,        project,
                comment)
            VALUES (
                :date,      :is_real,
                :exp_type,  :sname,
                :sbatch,    :t_act,
                :t_exp,     :machine,
                :gas,       :user,
                :lab,       :project,
                :comment)
            """

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Build upload dict
        upload_dict = {
            'date':     isotherm.date,
            'is_real':  isotherm.is_real,
            'exp_type': isotherm.exp_type,
            'sname':    isotherm.name,
            'sbatch':   isotherm.batch,
            't_act':    isotherm.t_act,
            't_exp':    isotherm.t_exp,
            'machine':  isotherm.machine,
            'gas':      isotherm.gas,
            'user':     isotherm.user,
            'lab':      isotherm.lab,
            'project':  isotherm.project,
            'comment':  isotherm.comment
        }
        if overwrite:
            upload_dict.update({'id': isotherm.id})

        # Upload experiment info to database
        cursor.execute(sql_com, upload_dict)

        # Now to upload data into experiment_data table
        # Get id of insertion
        if overwrite:
            exp_id = isotherm.id
        else:
            exp_id = cursor.lastrowid

        # Build sql request
        if overwrite:
            sql_com2 = """
                       UPDATE "experiment_data"
                       SET
                           data   = :data
                       WHERE
                           exp_id = :exp_id
                           AND
                           dtype  = :dtype
                       """
        else:
            sql_com2 = """
                       INSERT INTO "experiment_data"
                       (exp_id, dtype, data)
                       VALUES
                       (:exp_id, :dtype, :data)
                       """

        # Insert data into experiment_data table
        cursor.execute(sql_com2,
                       {'exp_id': exp_id, 'dtype': 'pressure',
                           'data': isotherm.pressure_all().tobytes()}
                       )

        cursor.execute(sql_com2,
                       {'exp_id': exp_id, 'dtype': 'loading',
                           'data': isotherm.loading_all().tobytes()}
                       )

        enthalpy = isotherm.enthalpy_all()
        if enthalpy is not None:
            cursor.execute(sql_com2,
                           {'exp_id': exp_id, 'dtype': 'enthalpy',
                               'data': enthalpy.tobytes()}
                           )

        # Commit the change
        db.commit()

        # Print success
        print("Success:", isotherm)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        print("Error on isotherm:", "\n",
              isotherm.exp_type,
              isotherm.name,
              isotherm.batch,
              isotherm.user,
              isotherm.gas,
              isotherm.machine,
              isotherm.t_act,
              isotherm.t_exp,
              "\n", e)

    finally:
        # Close the db connection
        db.close()

    return


# %%
def db_delete_experiment(pth, isotherm):
    """
    Delete experiment to the database
    """

    # Build SQL request
    if isotherm.id is None or not isotherm.id:
        raise ValueError("Cannot delete an isotherm without an id")

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Delete data from experiment_data table
        # Build sql request
        sql_com2 = """
                    DELETE FROM "experiment_data"
                    WHERE
                        exp_id = :exp_id
                    """

        cursor.execute(sql_com2, {'exp_id': isotherm.id})

        # Delete experiment info in database
        # get id of the experiment that needs to be overwritten
        sql_com = """
                    DELETE FROM "experiments"
                    WHERE
                        id = :id
                    """

        cursor.execute(sql_com, {'id': isotherm.id})

        # Commit the change
        db.commit()

        # Print success
        print("Success:", isotherm)

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        print("Error on isotherm:", "\n",
              isotherm.exp_type,
              isotherm.name,
              isotherm.batch,
              isotherm.user,
              isotherm.gas,
              isotherm.machine,
              isotherm.t_act,
              isotherm.t_exp,
              "\n", e)

    finally:
        # Close the db connection
        db.close()

    return

# %%


def db_get_experiments(pth, criteria):
    """
    Gets experiments with the selected criteria from the database
    """

    # Build SQL request
    sql_com = """
        SELECT id,
            date,       is_real,
            exp_type,   sname,
            sbatch,     t_act,
            t_exp,      machine,
            gas,        user,
            lab,        project,
            comment

        FROM "experiments"

        WHERE
        """
    criteria_str = " AND ".join(list(map(
        lambda x:
        x[0] + " IS NULL" if x[1] == ""
        else x[0] + "=:" + x[0], criteria.items())))
    sql_com += criteria_str + ";"

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Get experiment info from database
        cursor.execute(sql_com, criteria)

        exp_infos = []
        for row in cursor:
            info = {}
            info['id'] = row[0]
            info['date'] = row[1]
            info['is_real'] = row[2]
            info['exp_type'] = row[3]
            info['name'] = row[4]
            info['batch'] = row[5]
            info['t_act'] = row[6]
            info['t_exp'] = row[7]
            info['machine'] = row[8]
            info['gas'] = row[9]
            info['user'] = row[10]
            info['lab'] = row[11]
            info['project'] = row[12]
            info['comment'] = row[13]
            exp_infos.append(info)

        if len(exp_infos) == 0:
            print("No values found")
            return

        # Get experiment data from database
        exp_datas = []
        for info in exp_infos:
            cursor.execute(
                """
                SELECT dtype, data
                FROM "experiment_data"
                WHERE exp_id = ?;
                """, (str(info['id']),)
            )

            columns = []
            data_arr = None
            for row in cursor:
                if row[0] == 'pressure':
                    columns.append("Pressure")
                elif row[0] == 'loading':
                    columns.append("Loading")
                elif row[0] == 'enthalpy':
                    columns.append("Enthalpy")

                raw = array.array('d', row[1])
                if data_arr is None:
                    data_arr = numpy.expand_dims(numpy.array(raw), axis=1)
                else:
                    data_arr = numpy.hstack(
                        (data_arr, numpy.expand_dims(numpy.array(raw), axis=1)))

            exp_datas.append(pandas.DataFrame(data_arr, columns=columns))

        # build isotherm objects
        isotherms = []
        for x in list(map(list, zip(exp_datas, exp_infos))):
            isotherms.append(PointIsotherm(x[0], x[1],
                                           pressure_key="Pressure",
                                           loading_key="Loading",
                                           enthalpy_key="Enthalpy"))

        # Print success
        print("Selected", len(isotherms), "isotherms")

        return isotherms

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    # except ValueError as e:
    #     print(e)
    #     db.rollback()

    finally:
        # Close the db connection
        db.close()

    return

# %%


def db_get_experiment_id(pth, criteria):
    """
    Gets the id of an experiment with the selected criteria from the database
    """
    # Build SQL request
    sql_com = """
        SELECT id,
            date,       is_real,
            exp_type,   sname,
            sbatch,     t_act,
            t_exp,      machine,
            gas,        user,
            lab,        project,
            comment

        FROM "experiments"

        WHERE
        """
    criteria_str = " AND ".join(
        list(map(lambda x: x + "=:" + x, criteria.keys())))
    sql_com += criteria_str + ";"

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Get experiment info from database
        cursor.execute(sql_com, criteria)
        if cursor.rowcount == 0:
            raise ValueError("No values found")
        elif cursor.rowcount > 1:
            raise ValueError("Multiple isotherms with the same criteria")
        else:
            return cursor.lastrowid

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    # except ValueError as e:
    #     print(e)
    #     db.rollback()

    finally:
        # Close the db connection
        db.close()

    return


# %%
def db_upload_experiment_calculated(pth, data, overwrite=False):
    """
    Uploads an experiment calculated value to be stored in the database
    (such as initial enthalpy of adsorption, henry constant etc)
    Specify overwrite to write on top of existing values
    """
    # Build sql request
    if overwrite:
        sql_com = """
                    UPDATE "experiment_calculated"
                    SET
                        henry_c     = :henry_c
                        enth_init   = :enth_init
                    WHERE
                        exp_id = :exp_id
                    """
    else:
        sql_com = """
                    INSERT INTO "experiment_calculated"
                    (exp_id, henry_c, enth_init)
                    VALUES
                    (:exp_id, :henry_c, :enth_init)
                    """

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Upload data to database
        cursor.execute(sql_com, {
            'exp_id':         data['exp_id'],
            'henry_c':        data['henry_c'],
            'enth_init':      data['enth_init']
        }
        )

        # Commit the change
        db.commit()

        # Print success
        print("Calculated data uploaded")

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        print("Error on id:", "\n",
              data['exp_id'],
              "\n", e)

    finally:
        # Close the db connection
        db.close()

    return


# %%
def db_get_gas(pth, name):
    """
    Gets specified gas
    """

    # Build SQL request
    sql_com = """
        SELECT * FROM "gasses" WHERE nick=:nick
        """

    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)
        db.row_factory = sqlite3.Row

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Get all gasses from database
        db_params = {"nick": name}
        cursor.execute(sql_com, db_params)
        if cursor.rowcount == 0:
            raise ValueError("No values found")
        elif cursor.rowcount > 1:
            raise ValueError("Too many values found")

        # Build gas object
        r = cursor.fetchone()

        gasparams = {}

        gasparams["name"] = r["nick"]
        gasparams["mmass"] = r["molar_mass"]
        gasparams["polarizability"] = r["polarizability"]
        gasparams["dipole"] = r["dipole"]
        gasparams["quadrupole"] = r["quadrupole"]

        reqgas = Gas(gasparams)

        return reqgas

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    finally:
        # Close the db connection
        db.close()

    return


#####################################################################
# Table creation and reinitialisation
#
# WARNING: deletes data

# %%
def db_create_table_samples(pth):
    """
    Sample table reinitialisation
    """
    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Check if table users does not exist and create it
        cursor.executescript(
            '''

            DROP TABLE IF EXISTS "samples";

            CREATE TABLE "samples" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name`          TEXT        NOT NULL,
                `batch`         TEXT        NOT NULL,
                `owner`         TEXT        NOT NULL,
                `contact`       TEXT        NOT NULL,
                `source_lab`    TEXT        NOT NULL,
                `project`       TEXT,
                `struct`        TEXT,
                `family`        TEXT        NOT NULL,
                `form`          TEXT        NOT NULL,
                `modifier`      TEXT,
                `comment`       TEXT,

                FOREIGN KEY(`owner`)        REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`contact`)      REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`source_lab`)   REFERENCES `labs`(`nick`),
                FOREIGN KEY(`project`)      REFERENCES `projects`(`nick`),
                FOREIGN KEY(`family`)       REFERENCES `material_family`(`nick`),
                FOREIGN KEY(`form`)         REFERENCES `forms`(`nick`)
                UNIQUE(name,batch));

            ''')

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    finally:
        # Close the db connection
        db.close()

    print("Sample table created")

    return

# %%


def db_create_table_experiments(pth):
    """
    Experiment table reinitialisation
    """
    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Check if table users does not exist and create it
        cursor.executescript(
            '''

            DROP TABLE IF EXISTS "experiments";

            CREATE TABLE "experiments" (

            `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `date`          TEXT,
            `is_real`       INTEGER     NOT NULL,
            `exp_type`      TEXT        NOT NULL,
            `sname`         TEXT        NOT NULL,
            `sbatch`        TEXT        NOT NULL,
            `t_act`         REAL        NOT NULL,
            `t_exp`         REAL        NOT NULL,
            `machine`       TEXT        NOT NULL,
            `gas`           TEXT        NOT NULL,
            `user`          TEXT        NOT NULL,
            `lab`           TEXT        NOT NULL,
            `project`       TEXT,
            `comment`       TEXT,

            FOREIGN KEY(`sname`,`sbatch`)   REFERENCES `samples`(`name`,`batch`),
            FOREIGN KEY(`exp_type`)         REFERENCES `experiment_type`(`nick`),
            FOREIGN KEY(`machine`)          REFERENCES `machines`(`nick`),
            FOREIGN KEY(`user`)             REFERENCES `contacts`(`nick`),
            FOREIGN KEY(`gas`)              REFERENCES `gasses`(`nick`),
            FOREIGN KEY(`lab`)              REFERENCES `labs`(`nick`),
            FOREIGN KEY(`project`)          REFERENCES `projects`(`nick`)
            UNIQUE(date, is_real, exp_type, sname, sbatch, t_act, t_exp, machine, gas, user)
            );

            ''')

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    finally:
        # Close the db connection
        db.close()

    print("Experiment table created")

    return

# %%


def db_create_table_experiment_data(pth):
    """
    Experiment data table reinitialisation
    """
    try:
        # Creates or opens a file called mydb with a SQLite3 DB
        db = sqlite3.connect(pth)

        # Get a cursor object
        cursor = db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

        # Check if table users does not exist and create it
        cursor.executescript(
            '''

            DROP TABLE IF EXISTS "experiment_data";

            CREATE TABLE "experiment_data" (

            `id`        INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `exp_id`    INTEGER     NOT NULL,
            `dtype`     TEXT        NOT NULL,
            `data`      BLOB        NOT NULL,

            FOREIGN KEY(`exp_id`)   REFERENCES `experiments`(`id`),
            FOREIGN KEY(`dtype`)    REFERENCES `experiment_data_type`(`type`)
            );

            ''')

    # Catch the exception
    except sqlite3.IntegrityError as e:
        # Roll back any change if something goes wrong
        db.rollback()
        raise e

    finally:
        # Close the db connection
        db.close()

    print("Experiment data table created")

    return
