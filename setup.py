import sys
from setuptools import setup

if sys.version_info[0] != 3:
    print("Requires Python 3.")
    sys.exit(1)

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='adsutils',
      version='0.1',
      description='Collection of utilities for adsorption',
      url='',
      download_url='',
      packages=['adsutils'],
      package_data={'adsutils.tests': ['data calorimetry/*.csv',
                                       'data isotherms/*.xlxs'],
                   },
      install_requires=[
          'numpy',
          'scipy',
          'pandas',
          'matplotlib',
          'pyiast',
          'coolprop',
          ],
      keywords='chemistry adsorption isotherm utilities',
      author='Paul A. Iacomi',
      author_email='iacomi.paul@gmail.com',
      license='MIT',
      zip_safe=False)
