#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name='pygaps',
    version='1.3.0',
    license='MIT license',
    description='A framework for processing adsorption data for porous materials',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges',
                   re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    author='Paul Iacomi',
    author_email='iacomi.paul@gmail.com',
    url='https://github.com/pauliacomi/pygaps',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        # 'Programming Language :: Python :: Implementation :: CPython',
        # 'Programming Language :: Python :: Implementation :: PyPy3',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    keywords=[
        'adsorption', 'science', 'porous materials'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'numpy >= 1.13',
        'scipy >= 1.0.0',
        'pandas >= 0.21.1',
        'matplotlib >= 2.1',
        'xlrd >= 1.1',
        'xlwt >= 1.3',
        'coolprop >= 6.0',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coverage',
        'nose',
    ],
    extras_require={
        'reST': [
            'docutils>=0.11'
            'doc9',
            'pandoc',
            'restructuredtext-lint',
        ],
    },
)
