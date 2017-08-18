# %%
import os

import adsutils

json_path = os.path.join(os.getcwd(), 'tests', 'data', 'isotherms_json')
json_file_paths = adsutils.util_get_file_paths(json_path, '.json')
isotherms = []
for filepath in json_file_paths:
    with open(filepath, 'r') as text_file:
        isotherms.append(adsutils.isotherm_from_json(text_file.read()))

#################################################################################
# PyIAST isotherm modelling
#################################################################################
#
# %%
isotherm = isotherms[1]
modelH = isotherm.get_model_isotherm("Henry")
modelH.name = "Henry"
modelL = isotherm.get_model_isotherm("Langmuir")
modelL.name = "Langmuir"
modelDL = isotherm.get_model_isotherm("DSLangmuir")
modelDL.name = "DS Langmuir"

adsutils.plot_iso({isotherm, modelH, modelL, modelDL},
                  plot_type='isotherm', branch='ads', logarithmic=False, color=True)
