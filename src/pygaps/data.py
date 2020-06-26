"""
Loading some data at import-time.

Here is where objects such as adsorbates or materials
are imported to be available for pyGAPS.
These are populated at import-time.
Also defines the internal database location.
"""
from pathlib import Path

from .parsing.sqlite import adsorbate_from_db
from .parsing.sqlite import materials_from_db

DATABASE = Path(__file__).parent / 'data' / 'default.db'
MATERIAL_LIST = materials_from_db(DATABASE, verbose=False)
ADSORBATE_LIST = adsorbate_from_db(DATABASE, verbose=False)
