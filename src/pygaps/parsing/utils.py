import re

# regexes

RE_PUNCTUATION = re.compile(r"['\"_,\^]")  # quotes, underscores, commas, superscript
RE_SPACES = re.compile(r"\s+")  # spaces/tabs
# unicode superscripts
RE_SUPERSCRIPT2 = re.compile("²")
RE_SUPERSCRIPT3 = re.compile("³")
RE_BRACKETS = re.compile(r"[\{\[\(\)\]\}]")  # all bracket type

RE_ONLY_NUMBERS = re.compile(r"^(-)?\d+(.|,)?\d+")
RE_BETWEEN_BRACKETS = re.compile(r"(?<=\().+?(?=\))")


def search_key_in_def_dict(key, def_dict):
    """Finds key in the dictionary, provided it exists in the value ["text"] list"""
    return next(k for k, v in def_dict.items() if any(key == n for n in v.get('text', [])))


def search_key_starts_def_dict(key, def_dict):
    """Finds key in the dictionary, provided it starts in the value ["text"] list"""
    return next(k for k, v in def_dict.items() if any(key.startswith(n) for n in v.get('text', [])))


def handle_xlrd_datetime(sheet, val):
    """
    Convert date to string.

    Input is a cell of type 'datetime'.
    """
    if val:
        from xlrd.xldate import xldate_as_datetime
        return xldate_as_datetime(val, sheet.book.datemode).isoformat()


def handle_xlrd_date(sheet, val):
    """
    Convert date to string.

    Input is a cell of type 'date'.
    """
    if val:
        from xlrd.xldate import xldate_as_datetime
        return xldate_as_datetime(val, sheet.book.datemode).strftime("%Y-%m-%d")


def handle_xlrd_time(sheet, val):
    """
    Convert date to string.

    Input is a cell of type 'time'.
    """
    if val:
        from xlrd.xldate import xldate_as_datetime
        return xldate_as_datetime(val, sheet.book.datemode).strftime("%H:%M:%S")


def handle_excel_string(val):
    """
    Replace any newline found.

    Input is a cell of type 'string'.
    """
    if val:
        return str(val).replace('\r\n', ' ')
    return None


def handle_string_time_minutes(text):
    """Convert time points from HH:MM format to minutes."""
    hours, mins = str(text).split(':')
    return int(hours) * 60 + int(mins)
