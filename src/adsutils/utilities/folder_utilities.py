"""
This module contains general functions for folder stepping
"""

import os.path


def util_get_file_paths(folder, extension=None):
    '''
    A function that will get the paths of the files requested as a list.

    :param folder: The folder where the function will look in

    '''
    if extension is None:
        raise Exception("Must provide a file extension to look for")

    paths = []

    for root, _, files in os.walk(folder):
        for f in files:
            fullpath = os.path.join(root, f)
            ext = os.path.splitext(fullpath)[-1].lower()
            if ext == extension:
                paths.append(fullpath)

    return paths
