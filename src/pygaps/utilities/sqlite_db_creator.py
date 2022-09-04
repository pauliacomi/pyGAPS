"""Generate the default sqlite database."""

import json

import pygaps
from pygaps.parsing import sqlite as pgp_sqlite
from pygaps.utilities.sqlite_db_pragmas import PRAGMAS
from pygaps.utilities.sqlite_utilities import db_execute_general


def db_create(path: str, verbose: bool = False):
    """
    Create the entire database.

    Parameters
    ----------
    path : str
        Path where the database is created.
    verbose : bool
        Print out extra information.

    """
    for pragma in PRAGMAS:
        db_execute_general(pragma, path, verbose=verbose)

    # Get json files
    import importlib.resources as importlib_resources

    # Get and upload adsorbate property types
    ads_props_json = importlib_resources.read_text('pygaps.data', 'adsorbate_props.json')
    ads_props = json.loads(ads_props_json)
    for ap_type in ads_props:
        pgp_sqlite.adsorbate_property_type_to_db(ap_type, db_path=path, verbose=verbose)

    # Get and upload adsorbates
    ads_json = importlib_resources.read_text('pygaps.data', 'adsorbates.json')
    adsorbates = json.loads(ads_json)
    for ads in adsorbates:
        pgp_sqlite.adsorbate_to_db(pygaps.Adsorbate(**ads), db_path=path, verbose=verbose)

    # Upload standard isotherm types
    pgp_sqlite.isotherm_type_to_db({'type': 'isotherm'}, db_path=path)
    pgp_sqlite.isotherm_type_to_db({'type': 'pointisotherm'}, db_path=path)
    pgp_sqlite.isotherm_type_to_db({'type': 'modelisotherm'}, db_path=path)
