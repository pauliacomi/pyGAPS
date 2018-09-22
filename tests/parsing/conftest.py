import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'docs', 'examples', 'data', 'parsing')

DATA_EXCEL_PATH = os.path.join(DATA_PATH, 'excel')

DATA_EXCEL_STD = [os.path.join(DATA_EXCEL_PATH, 'HKUST-1(Cu) CO2 303.0.xls'),
                  os.path.join(DATA_EXCEL_PATH, 'MCM-41 N2 77.0.xls')]

DATA_EXCEL_MIC = [os.path.join(DATA_EXCEL_PATH, 'mic', 'Sample_A.xls'),
                  os.path.join(DATA_EXCEL_PATH, 'mic', 'Sample_B.xls')]

DATA_EXCEL_BEL = [os.path.join(DATA_EXCEL_PATH, 'bel', 'Sample_C.xls'),
                  os.path.join(DATA_EXCEL_PATH, 'bel', 'Sample_D.xls')]

DATA_BEL = [os.path.join(DATA_PATH, 'bel', 'Sample_C.DAT')]
