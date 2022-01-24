from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / 'docs' / 'examples' / 'data' / 'parsing'

XL_PATH = DATA_PATH / 'excel'
JSON_PATH = DATA_PATH / 'json'
AIF_PATH = DATA_PATH / 'aif'

BEL_PATH = DATA_PATH / 'commercial' / 'bel'
MIC_PATH = DATA_PATH / 'commercial' / 'mic'
TP_PATH = DATA_PATH / 'commercial' / '3p'
QNT_PATH = DATA_PATH / 'commercial' / 'qnt'
NIST_PATH = DATA_PATH / 'nist'

DATA_XL = XL_PATH.glob("*.xls")
DATA_AIF = AIF_PATH.glob("*.aif")
DATA_JSON = JSON_PATH.glob("*.json")
DATA_JSON_NIST = NIST_PATH.glob("*.json")
DATA_MIC_XL = MIC_PATH.glob("*.xls")
DATA_BEL = BEL_PATH.glob("*.DAT")
DATA_BEL_XL = BEL_PATH.glob("*.xls")
DATA_BEL_CSV = BEL_PATH.glob("*.csv")
DATA_3P_XL = TP_PATH.glob("*.xlsx")
DATA_QNT = QNT_PATH.glob("*.txt")
