"""
Loading some data at import-time.

Here is where objects such as adsorbates or materials
are imported to be available for pyGAPS.
These are populated at import-time.
Also defines the internal database location.
"""
import os

from .parsing.sqliteinterface import db_get_adsorbate_names
from .parsing.sqliteinterface import db_get_adsorbates
from .parsing.sqliteinterface import db_get_materials

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'local.db')

MATERIAL_LIST = db_get_materials(DATABASE, verbose=False)
ADSORBATE_NAME_LIST = [a['name'].lower() for a in db_get_adsorbate_names(DATABASE)]
ADSORBATE_LIST = db_get_adsorbates(DATABASE, verbose=False)
