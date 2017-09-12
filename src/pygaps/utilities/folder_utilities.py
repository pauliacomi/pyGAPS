"""
This module contains general functions for folder stepping
"""

import os.path

from .exceptions import Error


def util_get_file_paths(folder, extension=None):
    '''
    Gets the paths of the files with the requested extension as a list.

    Parameters
    ----------
    folder : str
        folder where the function will look in, recursively
    extension : str
        the extension of the files to look for

    Returns
    -------
    list
        paths of each file

    '''
    if extension is None:
        raise Error("Must provide a file extension to look for")

    paths = []

    for root, _, files in os.walk(folder):
        for file in files:
            fullpath = os.path.join(root, file)
            ext = os.path.splitext(fullpath)[-1].lower()
            if ext == extension:
                paths.append(fullpath)

    return paths
