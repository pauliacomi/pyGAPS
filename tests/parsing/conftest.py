import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'docs', 'examples', 'data', 'parsing')

DATA_EXCEL_PATH = os.path.join(DATA_PATH, 'excel')
DATA_EXCEL_MIC = [os.path.join(DATA_EXCEL_PATH, 'mic', 'Sample_A.xls'),
                  os.path.join(DATA_EXCEL_PATH, 'mic', 'Sample_B.xls')]

DATA_EXCEL_BEL = [os.path.join(DATA_EXCEL_PATH, 'bel', 'Sample_C.xls'),
                  os.path.join(DATA_EXCEL_PATH, 'bel', 'Sample_D.xls')]
