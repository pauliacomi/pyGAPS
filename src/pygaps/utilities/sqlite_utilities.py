"""General functions for SQL query building."""


def build_update(table, to_set, where, prefix=None):
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
        f"UPDATE \"{table}\" SET " + ", ".join(f"{w} = :{w}" for w in to_set) +
        " WHERE " + " AND ".join(f"{w} = :{prefix or ''}{w}" for w in where)
    )


def build_insert(table, to_insert):
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
        f"INSERT INTO \"{table}\" (" + ", ".join(f"{w}" for w in to_insert) +
        ") VALUES (" + ", ".join(f":{w}" for w in to_insert) + ")"
    )


def build_select(table, to_select, where=None):
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
            "SELECT " + ", ".join(f"{w}" for w in to_select) +
            f" FROM \"{table}\" WHERE " +
            " AND ".join(f"{w} = :{w}" for w in where)
        )
    return (
        "SELECT " + ", ".join(f"{w}" for w in to_select) + f" FROM \"{table}\""
    )


def build_select_unnamed(table, to_select, where, join="AND"):
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
        "SELECT " + ", ".join(f"{w}" for w in to_select) +
        f" FROM \"{table}\" WHERE " +
        (" " + join + " ").join(f"{w} = ?" for w in where)
    )


def build_delete(table, where):
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
    return (
        f"DELETE FROM \"{table}\" WHERE " +
        " AND ".join(f"{w} = :{w}" for w in where)
    )
