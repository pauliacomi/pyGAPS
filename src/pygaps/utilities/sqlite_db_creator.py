"""
This module contains the functions that generate the sqlite database.
"""


import sqlite3

from .exceptions import ParsingError
from .sqlite_db_pragmas import PRAGMAS


def db_create(pth):
    """
    Creates the entire database.

    Parameters
    ----------
    pth : str
        Path where the database is created.

    """
    for pragma in PRAGMAS:
        db_execute_general(pth, pragma)
    return


def db_execute_general(pth, statement):
    """
    A general function that executes SQL statements.

    Parameters
    ----------
    pth : str
        Path where the database is located.
    statement : str
        SQL statement to execute.

    """

    # Attempt to connect
    try:
        # Creates or opens a file called mydb with a SQLite3 DB
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
