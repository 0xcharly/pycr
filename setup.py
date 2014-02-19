#! /usr/bin/env python

"""
Setup configuration file for Gerrit Code Review - Command Line Tools
"""

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
    packages=['libpycr', 'libpycr.commands', 'libpycr.utils'],
    requires=['requests', 'pygments'],
    scripts=[os.path.join('scripts', 'gerrit-cl')],
)
