# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa

__author__ = 'Paul A. Iacomi'
__docformat__ = 'restructuredtext'
__version__ = '1.3.0'

# isort:skip_file

# This code is written for Python 3.
import importlib
import sys
if sys.version_info[0] != 3:
    print("Code requires Python 3.")
    sys.exit(1)


# Let users know if they're missing any of our hard dependencies
hard_dependencies = ("numpy", "pandas", "scipy",
                     "matplotlib", "CoolProp")
missing_dependencies = []
dependency = None

for dependency in hard_dependencies:
    try:
        importlib.import_module(dependency)
    except ImportError as e_info:
        missing_dependencies.append(dependency)

if missing_dependencies:
    raise ImportError(
        "Missing required dependencies {0}".format(missing_dependencies))
del hard_dependencies, dependency, missing_dependencies

from .data import DATABASE
from .data import ADSORBATE_LIST
from .data import SAMPLE_LIST
from .api import *
