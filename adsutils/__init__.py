'''
This module has many functionalities for manipulating
data from adsorption experiments
'''
__author__ = 'Paul A. Iacomi'

# This code is written for Python 3.
import sys
if sys.version_info[0] != 3:
    print("Code requires Python 3.")
    sys.exit(1)

# Let users know if they're missing any of our hard dependencies
hard_dependencies = ("numpy", "pandas", "pyiast", "sqlite3", "xlwings", "CoolProp")
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append(dependency)

if missing_dependencies:
    raise ImportError("Missing required dependencies {0}".format(missing_dependencies))
del hard_dependencies, dependency, missing_dependencies

from adsutils.classes.pointisotherm import *
from adsutils.classes.user import *
from adsutils.classes.sample import *
from adsutils.classes.gas import *

from adsutils.calculations.initial_henry import *
from adsutils.calculations.initial_enthalpy import *
from adsutils.calculations.bet import *

from adsutils.dataimport.excelinterface import *
from adsutils.dataimport.csvinterface import *
from adsutils.dataimport.sqliteinterface import *

from adsutils.graphing.isothermgraphs import *


SAMPLE_LIST = []
GAS_LIST = []