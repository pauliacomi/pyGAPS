import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'docs', 'examples', 'data', 'parsing')

DATA_EXCEL_PATH = os.path.join(DATA_PATH, 'excel')
DATA_EXCEL_MIC = ['mic/Sample_A.xls', 'mic/Sample_B.xls']
