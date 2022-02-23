# -*- encoding: utf-8 -*-

import re
from pathlib import Path

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
    return re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', text)


setup(long_description=remove_badges(read('README.rst')))
