"""Generate the default sqlite database."""


import sqlite3

import pygaps

from .exceptions import ParsingError
from .sqlite_db_pragmas import PRAGMAS


def db_create(pth):
    """
    Create the entire database.

    Parameters
    ----------
    pth : str
        Path where the database is created.

    """
    for pragma in PRAGMAS:
        db_execute_general(pth, pragma)

    pygaps.db_upload_isotherm_property_type(pth, {'type': 'pressure_mode'})
    pygaps.db_upload_isotherm_property_type(pth, {'type': 'pressure_unit'})
    pygaps.db_upload_isotherm_property_type(pth, {'type': 'adsorbate_mode'})
    pygaps.db_upload_isotherm_property_type(pth, {'type': 'adsorbate_unit'})
    pygaps.db_upload_isotherm_property_type(pth, {'type': 'loading_mode'})
    pygaps.db_upload_isotherm_property_type(pth, {'type': 'loading_unit'})

    return


def db_execute_general(pth, statement):
    """
    Execute general SQL statements.

    Parameters
    ----------
    pth : str
        Path where the database is located.
    statement : str
        SQL statement to execute.

    """
    # Attempt to connect
    try:
        with sqlite3.connect(pth) as db:

            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if table does not exist and create it
            cursor.executescript(statement)

    # Catch the exception
    except sqlite3.OperationalError as e_info:
        print("Unable to execute statement", statement)
        raise ParsingError from e_info

    # Close the db connection
    if db:
        db.close()

    return
