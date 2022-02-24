"""
Loading some data at import-time.

Here is where objects such as adsorbates or materials are imported to be
available for pyGAPS. These are populated at import-time. Also defines the
internal database location.
"""
# flake8: noqa
# isort:skip_file

try:
    import importlib.resources as importlib_resources
    from importlib.resources import files as importlib_resources_files
except ImportError:
    # TODO Deprecation after PY<39
    # Use backported `importlib_resources`.
    import importlib_resources as importlib_resources
    from importlib_resources import files as importlib_resources_files

from contextlib import ExitStack
import atexit

# We use an exit stack and register it at interpreter exit to cleanup anything needed
file_manager = ExitStack()
atexit.register(file_manager.close)
ref = importlib_resources_files('pygaps.data') / 'default.db'
DATABASE = file_manager.enter_context(importlib_resources.as_file(ref))

# Lists of pygaps data
MATERIAL_LIST = []
ADSORBATE_LIST = []


def load_data():
    """Will proceed with filling the data store."""

    from pygaps.parsing.sqlite import adsorbates_from_db
    from pygaps.parsing.sqlite import materials_from_db

    global MATERIAL_LIST
    global ADSORBATE_LIST

    MATERIAL_LIST.extend(materials_from_db(verbose=False))
    ADSORBATE_LIST.extend(adsorbates_from_db(verbose=False))


_kernel_res = importlib_resources_files('pygaps.data.kernels')
KERNELS = {
    'DFT-N2-77K-carbon-slit': _kernel_res / 'DFT-N2-77K-carbon-slit.csv',
}
