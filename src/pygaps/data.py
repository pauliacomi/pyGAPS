"""
Loading some data at import-time.

Here is where objects such as adsorbates or materials
are imported to be available for pyGAPS.
These are populated at import-time.
Also defines the internal database location.
"""
from pathlib import Path

from .parsing.sqliteinterface import db_get_adsorbate_names
from .parsing.sqliteinterface import db_get_adsorbates
from .parsing.sqliteinterface import db_get_materials

DATABASE = Path(__file__).parent / 'database' / 'local.db'

MATERIAL_LIST = db_get_materials(DATABASE, verbose=False)
ADSORBATE_NAME_LIST = [
    a['name'].lower() for a in db_get_adsorbate_names(DATABASE)
]
ADSORBATE_LIST = db_get_adsorbates(DATABASE, verbose=False)
