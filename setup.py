#! /usr/bin/env python

"""Gerrit Code Review - Command Line Tools"""

import os
from distutils.core import setup


# Ensure execution from the root directory
ROOT_DIR = os.path.dirname(__file__)

if ROOT_DIR != '':
    os.chdir(ROOT_DIR)

# Dynamically calculate the version based on libpycr.VERSION
VERSION = __import__('libpycr').get_version()

# Run the setup tools
setup(
    name='PyCR',
    version=VERSION,
    author='JC Delay',
    author_email='jcd.delay@gmail.com',
    license='Apache v2',
    description='A Command-line Interface to Gerrit Code Review v2.8',
    packages=['libpycr', 'libpycr.builtin', 'libpycr.gerrit',
              'libpycr.gerrit.api', 'libpycr.meta', 'libpycr.utils'],
    requires=['requests', 'pygments', 'prettytable'],
    scripts=[
        os.path.join('scripts', 'git-cl'),
        os.path.join('scripts', 'gerrit-accounts')
    ]
)
