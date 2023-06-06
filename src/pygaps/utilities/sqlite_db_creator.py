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
    try:
        from importlib.resources import files as ir_files
    except ImportError:
        # TODO Deprecation after PY<3.9
        # Use backported `importlib_resources`.
        from importlib_resources import files as ir_files

    # Get and upload adsorbate property types
    ads_props_json = ir_files('pygaps.data').joinpath('adsorbate_props.json').read_text(
        encoding='utf8'
    )
    ads_props = json.loads(ads_props_json)
    for ap_type in ads_props:
        pgp_sqlite.adsorbate_property_type_to_db(ap_type, db_path=path, verbose=verbose)

    # Get and upload adsorbates
    ads_json = ir_files('pygaps.data').joinpath('adsorbates.json').read_text(encoding='utf8')
    adsorbates = json.loads(ads_json)
    for ads in adsorbates:
        pgp_sqlite.adsorbate_to_db(pygaps.Adsorbate(**ads), db_path=path, verbose=verbose)

    # Upload standard isotherm types
    pgp_sqlite.isotherm_type_to_db({'type': 'isotherm'}, db_path=path)
    pgp_sqlite.isotherm_type_to_db({'type': 'pointisotherm'}, db_path=path)
    pgp_sqlite.isotherm_type_to_db({'type': 'modelisotherm'}, db_path=path)
