#!/usr/bin/env python
import sys
from setuptools import setup

# Should match pyproject.toml
SETUP_REQUIRES = ['setuptools >= 42', 'versioningit']
# This enables setuptools to install wheel on-the-fly
SETUP_REQUIRES += ['wheel'] if 'bdist_wheel' in sys.argv else []

if __name__ == '__main__':
    setup(
        name='chiptools',
        setup_requires=SETUP_REQUIRES,
    )
