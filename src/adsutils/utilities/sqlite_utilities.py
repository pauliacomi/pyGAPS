def build_update(table, to_set, where, prefix=None):
    """
    builds an update request
    """

    sql_q = 'UPDATE \"' + table + '\"'
    sql_q += " SET "
    sql_q += ', '.join('{0} = :{0}'.format(w) for w in to_set)
    sql_q += ' WHERE '
    if prefix is not None:
        sql_q += ' AND '.join('{0} = :{1}{0}'.format(w, prefix) for w in where)
    else:
        sql_q += ' AND '.join('{0} = :{0}'.format(w) for w in where)

    return sql_q


def build_insert(table, to_insert):
    """
    builds an insert request
    """

    sql_q = 'INSERT INTO \"' + table + '\" ('
    sql_q += ', '.join('{0}'.format(w) for w in to_insert)
    sql_q += ') VALUES ('
    sql_q += ', '.join(':{0}'.format(w) for w in to_insert)
    sql_q += ')'

    return sql_q


def build_select(table, to_select, where):
    """
    builds an select request
    """

    sql_q = "SELECT "
    sql_q += ', '.join('{0}'.format(w) for w in to_select)
    sql_q += ' FROM \"' + table + '\"'
    if len(where) > 0:
        sql_q += ' WHERE '
        sql_q += ' AND '.join('{0} = :{0}'.format(w) for w in where)

    # sql_q += ' AND '.join(list(map(lambda x:
    #                                x[0] + " IS NULL"
    #                                if x[1] == ""
    #                                else x[0] + "=:" + x[0],
    #                                where.items())))

    return sql_q


def build_delete(table, where):
    """
    builds a delete request
    """

    sql_q = "DELETE "
    sql_q += ' FROM \"' + table + '\"'
    sql_q += ' WHERE '
    sql_q += ' AND '.join('{0} = :{0}'.format(w) for w in where)

    return sql_q
