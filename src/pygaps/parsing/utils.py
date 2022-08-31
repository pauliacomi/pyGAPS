def _search_key_in_def_dict(key, def_dict):
    return next(k for k, v in def_dict.items() if any(key == n for n in v.get('text', [])))

def _search_key_starts_def_dict(key, def_dict):
    return next(k for k, v in def_dict.items() if any(key.startswith(n) for n in v.get('text', [])))


def _handle_xlrd_date(sheet, val):
    """
    Convert date to string.

    Input is a cell of type 'date'.
    """
    if val:
        from xlrd.xldate import xldate_as_datetime
        return xldate_as_datetime(val, sheet.book.datemode).strftime("%Y-%m-%d")


def _handle_xlrd_time(sheet, val):
    """
    Convert date to string.

    Input is a cell of type 'date'.
    """
    if val:
        from xlrd.xldate import xldate_as_datetime
        return xldate_as_datetime(val, sheet.book.datemode).strftime("%H-%M-%S")


def _handle_excel_string(val):
    """
    Replace any newline found.

    Input is a cell of type 'string'.
    """
    if val:
        return str(val).replace('\r\n', ' ')
    return None
