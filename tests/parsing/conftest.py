from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / 'docs' / 'examples' / 'data' / 'parsing'

XL_PATH = DATA_PATH / 'excel'
JSON_PATH = DATA_PATH / 'json'
CSV_PATH = DATA_PATH / 'csv'
AIF_PATH = DATA_PATH / 'aif'
NIST_PATH = DATA_PATH / 'nist'

DATA_XL = tuple(XL_PATH.glob("*.xls"))
DATA_JSON = tuple(JSON_PATH.glob("*.json"))
DATA_CSV = tuple(CSV_PATH.glob("*.csv"))
DATA_AIF = tuple(AIF_PATH.glob("*.aif"))
DATA_JSON_NIST = tuple(NIST_PATH.glob("*.json"))
