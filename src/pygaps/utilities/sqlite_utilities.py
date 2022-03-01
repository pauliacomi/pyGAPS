"""General functions for SQL query building."""

import sqlite3

from pygaps import logger
from pygaps.utilities.exceptions import ParsingError


def db_execute_general(
    statement: str,
    pth: str,
    verbose: bool = False,
):
    """
    Execute general SQL statements.

    Parameters
    ----------
    statement : str
        SQL statement to execute.
    pth : str
        Path where the database is located.
    verbose : bool
        Print out extra information.

    """
    # Attempt to connect
    try:
        # TODO deprecate 3.6: switch below
        # with sqlite3.connect(pth) as db:
        with sqlite3.connect(str(pth)) as db:

            # Get a cursor object
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Check if table does not exist and create it
            cursor.executescript(statement)

    # Catch the exception
    except sqlite3.Error as e_info:
        logger.info(f"Unable to execute statement: \n{statement}")
        raise ParsingError from e_info


def build_update(
    table: str,
    to_set: list,
    where: list,
    prefix: str = None,
):
    """
    Build an update request.

    Parameters
    ----------
    table : str
        Table where query will be directed.
    to_set: iterable
        The list of columns to update.
    where: iterable
        The list of conditions to constrain the query.
    prefix: str, optional
        The prefix to introduce to the second part of the constraint.

    Returns
    -------
    str
        Built query string.

    """
    return (
        f"UPDATE \"{table}\" SET " + ", ".join(f"{w} = :{w}" for w in to_set) + " WHERE " +
        " AND ".join(f"{w} = :{prefix or ''}{w}" for w in where)
    )


def build_insert(table: str, to_insert: list):
    """
    Build an insert request.

    Parameters
    ----------
    table : str
        Table where query will be directed.
    to_insert: iterable
        The list of columns where the values will be inserted.

    Returns
    -------
    str
        Built query string.

    """
    return (
        f"INSERT INTO \"{table}\" (" + ", ".join(f"{w}" for w in to_insert) + ") VALUES (" +
        ", ".join(f":{w}" for w in to_insert) + ")"
    )


def build_select(
    table: str,
    to_select: list,
    where: list = None,
):
    """
    Build a select request.

    Parameters
    ----------
    table : str
        Table where query will be directed.
    to_set: iterable
        The list of columns to select.
    where: iterable
        The list of conditions to constrain the query.

    Returns
    -------
    str
        Built query string.

    """
    if where:
        return (
            "SELECT " + ", ".join(f"{w}" for w in to_select) + f" FROM \"{table}\" WHERE " +
            " AND ".join(f"{w} = :{w}" for w in where)
        )
    return ("SELECT " + ", ".join(f"{w}" for w in to_select) + f" FROM \"{table}\"")


def build_select_unnamed(table: str, to_select: list, where: list, join: str = "AND"):
    """
    Build an select request with multiple parameters.

    Parameters
    ----------
    table : str
        Table where query will be directed.
    to_set : iterable
        The list of columns to select
    where : iterable
        The list of conditions to constrain the query.
    join : str
        The joining clause of the parameters.

    Returns
    -------
    str
        Built query string.

    """
    return (
        "SELECT " + ", ".join(f"{w}" for w in to_select) + f" FROM \"{table}\" WHERE " +
        (" " + join + " ").join(f"{w} = ?" for w in where)
    )


def build_delete(table: str, where: list):
    """
    Build a delete request.

    Parameters
    ----------
    table : str
        Table where query will be directed.
    where: iterable
        The list of conditions to constrain the query.

    Returns
    -------
    str
        Built query string.

    """
    return (f"DELETE FROM \"{table}\" WHERE " + " AND ".join(f"{w} = :{w}" for w in where))
