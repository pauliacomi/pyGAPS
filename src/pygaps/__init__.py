# pylint: disable=W0614,W0611,W0622,C0411
# flake8: noqa
# isort:skip_file

__author__ = 'Paul Iacomi'
__docformat__ = 'restructuredtext'

# _version.py is written by setuptools_scm at build/install time
try:
    from ._version import __version__
except ImportError:
    from importlib.metadata import PackageNotFoundError, version as _version
    try:
        __version__ = _version("pygaps")
    except PackageNotFoundError:
        __version__ = "0+unknown"
    del PackageNotFoundError, _version

from .logging import logger

# Data
from pygaps.data import DATABASE
from pygaps.data import ADSORBATE_LIST
from pygaps.data import MATERIAL_LIST
from pygaps.data import load_data

# Thermodynamic backend
from pygaps.utilities.coolprop_utilities import thermodynamic_backend
from pygaps.utilities.coolprop_utilities import backend_use_coolprop
from pygaps.utilities.coolprop_utilities import backend_use_refprop

# Core classes
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.material import Material
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.core.modelisotherm import ModelIsotherm

# Data load
load_data()
del load_data

# Other user-facing functions
# from .api import *
