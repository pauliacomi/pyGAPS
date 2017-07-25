import sys
from setuptools import setup

if sys.version_info[0] != 3:
    print("Requires Python 3.")
    sys.exit(1)

setup(name='adsutils',
      version='0.1',
      description='Collection of utilities for adsorption',
      url='',
      download_url='',
      install_requires=['numpy', 'scipy', 'pandas', 'matplotlib', 'pyiast'],
      keywords='chemistry adsorption isotherm utilities',
      author='Paul A. Iacomi',
      author_email='iacomi.paul@gmail.com',
      license='MIT',
      packages=['adsutils'],
      zip_safe=False)
