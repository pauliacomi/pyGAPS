from pathlib import Path

DATA_PATH = Path(
    __file__
).parent.parent.parent / 'docs' / 'examples' / 'data' / 'parsing'

XL_PATH = DATA_PATH / 'excel'
JSON_PATH = DATA_PATH / 'json'
AIF_PATH = DATA_PATH / 'aif'
SPECIAL_PATH = DATA_PATH / 'special'

DATA_XL = [
    XL_PATH / 'HKUST-1(Cu) CO2 303.0.xls',
    XL_PATH / 'MCM-41 N2 77.0.xls',
]

DATA_AIF = [
    AIF_PATH / 'dut-8_etoh_298k.aif',
    AIF_PATH / 'dmof_C2H6_298k.aif',
    AIF_PATH / 'ar_test_77k.aif',
]

DATA_JSON = [
    JSON_PATH / 'HKUST-1(Cu) CO2 303.0.json',
    JSON_PATH / 'MCM-41 N2 77.0.json',
]

DATA_JSON = [
    JSON_PATH / 'HKUST-1(Cu) CO2 303.0.json',
    JSON_PATH / 'MCM-41 N2 77.0.json',
]

DATA_MIC_XL = [
    SPECIAL_PATH / 'mic' / 'Sample_A.xls',
    SPECIAL_PATH / 'mic' / 'Sample_B.xls',
]

DATA_BEL_XL = [
    SPECIAL_PATH / 'bel' / 'Sample_C.xls',
    SPECIAL_PATH / 'bel' / 'Sample_D.xls',
]

DATA_BEL = [
    SPECIAL_PATH / 'bel' / 'Sample_E.DAT',
]
