"""Generate the default sqlite database."""

import json
import sqlite3

import pygaps
from pygaps.parsing import sqlite as pgsqlite

from .exceptions import ParsingError
from .sqlite_db_pragmas import PRAGMAS


def db_create(pth, verbose=False):
    """
    Create the entire database.

    Parameters
    ----------
    pth : str
        Path where the database is created.

    """
    for pragma in PRAGMAS:
        db_execute_general(pth, pragma, verbose=verbose)

    # Load adsorbate paths
    import pkg_resources
    ads_props_path = pkg_resources.resource_filename(
        'pygaps', 'data/adsorbate_props.json'
    )
    ads_path = pkg_resources.resource_filename(
        'pygaps', 'data/adsorbates.json'
    )

    # Import adsorbate json
    with open(ads_props_path) as f:
        ads_props = json.load(f)
    for ap_type in ads_props:
        pgsqlite.adsorbate_property_type_to_db(pth, ap_type, verbose=verbose)

    # Upload adsorbate property types
    with open(ads_path) as f:
        adsorbates = json.load(f)

    # Upload adsorbates
    for ads in adsorbates:
        pgsqlite.adsorbate_to_db(pth, pygaps.Adsorbate(**ads), verbose=verbose)

    # Upload standard isotherm types
    pgsqlite.isotherm_type_to_db(pth, {'type': 'isotherm'})
    pgsqlite.isotherm_type_to_db(pth, {'type': 'pointisotherm'})
    pgsqlite.isotherm_type_to_db(pth, {'type': 'modelisotherm'})


def db_execute_general(pth, statement, verbose=False):
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
    except sqlite3.Error as e_info:
        print("Unable to execute statement", statement)
        raise ParsingError from e_info
