"""General functions for stepping through folders."""

from pathlib import Path
from .exceptions import pgError


def util_get_file_paths(folder, extension=None):
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

    paths = Path(folder).rglob(f"*.{extension}")

    return paths
