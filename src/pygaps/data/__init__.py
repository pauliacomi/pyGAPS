"""
Loading some data at import-time.

Here is where objects such as adsorbates or materials are imported to be
available for pyGAPS. These are populated at import-time. Also defines the
internal database location.
"""
# flake8: noqa
# isort:skip_file

# TODO This will not work inside a zip file...
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

with pkg_resources.path('pygaps.data', 'default.db') as dbpath:
    DATABASE = dbpath

# Lists of pygaps data
MATERIAL_LIST = []
ADSORBATE_LIST = []


def load_data():
    """Will proceed with filling the data store."""

    from ..parsing.sqlite import adsorbates_from_db
    from ..parsing.sqlite import materials_from_db

    global MATERIAL_LIST
    global ADSORBATE_LIST

    MATERIAL_LIST.extend(materials_from_db(verbose=False))
    ADSORBATE_LIST.extend(adsorbates_from_db(verbose=False))
