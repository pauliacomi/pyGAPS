"""
Loading some data at import-time.

Here is where objects such as adsorbates or materials are imported to be
available for pyGAPS. These are populated at import-time. Also defines the
internal database location.
"""
# isort:skip_file

import pkg_resources

DATABASE = pkg_resources.resource_filename('pygaps', 'data/default.db')

from .parsing.sqlite import adsorbates_from_db
from .parsing.sqlite import materials_from_db

MATERIAL_LIST = materials_from_db(verbose=False)
ADSORBATE_LIST = adsorbates_from_db(verbose=False)
