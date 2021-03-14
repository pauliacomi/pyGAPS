"""Collections of various python utilities."""

import collections.abc as abc
import pathlib
import warnings

from .exceptions import pgError


def _one_pass(iters):
    i = 0
    while i < len(iters):
        try:
            yield next(iters[i])
        except StopIteration:
            del iters[i]
        else:
            i += 1


def zip_varlen(*iterables):
    """Variable length zip() function."""
    iters = [iter(it) for it in iterables]
    while True:  # broken when an empty tuple is given by _one_pass
        val = tuple(_one_pass(iters))
        if val:
            yield val
        else:
            break


def grouped(iterable, n):
    """Divide an iterable in subgroups of max n elements."""
    return zip_varlen(*[iter(iterable)] * n)


def deep_merge(a, b, path=None, update=True):
    """Recursive updates of a dictionary."""
    if path is None:
        path = []
    for key, val in b.items():
        if key in a:
            if (
                isinstance(a[key], abc.Mapping)
                and isinstance(val, abc.Mapping)
            ):
                deep_merge(a[key], val, path + [str(key)], update)
            elif a[key] == val:
                pass  # same leaf value
            elif update:
                a[key] = val
            else:
                raise Exception(f"Conflict at {'.'.join(path + [str(key)])}")
        else:
            a[key] = val
    return a


def checkSQLbool(val):
    """Check if a value is a bool. Useful for sqlite storage."""
    if val in ['TRUE', 'FALSE']:
        if val == 'TRUE':
            return True
        return False
    return val


def get_file_paths(folder, extension=None):
    """
    Get the paths of the files with the requested extension as a list.

    Parameters
    ----------
    folder : str
        Folder where the function will look in, recursively.
    extension : str
        The extension of the files to look for.

    Returns
    -------
    list
        Paths of each file.

    """
    if extension is None:
        raise pgError("Must provide a file extension to look for")

    return pathlib.Path(folder).rglob(f"*.{extension}")


class simplewarning():
    """
    Context manager overrides warning formatter to remove unneeded info.
    """
    def __enter__(self):
        # ignore everything except the message
        def custom_formatwarning(msg, *args, **kwargs):
            return str(msg) + '\n'

        self.old_formatter = warnings.formatwarning
        warnings.formatwarning = custom_formatwarning
        return True

    def __exit__(self, type, value, traceback):
        warnings.formatwarning = self.old_formatter
        return True
