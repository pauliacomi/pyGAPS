"""General functions for stepping through folders."""

import os.path

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

    paths = []

    for root, _, files in os.walk(folder):
        for file in files:
            fullpath = os.path.join(root, file)
            ext = os.path.splitext(fullpath)[-1].lower()
            if ext == extension.lower():
                paths.append(fullpath)

    return paths
