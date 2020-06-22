from pathlib import Path

DATA_PATH = Path(
    __file__
).parent.parent.parent / 'docs' / 'examples' / 'data' / 'parsing'

DATA_EXCEL_PATH = DATA_PATH / 'excel'
DATA_JSON_PATH = DATA_PATH / 'json'

DATA_EXCEL_STD = [
    DATA_EXCEL_PATH / 'HKUST-1(Cu) CO2 303.0.xls',
    DATA_EXCEL_PATH / 'MCM-41 N2 77.0.xls'
]

DATA_JSON_STD = [
    DATA_JSON_PATH / 'HKUST-1(Cu) CO2 303.0.json',
    DATA_JSON_PATH / 'MCM-41 N2 77.0.json'
]

DATA_SPECIAL_PATH = DATA_PATH / 'special'

DATA_EXCEL_MIC = [
    DATA_SPECIAL_PATH / 'mic' / 'Sample_A.xls',
    DATA_SPECIAL_PATH / 'mic' / 'Sample_B.xls'
]

DATA_EXCEL_BEL = [
    DATA_SPECIAL_PATH / 'bel' / 'Sample_C.xls',
    DATA_SPECIAL_PATH / 'bel' / 'Sample_D.xls'
]

DATA_BEL = [DATA_SPECIAL_PATH / 'bel' / 'Sample_E.DAT']
