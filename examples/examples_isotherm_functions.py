# %%
import os

import pygaps

db_path = os.path.expanduser(
    r"~\OneDrive\Documents\PhD Documents\Data processing\Database\local.db")

isotherms = pygaps.db_get_experiments(db_path, {})

#################################################################################
#       Modes and units
#################################################################################
#
# %%
for isotherm in isotherms:
    isotherm.convert_pressure_mode("relative")
    isotherm.convert_pressure_mode("absolute")
