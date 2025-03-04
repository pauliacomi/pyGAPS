"""This module provides fixtures and paths for parsing tests."""

from ..conftest import DATA_PATH

PARSING_PATH = DATA_PATH / 'parsing'

DATA_XL = tuple((PARSING_PATH / 'excel').glob("*.xls"))
DATA_JSON = tuple((PARSING_PATH / 'json').glob("*.json"))
DATA_CSV = tuple((PARSING_PATH / 'csv').glob("*.csv"))
DATA_AIF = tuple((PARSING_PATH / 'aif').glob("*.aif"))
DATA_JSON_NIST = tuple((PARSING_PATH / 'nist').glob("*.json"))
