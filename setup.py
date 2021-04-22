# -*- encoding: utf-8 -*-

import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


def read(name, **kwargs):
    """Read and return file contents."""
    with open(
        Path(__file__).parent / name,
        encoding=kwargs.get('encoding', 'utf8'),
    ) as fh:
        return fh.read()


def remove_badges(text):
    """Remove badge text from the readme."""
    return re.compile('^.. start-badges.*^.. end-badges',
                      re.M | re.S).sub('', text)


setup(
    name='pygaps',
    use_scm_version={
        'local_scheme': 'dirty-tag',
        'write_to': 'src/pygaps/_version.py',
        'fallback_version': '3.1.0',
    },
    license='MIT license',
    description=  # noqa: E251
    """A framework for processing adsorption data for porous materials.""",
    long_description=remove_badges(read('README.rst')),
    long_description_content_type="text/x-rst",
    author='Paul Iacomi',
    author_email='mail@pauliacomi.com',
    url='https://github.com/pauliacomi/pygaps',
    project_urls={
        "Documentation": 'https://pygaps.readthedocs.io',
        "Source Code": 'https://github.com/pauliacomi/pygaps',
    },
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[path.name.suffix for path in Path('./src').glob('*.py')],
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'pygaps = pygaps.cli:main'
        ]
    },
    classifiers=[  # Classifier list at https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Chemistry',
    ],
    keywords=['adsorption', 'characterization', 'porous materials'],
    python_requires='>=3.6',
    setup_requires=[
        'setuptools_scm',
        'pytest-runner',
    ],
    install_requires=[
        'numpy',
        'scipy',
        'pandas',
        'matplotlib',
        'xlrd >= 1.1',
        'xlwt >= 1.3',
        'coolprop >= 6.0',
        'gemmi',
        'requests',
        'importlib_resources; python_version<"3.9"',  # TODO remove after 3.8 is unsupported
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coverage',
        'nose',
    ],
    extras_require={
        'dev': [
            'isort',
            'pylint',
            'flake8',
            'autopep8',
            'pydocstyle',
            'bump2version',
        ],
        'docs': [
            'docutils >= 0.11'
            'doc8',
            'pandoc',
            'restructuredtext-lint',
            'sphinx',
            'nbsphinx',
            'sphinx_rtd_theme',
        ],
    },
)
