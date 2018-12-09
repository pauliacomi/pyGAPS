"""
The memory storage from where objects such as adsorbates or samples
are taken. These are populated at import-time.

Also defines the internal database location.
"""
import os

from .parsing.sqliteinterface import db_get_adsorbates
from .parsing.sqliteinterface import db_get_adsorbate_names
from .parsing.sqliteinterface import db_get_samples

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'local.db')

SAMPLE_LIST = db_get_samples(DATABASE, verbose=False)
ADSORBATE_NAME_LIST = [a['name'].lower() for a in db_get_adsorbate_names(DATABASE)]
ADSORBATE_LIST = db_get_adsorbates(DATABASE, verbose=False)
