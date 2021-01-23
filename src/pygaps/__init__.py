# pylint: disable=W0614,W0611,W0622
# flake8: noqa
# isort:skip_file

__author__ = 'Paul A. Iacomi'
__docformat__ = 'restructuredtext'
__version__ = '2.0.2'

# This code is written for Python 3.
import sys
if sys.version_info[0] != 3:
    print("pyGAPS requires Python 3.")
    sys.exit(1)

# Let users know if they're missing any hard dependencies
hard_dependencies = ("numpy", "pandas", "scipy", "CoolProp")
missing_dependencies = []

import importlib
for dependency in hard_dependencies:
    try:
        importlib.import_module(dependency)
    except ImportError as e_info:
        missing_dependencies.append(f"{dependency}: {e_info}")

if missing_dependencies:
    raise ImportError(f"Missing required dependencies {missing_dependencies}")
del hard_dependencies, dependency, missing_dependencies

# Core
from .core.adsorbate import Adsorbate
from .core.material import Material
from .core.modelisotherm import ModelIsotherm
from .core.pointisotherm import PointIsotherm

# Data
from .data import DATABASE
from .data import ADSORBATE_LIST
from .data import MATERIAL_LIST
from .api import *
